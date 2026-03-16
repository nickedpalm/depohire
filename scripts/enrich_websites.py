#!/usr/bin/env python3
"""
Scrape listing websites for email addresses, contact form URLs,
social media links, and additional phone numbers.

Usage:
    python3 scripts/enrich_websites.py --vertical deposition-videographers [--dry-run] [--limit N]

No API keys needed. Just httpx + BeautifulSoup.
"""

import argparse
import json
import re
import sqlite3
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse

import httpx

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("Install BeautifulSoup: pip install beautifulsoup4")
    raise SystemExit(1)

PROJECT_ROOT = Path(__file__).parent.parent

# Patterns
EMAIL_RE = re.compile(
    r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b'
)
PHONE_RE = re.compile(
    r'(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'
)
# Pages likely to have contact info
CONTACT_PATHS = [
    '/contact', '/contact-us', '/contact/', '/contact-us/',
    '/about', '/about-us', '/about/', '/about-us/',
    '/get-a-quote', '/request-quote', '/get-quote',
    '/reach-us', '/connect',
]
# Junk emails to skip
JUNK_EMAILS = {
    'example.com', 'example.org', 'yoursite.com', 'yourdomain.com',
    'sentry.io', 'wixpress.com', 'w3.org', 'schema.org',
    'googleapis.com', 'google.com', 'facebook.com', 'twitter.com',
    'instagram.com', 'linkedin.com', 'youtube.com',
    'cloudflare.com', 'wordpress.org', 'wordpress.com',
    'gravatar.com', 'wp.com',
}
JUNK_PREFIXES = {'noreply', 'no-reply', 'donotreply', 'mailer-daemon', 'postmaster'}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; DepoHire/1.0; directory research)",
    "Accept": "text/html,application/xhtml+xml",
}


def is_valid_email(email: str) -> bool:
    """Filter out junk/system emails."""
    email = email.lower().strip()
    domain = email.split('@')[-1]
    local = email.split('@')[0]
    if domain in JUNK_EMAILS:
        return False
    if local in JUNK_PREFIXES:
        return False
    if len(email) > 80:
        return False
    # Skip image file extensions mistakenly captured
    if email.endswith(('.png', '.jpg', '.gif', '.svg', '.css', '.js')):
        return False
    return True


def extract_contact_info(html: str, base_url: str) -> dict:
    """Extract emails, phones, contact form URLs, and social links from HTML."""
    soup = BeautifulSoup(html, 'html.parser')
    text = soup.get_text(separator=' ')

    info = {
        "emails": set(),
        "phones": set(),
        "contact_form_url": None,
        "linkedin": None,
        "facebook": None,
    }

    # Find emails in mailto: links (highest confidence)
    for a in soup.find_all('a', href=True):
        href = a['href']
        if href.startswith('mailto:'):
            email = href.replace('mailto:', '').split('?')[0].strip()
            if is_valid_email(email):
                info["emails"].add(email)

    # Find emails in page text
    for match in EMAIL_RE.findall(text):
        if is_valid_email(match):
            info["emails"].add(match.lower())

    # Find phones in tel: links
    for a in soup.find_all('a', href=True):
        href = a['href']
        if href.startswith('tel:'):
            phone = href.replace('tel:', '').strip()
            if len(re.sub(r'\D', '', phone)) >= 10:
                info["phones"].add(phone)

    # Find contact form URLs
    for form in soup.find_all('form'):
        action = form.get('action', '')
        # Forms with email-related fields suggest a contact form
        inputs = form.find_all('input')
        has_email_field = any(
            i.get('type') == 'email' or i.get('name', '').lower() in ('email', 'e-mail')
            for i in inputs
        )
        if has_email_field and not info["contact_form_url"]:
            info["contact_form_url"] = base_url

    # Find social links
    for a in soup.find_all('a', href=True):
        href = a['href'].lower()
        if 'linkedin.com/company/' in href or 'linkedin.com/in/' in href:
            info["linkedin"] = a['href']
        elif 'facebook.com/' in href and '/sharer' not in href and 'facebook.com/tr' not in href:
            info["facebook"] = a['href']

    # Look for links to contact pages
    for a in soup.find_all('a', href=True):
        href = a['href'].lower()
        text_content = (a.get_text() or '').lower().strip()
        if any(p in href for p in ['/contact', '/get-a-quote', '/request-quote', '/reach-us']):
            if not info["contact_form_url"]:
                info["contact_form_url"] = urljoin(base_url, a['href'])
        elif text_content in ('contact', 'contact us', 'get a quote', 'request quote', 'reach us'):
            if not info["contact_form_url"]:
                info["contact_form_url"] = urljoin(base_url, a['href'])

    return info


def scrape_url(url: str, client: httpx.Client) -> str | None:
    """Fetch a URL and return HTML content."""
    try:
        resp = client.get(url, follow_redirects=True, timeout=15)
        if resp.status_code == 200 and 'text/html' in resp.headers.get('content-type', ''):
            return resp.text
    except Exception:
        pass
    return None


