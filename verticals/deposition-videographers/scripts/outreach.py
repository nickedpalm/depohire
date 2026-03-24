#!/usr/bin/env python3
"""
Provider outreach campaign for DepoHire.

Sends cold emails to unclaimed providers via Listmonk transactional API.
Each email includes a preview of their listing and a CTA to claim it.

Usage:
    # Preview mode (default) — prints emails without sending
    python3 scripts/outreach.py --preview

    # Preview a single provider
    python3 scripts/outreach.py --preview --slug acme-legal-video-nyc

    # Generate HTML preview file
    python3 scripts/outreach.py --preview --html > outreach-preview.html

    # DRY RUN — validates everything, doesn't send
    python3 scripts/outreach.py --dry-run

    # SEND to a single provider (for testing)
    python3 scripts/outreach.py --send --slug acme-legal-video-nyc

    # SEND to all providers (batch, with rate limiting)
    python3 scripts/outreach.py --send --batch --delay 2

    # SEND only to providers in a specific state
    python3 scripts/outreach.py --send --batch --state NY --delay 2

Environment:
    LISTMONK_URL       — Listmonk instance URL (default: https://mail.firestick.io)
    LISTMONK_USER      — Listmonk admin user (default: admin)
    LISTMONK_PASS      — Listmonk admin password
    SITE_DOMAIN        — Site domain (default: depohire.com)
"""

import argparse
import json
import glob
import os
import sys
import time
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from base64 import b64encode
from html import escape


SITE_DOMAIN = os.environ.get("SITE_DOMAIN", "depohire.com")
SITE_NAME = "DepoHire"
SITE_URL = f"https://{SITE_DOMAIN}"
FROM_EMAIL = f"{SITE_NAME} <contact@{SITE_DOMAIN}>"

LISTMONK_URL = os.environ.get("LISTMONK_URL", "https://mail.firestick.io")
LISTMONK_USER = os.environ.get("LISTMONK_USER", "admin")
LISTMONK_PASS = os.environ.get("LISTMONK_PASS", "")


def load_listings():
    """Load all listings from JSON files."""
    listings = []
    base = os.path.join(os.path.dirname(__file__), "..", "src", "data", "listings")
    for f in sorted(glob.glob(os.path.join(base, "*.json"))):
        with open(f) as fh:
            data = json.load(fh)
            listings.extend(data)
    return listings


def load_cities():
    """Load city data for display names."""
    path = os.path.join(os.path.dirname(__file__), "..", "src", "data", "cities.json")
    with open(path) as f:
        return {c["slug"]: c for c in json.load(f)}


def is_valid_email(email):
    """Filter out obvious fake/placeholder emails."""
    if not email or "@" not in email:
        return False
    fakes = {"user@domain.com", "info@example.com", "email@example.com", "test@test.com",
             "noemail@noemail.com", "no@email.com", "none@none.com"}
    return email.lower().strip() not in fakes


