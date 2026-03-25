#!/usr/bin/env python3
"""
Outreach form submission script for directory factory.

Automates submitting contact forms for providers who have a contact_form_url
but no email address, sending them a listing claim notification.

Usage:
    python3 scripts/outreach_forms.py --vertical deposition-videographers [--dry-run] [--limit N]
"""

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from glob import glob
from pathlib import Path

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

FACTORY_ROOT = Path(__file__).resolve().parent.parent

SENDER_NAME = "Nick Palmer, DepoHire"
SENDER_EMAIL = "contact@depohire.com"
SENDER_PHONE = ""

MESSAGE_TEMPLATE = (
    "Hi, your business is listed on DepoHire.com — the #1 directory for "
    "deposition videographers. Attorneys in {city} are actively searching "
    "for providers like you.\n\n"
    "Claim your free listing: https://depohire.com/listing/{slug}/\n\n"
    "Questions? Reply to this message or email contact@depohire.com"
)

# Field-matching keywords (lowered)
NAME_KEYWORDS = ["name", "your name", "full name", "first name", "your-name", "full-name"]
EMAIL_KEYWORDS = ["email", "e-mail", "your email", "email-address", "your-email"]
PHONE_KEYWORDS = ["phone", "tel", "telephone", "mobile", "your-phone"]
MESSAGE_KEYWORDS = ["message", "comment", "inquiry", "details", "question", "comments",
                    "your-message", "how can we help", "description", "body", "note"]
COMPANY_KEYWORDS = ["company", "business", "organization", "firm"]
SUBJECT_KEYWORDS = ["subject", "topic", "reason", "regarding"]

# Captcha markers
CAPTCHA_SELECTORS = [
    "iframe[src*='recaptcha']",
    "iframe[src*='google.com/recaptcha']",
    ".g-recaptcha",
    "#g-recaptcha",
    "iframe[src*='challenges.cloudflare.com']",
    ".cf-turnstile",
    "[data-sitekey]",
    "iframe[src*='hcaptcha.com']",
    ".h-captcha",
]

SUBMIT_SELECTORS = [
    "button[type='submit']",
    "input[type='submit']",
    "button:has-text('Submit')",
    "button:has-text('Send')",
    "button:has-text('Contact')",
    "button:has-text('Get in Touch')",
    "button:has-text('Send Message')",
    "input[value='Submit' i]",
    "input[value='Send' i]",
    "input[value='Send Message' i]",
]

PAGE_TIMEOUT = 15_000  # ms
DELAY_BETWEEN = 3  # seconds


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_providers(vertical: str) -> list[dict]:
    """Load all listing JSON files for the given vertical."""
    listings_dir = FACTORY_ROOT / "verticals" / vertical / "src" / "data" / "listings"
    providers = []
    for fp in sorted(listings_dir.glob("*.json")):
        with open(fp) as f:
            data = json.load(f)
            if isinstance(data, list):
                providers.extend(data)
            else:
                providers.append(data)
    return providers


def filter_form_targets(providers: list[dict]) -> list[dict]:
    """Keep only providers with a contact_form_url and no email."""
    targets = []
    for p in providers:
        url = (p.get("contact_form_url") or "").strip()
        email = (p.get("email") or "").strip()
        if url and not email:
            targets.append(p)
    return targets


def _text_matches(text: str, keywords: list[str]) -> bool:
    """Check if any keyword appears in the text (case-insensitive)."""
    text = text.lower()
    return any(kw in text for kw in keywords)


def _field_signature(el_handle, page) -> str:
    """Build a searchable string from an element's name/id/placeholder/label/aria-label."""
    parts = []
    for attr in ("name", "id", "placeholder", "aria-label", "aria-labelledby"):
        val = el_handle.get_attribute(attr)
        if val:
            parts.append(val)
    # Also check associated <label>
    el_id = el_handle.get_attribute("id")
    if el_id:
        label = page.query_selector(f"label[for='{el_id}']")
        if label:
            parts.append(label.inner_text())
    return " ".join(parts).lower()


def detect_captcha(page) -> bool:
    """Return True if the page contains a known captcha widget."""
    for sel in CAPTCHA_SELECTORS:
        try:
            if page.query_selector(sel):
                return True
        except Exception:
            pass
    return False