def scrape_listing(website: str, client: httpx.Client) -> dict:
    """Scrape a listing's website and contact pages for contact info."""
    combined = {
        "emails": set(),
        "phones": set(),
        "contact_form_url": None,
        "linkedin": None,
        "facebook": None,
    }

    # Scrape main page
    html = scrape_url(website, client)
    if html:
        info = extract_contact_info(html, website)
        combined["emails"].update(info["emails"])
        combined["phones"].update(info["phones"])
        combined["contact_form_url"] = info["contact_form_url"]
        combined["linkedin"] = info["linkedin"]
        combined["facebook"] = info["facebook"]

    # Try contact pages if we don't have an email yet
    if not combined["emails"]:
        parsed = urlparse(website)
        base = f"{parsed.scheme}://{parsed.netloc}"
        for path in CONTACT_PATHS[:4]:  # Try first 4 contact paths
            contact_url = base + path
            html = scrape_url(contact_url, client)
            if html:
                info = extract_contact_info(html, contact_url)
                combined["emails"].update(info["emails"])
                combined["phones"].update(info["phones"])
                if not combined["contact_form_url"]:
                    combined["contact_form_url"] = info["contact_form_url"]
                if not combined["linkedin"]:
                    combined["linkedin"] = info["linkedin"]
                if not combined["facebook"]:
                    combined["facebook"] = info["facebook"]
                if combined["emails"]:
                    break  # Got an email, stop trying
            time.sleep(0.5)

    return combined


def main():
    parser = argparse.ArgumentParser(description="Scrape websites for contact info")
    parser.add_argument("--vertical", required=True, help="Vertical slug")
    parser.add_argument("--dry-run", action="store_true", help="Show stats only")
    parser.add_argument("--limit", type=int, default=0, help="Limit listings to scrape")
    args = parser.parse_args()

    db_path = PROJECT_ROOT / "verticals" / args.vertical / "pipeline.db"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")

    # Get listings with websites that don't have emails yet
    rows = conn.execute("""
        SELECT id, name, city, website, phone, email
        FROM raw_listings
        WHERE website IS NOT NULL AND website != ''
        ORDER BY city, name
    """).fetchall()

    print(f"Listings with websites: {len(rows)}")
    already_has_email = sum(1 for r in rows if r["email"])
    print(f"  Already have email: {already_has_email}")
    print(f"  To scrape: {len(rows) - already_has_email}")

    if args.dry_run:
        print("\nDry run — no scraping.")
        conn.close()
        return

    to_scrape = [r for r in rows if not r["email"]]
    if args.limit:
        to_scrape = to_scrape[:args.limit]
        print(f"\nLimited to {args.limit}")

    stats = {"email": 0, "phone": 0, "form": 0, "linkedin": 0, "facebook": 0, "errors": 0}

    print(f"\nScraping {len(to_scrape)} websites...")
    client = httpx.Client(headers=HEADERS, follow_redirects=True)

    for i, row in enumerate(to_scrape):
        if (i + 1) % 25 == 0 or (i + 1) == len(to_scrape):
            print(f"  Progress: {i + 1}/{len(to_scrape)} (emails: +{stats['email']}, forms: +{stats['form']}, linkedin: +{stats['linkedin']})")

        try:
            info = scrape_listing(row["website"], client)
        except Exception as e:
            stats["errors"] += 1
            continue

        updates = []
        params = []

        # Best email (prefer info@, contact@, then first found)
        if info["emails"]:
            emails = sorted(info["emails"])
            preferred = next(
                (e for e in emails if e.startswith(('info@', 'contact@', 'office@'))),
                emails[0]
            )
            updates.append("email = ?")
            params.append(preferred)
            stats["email"] += 1

        # Add phone if listing doesn't have one
        if not row["phone"] and info["phones"]:
            updates.append("phone = ?")
            params.append(list(info["phones"])[0])
            stats["phone"] += 1

        if info["contact_form_url"]:
            updates.append("contact_form_url = ?")
            params.append(info["contact_form_url"])
            stats["form"] += 1

        if info["linkedin"]:
            updates.append("linkedin = ?")
            params.append(info["linkedin"])
            stats["linkedin"] += 1

        if info["facebook"]:
            updates.append("facebook = ?")
            params.append(info["facebook"])
            stats["facebook"] += 1

        if updates:
            # Determine best contact method
            if info["emails"]:
                method = "email"
            elif row["phone"] or info["phones"]:
                method = "phone"
            elif info["contact_form_url"]:
                method = "form"
            else:
                method = "website_only"
            updates.append("contact_method = ?")
            params.append(method)

            params.append(row["id"])
            conn.execute(f"UPDATE raw_listings SET {', '.join(updates)} WHERE id = ?", params)

        # Commit every 50
        if (i + 1) % 50 == 0:
            conn.commit()

        # Polite rate limiting
        time.sleep(1)

    client.close()
    conn.commit()

    # Set contact_method for listings we didn't scrape (already had data or no website)
    conn.execute("""
        UPDATE raw_listings SET contact_method = 'email'
        WHERE email IS NOT NULL AND email != '' AND contact_method IS NULL
    """)
    conn.execute("""
        UPDATE raw_listings SET contact_method = 'phone'
        WHERE (email IS NULL OR email = '') AND phone IS NOT NULL AND phone != '' AND contact_method IS NULL
    """)
    conn.execute("""
        UPDATE raw_listings SET contact_method = 'website_only'
        WHERE (email IS NULL OR email = '') AND (phone IS NULL OR phone = '')
        AND website IS NOT NULL AND website != '' AND contact_method IS NULL
    """)
    conn.execute("""
        UPDATE raw_listings SET contact_method = 'none'
        WHERE contact_method IS NULL
    """)
    conn.commit()
    conn.close()

    print(f"\nDone!")
    print(f"  Emails found: {stats['email']}")
    print(f"  Phones added: {stats['phone']}")
    print(f"  Contact forms found: {stats['form']}")
    print(f"  LinkedIn profiles: {stats['linkedin']}")
    print(f"  Facebook pages: {stats['facebook']}")
    print(f"  Errors: {stats['errors']}")
    print(f"\nRun: python3 scripts/export.py --vertical {args.vertical}")


if __name__ == "__main__":
    main()