def render_email(listing, city_name):
    """Render the cold outreach email HTML."""
    name = escape(listing["name"])
    city = escape(city_name)
    state = escape(listing.get("state", ""))
    slug = listing["slug"]
    rating = listing.get("rating", 0)
    review_count = listing.get("review_count", 0)
    services = listing.get("services", [])
    certs = listing.get("certifications", [])

    stars_html = "".join(
        f'<span style="color:#fbbf24;font-size:18px">★</span>' if i < round(rating)
        else f'<span style="color:#d1d5db;font-size:18px">☆</span>'
        for i in range(5)
    )

    services_html = ""
    if services:
        tags = " ".join(
            f'<span style="display:inline-block;background:#f0f4ff;color:#1e40af;'
            f'padding:4px 10px;border-radius:6px;font-size:12px;margin:2px">{escape(s)}</span>'
            for s in services[:6]
        )
        services_html = f'<div style="margin-top:12px">{tags}</div>'

    certs_html = ""
    if certs:
        badges = " ".join(
            f'<span style="display:inline-block;background:#ecfdf5;color:#065f46;'
            f'padding:4px 10px;border-radius:6px;font-size:12px;margin:2px">✓ {escape(c)}</span>'
            for c in certs[:4]
        )
        certs_html = f'<div style="margin-top:8px">{badges}</div>'

    listing_url = f"{SITE_URL}/listing/{slug}/"
    claim_url = f"{SITE_URL}/provider/login?listing={slug}"
    provider_url = f"{listing_url}?src=provider"
    unsubscribe_url = f"{SITE_URL}/api/unsubscribe?email={listing['email']}"

    subject = f"Your business is listed on {SITE_NAME} — claim it free"

    html = f"""<!DOCTYPE html>
<html>
<body style="margin:0;padding:0;background:#f9fafb;font-family:system-ui,-apple-system,sans-serif">
<div style="max-width:560px;margin:40px auto;background:#fff;border-radius:12px;border:1px solid #e5e7eb;overflow:hidden">

  <!-- Header -->
  <div style="background:#1e3a5f;padding:24px 32px">
    <h1 style="color:#fff;font-size:20px;margin:0;font-weight:700">{SITE_NAME}</h1>
  </div>

  <div style="padding:32px">
    <!-- Greeting -->
    <p style="color:#1a1a1a;font-size:16px;line-height:1.6;margin:0 0 20px">
      Hi there,
    </p>
    <p style="color:#4b5563;font-size:15px;line-height:1.6;margin:0 0 20px">
      We've built <strong>{SITE_NAME}</strong> — a free directory that helps attorneys find
      deposition videographers. Your business already has a listing:
    </p>

    <!-- Listing Preview Card -->
    <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:12px;padding:20px;margin:0 0 24px">
      <div style="font-size:18px;font-weight:700;color:#1a1a1a;margin:0 0 4px">{name}</div>
      <div style="font-size:14px;color:#6b7280;margin:0 0 12px">{city}, {state}</div>

      {f'<div style="margin-bottom:8px">{stars_html} <span style="color:#6b7280;font-size:14px">({review_count} reviews)</span></div>' if rating else ''}
      {services_html}
      {certs_html}

      <div style="margin-top:16px">
        <a href="{provider_url}" style="color:#2563eb;font-size:14px;text-decoration:none;font-weight:500">
          View your listing →
        </a>
      </div>
    </div>

    <!-- Value Props -->
    <p style="color:#4b5563;font-size:15px;line-height:1.6;margin:0 0 16px">
      <strong>Claim your listing (free)</strong> and you can:
    </p>
    <table style="width:100%;margin:0 0 24px" cellpadding="0" cellspacing="0">
      <tr>
        <td style="padding:6px 12px 6px 0;vertical-align:top;color:#2563eb;font-size:16px">✓</td>
        <td style="padding:6px 0;color:#4b5563;font-size:14px;line-height:1.5">Edit your business description, services, and credentials</td>
      </tr>
      <tr>
        <td style="padding:6px 12px 6px 0;vertical-align:top;color:#2563eb;font-size:16px">✓</td>
        <td style="padding:6px 0;color:#4b5563;font-size:14px;line-height:1.5">Add photos and a demo reel to showcase your work</td>
      </tr>
      <tr>
        <td style="padding:6px 12px 6px 0;vertical-align:top;color:#2563eb;font-size:16px">✓</td>
        <td style="padding:6px 0;color:#4b5563;font-size:14px;line-height:1.5">Receive quote requests directly from attorneys in your area</td>
      </tr>
      <tr>
        <td style="padding:6px 12px 6px 0;vertical-align:top;color:#2563eb;font-size:16px">✓</td>
        <td style="padding:6px 0;color:#4b5563;font-size:14px;line-height:1.5">Get a "Verified" badge on your listing</td>
      </tr>
    </table>

    <!-- CTA Button -->
    <div style="text-align:center;margin:0 0 24px">
      <a href="{claim_url}"
         style="display:inline-block;background:#2563eb;color:#fff;padding:14px 32px;border-radius:8px;text-decoration:none;font-weight:600;font-size:15px">
        Claim Your Free Listing
      </a>
    </div>

    <p style="color:#9ca3af;font-size:13px;line-height:1.5;margin:0">
      It takes 30 seconds — just verify your email and you're in. No credit card required.
    </p>
  </div>

  <!-- Footer -->
  <div style="border-top:1px solid #f3f4f6;padding:20px 32px;background:#fafafa">
    <p style="color:#9ca3af;font-size:12px;margin:0;line-height:1.6">
      <a href="{listing_url}" style="color:#6b7280;text-decoration:none">View listing</a> ·
      <a href="{SITE_URL}/removal-request/?listing={slug}&name={name}" style="color:#6b7280;text-decoration:none">Request removal</a> ·
      <a href="{unsubscribe_url}" style="color:#6b7280;text-decoration:none">Unsubscribe</a>
    </p>
    <p style="color:#d1d5db;font-size:11px;margin:8px 0 0;line-height:1.5">
      {SITE_NAME} · PO Box 1547, Austin, TX 78767<br>
      You're receiving this because your business is listed on {SITE_DOMAIN}.
      <a href="{unsubscribe_url}" style="color:#d1d5db">Unsubscribe</a> at any time.
    </p>
  </div>
</div>
</body>
</html>"""

    return subject, html


