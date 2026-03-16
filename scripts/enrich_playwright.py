#!/usr/bin/env python3
"""
Re-scrape websites using Playwright (headless browser) to find emails
hidden behind JavaScript rendering that httpx missed.

Usage:
    python3 scripts/enrich_playwright.py --vertical deposition-videographers [--dry-run] [--limit N]

Requires: pip install playwright && playwright install chromium
"""

import argparse
import asyncio
import re
import sqlite3
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse

PROJECT_ROOT = Path(__file__).parent.parent

EMAIL_RE = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b')
PHONE_RE = re.compile(r'(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b')

JUNK_DOMAINS = {
    'example.com', 'example.org', 'sentry.io', 'wixpress.com', 'w3.org',
    'schema.org', 'googleapis.com', 'google.com', 'facebook.com',
    'twitter.com', 'instagram.com', 'linkedin.com', 'youtube.com',
    'cloudflare.com', 'wordpress.org', 'wordpress.com', 'gravatar.com',
    'wp.com', 'gstatic.com', 'googletagmanager.com',
}
JUNK_PREFIXES = {'noreply', 'no-reply', 'donotreply', 'mailer-daemon', 'postmaster'}

CONTACT_PATHS = [
    '/contact', '/contact-us', '/contact/', '/contact-us/',
    '/about', '/about-us', '/about/', '/about-us/',
]


def is_valid_email(email: str) -> bool:
    email = email.lower().strip()
    domain = email.split('@')[-1]
    local = email.split('@')[0]
    if domain in JUNK_DOMAINS:
        return False
    if local in JUNK_PREFIXES:
        return False
    if len(email) > 80:
        return False
    if email.endswith(('.png', '.jpg', '.gif', '.svg', '.css', '.js', '.webp')):
        return False
    return True


async def scrape_page(page, url: str, timeout: int = 15000) -> dict:
    """Scrape a single page for contact info using Playwright."""
    info = {"emails": set(), "phones": set(), "contact_form_url": None}
    try:
        resp = await page.goto(url, wait_until="domcontentloaded", timeout=timeout)
        if not resp or resp.status != 200:
            return info
        # Wait for JS to render
        await page.wait_for_timeout(2000)

        # Get full rendered HTML
        html = await page.content()
        text = await page.evaluate("() => document.body?.innerText || ''")

        # Emails from mailto links
        mailto_emails = await page.evaluate("""
            () => Array.from(document.querySelectorAll('a[href^="mailto:"]'))
                .map(a => a.href.replace('mailto:', '').split('?')[0].trim())
        """)
        for email in mailto_emails:
            if is_valid_email(email):
                info["emails"].add(email.lower())

        # Emails from page text
        for match in EMAIL_RE.findall(text):
            if is_valid_email(match):
                info["emails"].add(match.lower())

        # Also check HTML source (sometimes emails are in data attributes, etc.)
        for match in EMAIL_RE.findall(html):
            if is_valid_email(match):
                info["emails"].add(match.lower())

        # Phones from tel links
        tel_phones = await page.evaluate("""
            () => Array.from(document.querySelectorAll('a[href^="tel:"]'))
                .map(a => a.href.replace('tel:', '').trim())
        """)
        for phone in tel_phones:
            if len(re.sub(r'\\D', '', phone)) >= 10:
                info["phones"].add(phone)

        # Check for contact form
        has_form = await page.evaluate("""
            () => {
                const forms = document.querySelectorAll('form');
                for (const form of forms) {
                    const inputs = form.querySelectorAll('input');
                    for (const input of inputs) {
                        if (input.type === 'email' ||
                            (input.name && input.name.toLowerCase().includes('email'))) {
                            return true;
                        }
                    }
                }
                return false;
            }
        """)
        if has_form:
            info["contact_form_url"] = url

        # Find contact page links
        if not info["emails"]:
            contact_links = await page.evaluate("""
                () => Array.from(document.querySelectorAll('a'))
                    .filter(a => {
                        const href = (a.href || '').toLowerCase();
                        const text = (a.innerText || '').toLowerCase().trim();
                        return href.includes('/contact') || href.includes('/get-a-quote') ||
                               text === 'contact' || text === 'contact us';
                    })
                    .map(a => a.href)
                    .slice(0, 2)
            """)
            if contact_links:
                info["contact_form_url"] = info["contact_form_url"] or contact_links[0]

    except Exception:
        pass

    return info