def find_submit_button(form, page):
    """Find a submit button inside the form, or fall back to page-wide search."""
    for sel in SUBMIT_SELECTORS:
        try:
            btn = form.query_selector(sel)
            if btn and btn.is_visible():
                return btn
        except Exception:
            pass
    # Fallback: any visible button/input inside the form
    for tag in ["button", "input[type='submit']", "input[type='button']"]:
        try:
            btn = form.query_selector(tag)
            if btn and btn.is_visible():
                return btn
        except Exception:
            pass
    return None


# ---------------------------------------------------------------------------
# Core form handler
# ---------------------------------------------------------------------------

def process_provider(page, provider: dict, dry_run: bool) -> dict:
    """Navigate to the provider's contact form and attempt submission."""
    slug = provider["slug"]
    name = provider["name"]
    city = provider.get("city", "your area")
    url = provider["contact_form_url"]

    result = {
        "slug": slug,
        "name": name,
        "city": city,
        "contact_form_url": url,
        "status": "error",
        "error": None,
        "fields_found": [],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    # Navigate
    try:
        page.goto(url, timeout=PAGE_TIMEOUT, wait_until="domcontentloaded")
        page.wait_for_timeout(2000)  # let JS render
    except PlaywrightTimeout:
        result["error"] = "page load timeout"
        return result
    except Exception as e:
        result["error"] = f"navigation error: {str(e)[:200]}"
        return result

    # Check for captcha
    if detect_captcha(page):
        result["status"] = "skipped_captcha"
        result["error"] = "captcha detected on page"
        return result

    # Find forms
    forms = page.query_selector_all("form")
    if not forms:
        result["status"] = "skipped_no_form"
        result["error"] = "no <form> element found"
        return result

    # Score each form by how many contact-ish fields it has
    best_form = None
    best_score = -1
    for form in forms:
        score = 0
        inputs = form.query_selector_all("input, textarea, select")
        for inp in inputs:
            sig = _field_signature(inp, page)
            if _text_matches(sig, NAME_KEYWORDS):
                score += 1
            if _text_matches(sig, EMAIL_KEYWORDS):
                score += 1
            if _text_matches(sig, MESSAGE_KEYWORDS):
                score += 1
        textareas = form.query_selector_all("textarea")
        if textareas:
            score += 1
        if score > best_score:
            best_score = score
            best_form = form

    if best_score == 0:
        result["status"] = "skipped_no_form"
        result["error"] = "no recognizable contact fields in any form"
        return result

    form = best_form

    # Check for captcha specifically inside the chosen form
    for sel in CAPTCHA_SELECTORS:
        try:
            if form.query_selector(sel):
                result["status"] = "skipped_captcha"
                result["error"] = "captcha detected in contact form"
                return result
        except Exception:
            pass

    # Build the outreach message
    message = MESSAGE_TEMPLATE.format(city=city, slug=slug)

    # Map fields
    fields_filled = []
    inputs = form.query_selector_all("input, textarea, select")

    for inp in inputs:
        tag = inp.evaluate("el => el.tagName.toLowerCase()")
        input_type = (inp.get_attribute("type") or "text").lower()

        # Skip hidden, submit, checkbox, radio, file fields
        if input_type in ("hidden", "submit", "button", "checkbox", "radio", "file", "image"):
            continue

        sig = _field_signature(inp, page)

        if _text_matches(sig, NAME_KEYWORDS):
            inp.fill(SENDER_NAME)
            fields_filled.append("name")
        elif _text_matches(sig, EMAIL_KEYWORDS) or input_type == "email":
            inp.fill(SENDER_EMAIL)
            fields_filled.append("email")
        elif _text_matches(sig, PHONE_KEYWORDS) or input_type == "tel":
            if SENDER_PHONE:
                inp.fill(SENDER_PHONE)
                fields_filled.append("phone")
            else:
                # Leave phone empty if optional; try to check if required
                required = inp.get_attribute("required") is not None
                aria_required = inp.get_attribute("aria-required") == "true"
                if required or aria_required:
                    inp.fill("N/A")
                    fields_filled.append("phone")
        elif tag == "textarea" or _text_matches(sig, MESSAGE_KEYWORDS):
            inp.fill(message)
            fields_filled.append("message")
        elif _text_matches(sig, COMPANY_KEYWORDS):
            inp.fill("DepoHire")
            fields_filled.append("company")
        elif _text_matches(sig, SUBJECT_KEYWORDS):
            inp.fill("Your DepoHire Listing")
            fields_filled.append("subject")
        else:
            # Unknown required field — fill with a safe default
            required = inp.get_attribute("required") is not None
            aria_required = inp.get_attribute("aria-required") == "true"
            if required or aria_required:
                if input_type == "email":
                    inp.fill(SENDER_EMAIL)
                elif input_type in ("number", "tel"):
                    inp.fill("0")
                elif tag == "select":
                    # Pick first non-empty option
                    options = inp.query_selector_all("option")
                    for opt in options[1:]:  # skip placeholder
                        val = opt.get_attribute("value")
                        if val:
                            inp.select_option(value=val)
                            break
                else:
                    inp.fill("N/A")
                fields_filled.append(f"other:{inp.get_attribute('name') or 'unknown'}")

    result["fields_found"] = list(set(fields_filled))

    if "message" not in fields_filled and "email" not in fields_filled:
        result["status"] = "skipped_no_form"
        result["error"] = "could not fill message or email field"
        return result

    if dry_run:
        result["status"] = "dry_run"
        result["error"] = None
        return result

    # Submit
    submit_btn = find_submit_button(form, page)
    if not submit_btn:
        result["status"] = "error"
        result["error"] = "no submit button found"
        return result

    try:
        submit_btn.click()
        page.wait_for_timeout(3000)  # wait for form submission to process
        result["status"] = "submitted"
        result["error"] = None
    except Exception as e:
        result["error"] = f"submit error: {str(e)[:200]}"

    return result


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Outreach form submission for directory providers")
    parser.add_argument("--vertical", required=True, help="Vertical slug (e.g. deposition-videographers)")
    parser.add_argument("--dry-run", action="store_true", help="Navigate and detect fields but don't submit")
    parser.add_argument("--limit", type=int, default=0, help="Only process first N providers")
    args = parser.parse_args()

    # Load and filter
    providers = load_providers(args.vertical)
    targets = filter_form_targets(providers)
    print(f"Loaded {len(providers)} providers, {len(targets)} have contact_form_url and no email")

    if args.limit > 0:
        targets = targets[:args.limit]
        print(f"Limited to {len(targets)} providers")

    if not targets:
        print("No providers to process.")
        sys.exit(0)

    log_path = FACTORY_ROOT / "verticals" / args.vertical / "outreach-log.json"

    # Load existing log if present
    existing_log = []
    if log_path.exists():
        with open(log_path) as f:
            existing_log = json.load(f)
    already_done = {e["slug"] for e in existing_log if e.get("status") in ("submitted",)}

    results = list(existing_log)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 800},
        )
        page = context.new_page()

        for i, provider in enumerate(targets):
            slug = provider["slug"]

            if slug in already_done:
                print(f"[{i+1}/{len(targets)}] SKIP (already submitted): {provider['name']}")
                continue

            print(f"[{i+1}/{len(targets)}] Processing: {provider['name']} — {provider['contact_form_url']}")

            try:
                result = process_provider(page, provider, dry_run=args.dry_run)
            except Exception as e:
                result = {
                    "slug": slug,
                    "name": provider["name"],
                    "city": provider.get("city", ""),
                    "contact_form_url": provider["contact_form_url"],
                    "status": "error",
                    "error": f"unexpected: {str(e)[:200]}",
                    "fields_found": [],
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }

            status_display = result["status"]
            if result["error"]:
                status_display += f" ({result['error'][:60]})"
            print(f"  → {status_display}  fields={result['fields_found']}")

            results.append(result)

            # Write log incrementally
            with open(log_path, "w") as f:
                json.dump(results, f, indent=2)

            if i < len(targets) - 1:
                time.sleep(DELAY_BETWEEN)

        browser.close()

    # Summary
    statuses = {}
    for r in results:
        s = r["status"]
        statuses[s] = statuses.get(s, 0) + 1
    print(f"\nDone. Log written to {log_path}")
    print(f"Summary: {json.dumps(statuses)}")


if __name__ == "__main__":
    main()