def send_via_listmonk(to_email, subject, html_body):
    """Send a transactional email via Listmonk API."""
    if not LISTMONK_PASS:
        raise ValueError("LISTMONK_PASS not set")

    payload = json.dumps({
        "subscriber_email": to_email,
        "template_id": 3,
        "subject": subject,
        "body": html_body,
        "content_type": "html",
        "data": {},
        "messenger": "email",
        "from_email": FROM_EMAIL,
    }).encode()

    auth = b64encode(f"{LISTMONK_USER}:{LISTMONK_PASS}".encode()).decode()

    req = Request(
        f"{LISTMONK_URL}/api/tx",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Basic {auth}",
        },
        method="POST",
    )

    try:
        resp = urlopen(req, timeout=15)
        return resp.status == 200
    except HTTPError as e:
        print(f"  ERROR: Listmonk returned {e.code}: {e.read().decode()[:200]}", file=sys.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(description="DepoHire provider outreach")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--preview", action="store_true", help="Preview emails (no sending)")
    group.add_argument("--dry-run", action="store_true", help="Validate everything, don't send")
    group.add_argument("--send", action="store_true", help="Actually send emails")

    parser.add_argument("--slug", help="Target a single listing by slug")
    parser.add_argument("--state", help="Target a single state (e.g., NY)")
    parser.add_argument("--batch", action="store_true", help="Send to all eligible providers")
    parser.add_argument("--delay", type=float, default=2.0, help="Seconds between sends (default: 2)")
    parser.add_argument("--limit", type=int, default=0, help="Max emails to send (0=unlimited)")
    parser.add_argument("--html", action="store_true", help="Output HTML preview")

    args = parser.parse_args()

    listings = load_listings()
    cities = load_cities()

    # Filter to providers with valid emails
    eligible = [
        l for l in listings
        if is_valid_email(l.get("email"))
        and not l.get("claimed")
    ]

    if args.slug:
        eligible = [l for l in eligible if l["slug"] == args.slug]
        if not eligible:
            print(f"No eligible listing found for slug: {args.slug}", file=sys.stderr)
            sys.exit(1)

    if args.state:
        eligible = [l for l in eligible if l.get("state") == args.state]

    if args.limit:
        eligible = eligible[:args.limit]

    print(f"Eligible providers: {len(eligible)}")

    if args.preview:
        if args.html:
            # Output a single HTML file with all previews
            print("<html><body style='background:#f0f0f0;padding:20px'>")
            for l in eligible[:10]:  # Preview first 10
                city_info = cities.get(l.get("city", ""), {})
                city_name = city_info.get("city", l.get("city", ""))
                subject, html = render_email(l, city_name)
                print(f"<h3 style='font-family:sans-serif;margin:30px 0 10px'>To: {l['email']} — {subject}</h3>")
                print(html)
                print("<hr>")
            print("</body></html>")
        else:
            for l in eligible[:5]:
                city_info = cities.get(l.get("city", ""), {})
                city_name = city_info.get("city", l.get("city", ""))
                subject, _ = render_email(l, city_name)
                print(f"  {l['name']}")
                print(f"    Email: {l['email']}")
                print(f"    Subject: {subject}")
                print(f"    City: {city_name}, {l.get('state', '')}")
                print(f"    Listing: {SITE_URL}/listing/{l['slug']}/")
                print(f"    Claim: {SITE_URL}/provider/login?listing={l['slug']}")
                print()
            if len(eligible) > 5:
                print(f"  ... and {len(eligible) - 5} more")

    elif args.dry_run:
        errors = 0
        for l in eligible:
            city_info = cities.get(l.get("city", ""), {})
            city_name = city_info.get("city", l.get("city", ""))
            try:
                subject, html = render_email(l, city_name)
                assert len(subject) > 0, "Empty subject"
                assert len(html) > 500, "HTML too short"
                assert l["email"] in html or "unsubscribe" in html.lower(), "Missing unsubscribe"
            except Exception as e:
                print(f"  FAIL: {l['slug']} — {e}", file=sys.stderr)
                errors += 1

        print(f"Validated {len(eligible)} emails, {errors} errors")
        if errors:
            sys.exit(1)

    elif args.send:
        if not args.slug and not args.batch:
            print("ERROR: Use --slug for single send or --batch for all", file=sys.stderr)
            sys.exit(1)

        if not LISTMONK_PASS:
            print("ERROR: LISTMONK_PASS not set", file=sys.stderr)
            sys.exit(1)

        sent = 0
        failed = 0
        for i, l in enumerate(eligible):
            city_info = cities.get(l.get("city", ""), {})
            city_name = city_info.get("city", l.get("city", ""))
            subject, html = render_email(l, city_name)

            print(f"  [{i+1}/{len(eligible)}] Sending to {l['email']} ({l['name']})...", end=" ")
            ok = send_via_listmonk(l["email"], subject, html)
            if ok:
                print("OK")
                sent += 1
            else:
                print("FAILED")
                failed += 1

            if i < len(eligible) - 1:
                time.sleep(args.delay)

        print(f"\nDone: {sent} sent, {failed} failed")


if __name__ == "__main__":
    main()