async def scrape_listing(page, website: str) -> dict:
    """Scrape a listing's website and contact pages."""
    combined = {"emails": set(), "phones": set(), "contact_form_url": None}

    # Main page
    info = await scrape_page(page, website)
    combined["emails"].update(info["emails"])
    combined["phones"].update(info["phones"])
    combined["contact_form_url"] = info["contact_form_url"]

    # Try contact pages if no email found
    if not combined["emails"]:
        parsed = urlparse(website)
        base = f"{parsed.scheme}://{parsed.netloc}"
        for path in CONTACT_PATHS[:4]:
            contact_url = base + path
            info = await scrape_page(page, contact_url, timeout=10000)
            combined["emails"].update(info["emails"])
            combined["phones"].update(info["phones"])
            if not combined["contact_form_url"]:
                combined["contact_form_url"] = info["contact_form_url"]
            if combined["emails"]:
                break

    return combined


async def run(args):
    from playwright.async_api import async_playwright

    db_path = PROJECT_ROOT / "verticals" / args.vertical / "pipeline.db"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")

    rows = conn.execute("""
        SELECT id, name, city, state, website, email, phone
        FROM raw_listings
        WHERE (email IS NULL OR email = '')
        AND website IS NOT NULL AND website != ''
        ORDER BY city, name
    """).fetchall()

    print(f"Listings missing email with website: {len(rows)}")

    if args.dry_run:
        print("\nDry run — no scraping.")
        conn.close()
        return

    if args.limit:
        rows = rows[:args.limit]
        print(f"Limited to {args.limit}")

    stats = {"email": 0, "phone": 0, "form": 0, "errors": 0}

    print(f"\nScraping {len(rows)} websites with Playwright...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 720},
        )
        page = await context.new_page()

        for i, row in enumerate(rows):
            if (i + 1) % 25 == 0 or (i + 1) == len(rows):
                print(f"  Progress: {i + 1}/{len(rows)} (emails: +{stats['email']}, forms: +{stats['form']})")

            try:
                info = await scrape_listing(page, row["website"])
            except Exception as e:
                stats["errors"] += 1
                continue

            updates = []
            params = []

            if info["emails"]:
                emails = sorted(info["emails"])
                preferred = next(
                    (e for e in emails if e.startswith(('info@', 'contact@', 'office@'))),
                    emails[0]
                )
                updates.append("email = ?")
                params.append(preferred)
                updates.append("contact_method = 'email'")
                stats["email"] += 1

            if not row["phone"] and info["phones"]:
                updates.append("phone = ?")
                params.append(list(info["phones"])[0])
                stats["phone"] += 1

            if info["contact_form_url"]:
                updates.append("contact_form_url = ?")
                params.append(info["contact_form_url"])
                stats["form"] += 1

            if updates:
                params.append(row["id"])
                conn.execute(
                    f"UPDATE raw_listings SET {', '.join(updates)} WHERE id = ?",
                    params,
                )

            if (i + 1) % 50 == 0:
                conn.commit()

        await browser.close()

    conn.commit()
    conn.close()

    print(f"\nDone!")
    print(f"  Emails found: {stats['email']}")
    print(f"  Phones added: {stats['phone']}")
    print(f"  Contact forms: {stats['form']}")
    print(f"  Errors: {stats['errors']}")
    print(f"\nRun: python3 scripts/export.py --vertical {args.vertical}")


def main():
    parser = argparse.ArgumentParser(description="Scrape websites with Playwright for contact info")
    parser.add_argument("--vertical", required=True, help="Vertical slug")
    parser.add_argument("--dry-run", action="store_true", help="Show stats only")
    parser.add_argument("--limit", type=int, default=0, help="Limit listings")
    args = parser.parse_args()
    asyncio.run(run(args))


if __name__ == "__main__":
    main()
