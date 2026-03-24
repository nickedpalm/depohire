#!/usr/bin/env python3
"""
Follow-up email templates for the provider drip sequence.

Templates:
  1. followup-unclaimed  — 5 days after cold email, still unclaimed
  2. followup-incomplete — 3 days after claim, profile < 60% complete
  3. followup-upgrade    — 14 days after claim, nudge to Sponsored

These are meant to be triggered by a cron job that checks D1 state.
For now, this file generates the HTML templates for preview/testing.

Usage:
    python3 scripts/outreach_followup.py --template followup-unclaimed --slug acme-video
    python3 scripts/outreach_followup.py --template followup-incomplete --slug acme-video
    python3 scripts/outreach_followup.py --template followup-upgrade --slug acme-video
    python3 scripts/outreach_followup.py --all-templates --html > drip-preview.html
"""

import argparse
import json
import glob
import os
import sys
from html import escape


SITE_DOMAIN = os.environ.get("SITE_DOMAIN", "depohire.com")
SITE_NAME = "DepoHire"
SITE_URL = f"https://{SITE_DOMAIN}"


def load_listings():
    base = os.path.join(os.path.dirname(__file__), "..", "src", "data", "listings")
    listings = {}
    for f in sorted(glob.glob(os.path.join(base, "*.json"))):
        for l in json.load(open(f)):
            listings[l["slug"]] = l
    return listings


def load_cities():
    path = os.path.join(os.path.dirname(__file__), "..", "src", "data", "cities.json")
    return {c["slug"]: c for c in json.load(open(path))}


def header_html():
    return f"""<div style="background:#1e3a5f;padding:24px 32px">
    <h1 style="color:#fff;font-size:20px;margin:0;font-weight:700">{SITE_NAME}</h1>
  </div>"""


def footer_html(email, slug, name):
    unsub = f"{SITE_URL}/api/unsubscribe?email={email}"
    return f"""<div style="border-top:1px solid #f3f4f6;padding:20px 32px;background:#fafafa">
    <p style="color:#9ca3af;font-size:12px;margin:0;line-height:1.6">
      <a href="{SITE_URL}/listing/{slug}/" style="color:#6b7280;text-decoration:none">View listing</a> ·
      <a href="{SITE_URL}/removal-request/?listing={slug}&name={escape(name)}" style="color:#6b7280;text-decoration:none">Request removal</a> ·
      <a href="{unsub}" style="color:#6b7280;text-decoration:none">Unsubscribe</a>
    </p>
    <p style="color:#d1d5db;font-size:11px;margin:8px 0 0;line-height:1.5">
      {SITE_NAME} · PO Box 1547, Austin, TX 78767<br>
      <a href="{unsub}" style="color:#d1d5db">Unsubscribe</a> at any time.
    </p>
  </div>"""


def wrap_email(inner, email, slug, name):
    return f"""<!DOCTYPE html>
<html>
<body style="margin:0;padding:0;background:#f9fafb;font-family:system-ui,-apple-system,sans-serif">
<div style="max-width:560px;margin:40px auto;background:#fff;border-radius:12px;border:1px solid #e5e7eb;overflow:hidden">
  {header_html()}
  <div style="padding:32px">
    {inner}
  </div>
  {footer_html(email, slug, name)}
</div>
</body>
</html>"""


def template_followup_unclaimed(listing, city_name):
    name = escape(listing["name"])
    slug = listing["slug"]
    claim_url = f"{SITE_URL}/provider/login?listing={slug}"

    subject = f"{name} — your listing is still unclaimed"

    inner = f"""
    <p style="color:#1a1a1a;font-size:16px;line-height:1.6;margin:0 0 16px">
      Hi,
    </p>
    <p style="color:#4b5563;font-size:15px;line-height:1.6;margin:0 0 16px">
      A few days ago we let you know that <strong>{name}</strong> has a listing on {SITE_NAME}.
      It's still unclaimed — which means attorneys searching for deposition videographers
      in {escape(city_name)} might see an incomplete profile.
    </p>
    <p style="color:#4b5563;font-size:15px;line-height:1.6;margin:0 0 24px">
      Claiming takes 30 seconds and lets you control your profile, add photos,
      and start receiving quote requests from attorneys. It's completely free.
    </p>
    <div style="text-align:center;margin:0 0 24px">
      <a href="{claim_url}"
         style="display:inline-block;background:#2563eb;color:#fff;padding:14px 32px;border-radius:8px;text-decoration:none;font-weight:600;font-size:15px">
        Claim Your Listing
      </a>
    </div>
    <p style="color:#9ca3af;font-size:13px;line-height:1.5;margin:0">
      If this isn't your business, you can <a href="{SITE_URL}/removal-request/?listing={slug}" style="color:#6b7280">request removal</a>.
    </p>"""

    return subject, wrap_email(inner, listing["email"], slug, listing["name"])


def template_followup_incomplete(listing, city_name):
    name = escape(listing["name"])
    slug = listing["slug"]
    dashboard_url = f"{SITE_URL}/provider/dashboard/profile"

    subject = f"Your {SITE_NAME} profile is incomplete — here's what to add"

    inner = f"""
    <p style="color:#1a1a1a;font-size:16px;line-height:1.6;margin:0 0 16px">
      Hi,
    </p>
    <p style="color:#4b5563;font-size:15px;line-height:1.6;margin:0 0 16px">
      Thanks for claiming <strong>{name}</strong> on {SITE_NAME}! Your profile is live,
      but it's not yet complete. Complete profiles get significantly more quote requests.
    </p>
    <p style="color:#4b5563;font-size:15px;line-height:1.6;margin:0 0 8px">
      <strong>Quick wins to boost your profile:</strong>
    </p>
    <table style="width:100%;margin:0 0 24px" cellpadding="0" cellspacing="0">
      <tr>
        <td style="padding:6px 12px 6px 0;vertical-align:top;color:#2563eb;font-size:16px">1.</td>
        <td style="padding:6px 0;color:#4b5563;font-size:14px;line-height:1.5"><strong>Add a description</strong> — Tell attorneys why they should hire you</td>
      </tr>
      <tr>
        <td style="padding:6px 12px 6px 0;vertical-align:top;color:#2563eb;font-size:16px">2.</td>
        <td style="padding:6px 0;color:#4b5563;font-size:14px;line-height:1.5"><strong>Upload photos</strong> — Show your equipment and setup</td>
      </tr>
      <tr>
        <td style="padding:6px 12px 6px 0;vertical-align:top;color:#2563eb;font-size:16px">3.</td>
        <td style="padding:6px 0;color:#4b5563;font-size:14px;line-height:1.5"><strong>List your services</strong> — Realtime streaming? Day-of delivery?</td>
      </tr>
      <tr>
        <td style="padding:6px 12px 6px 0;vertical-align:top;color:#2563eb;font-size:16px">4.</td>
        <td style="padding:6px 0;color:#4b5563;font-size:14px;line-height:1.5"><strong>Add certifications</strong> — CLVS and other credentials</td>
      </tr>
    </table>
    <div style="text-align:center;margin:0 0 24px">
      <a href="{dashboard_url}"
         style="display:inline-block;background:#2563eb;color:#fff;padding:14px 32px;border-radius:8px;text-decoration:none;font-weight:600;font-size:15px">
        Complete Your Profile
      </a>
    </div>
    <p style="color:#9ca3af;font-size:13px;line-height:1.5;margin:0">
      Providers with complete profiles receive 3x more quote requests on average.
    </p>"""

    return subject, wrap_email(inner, listing["email"], slug, listing["name"])


def template_followup_upgrade(listing, city_name):
    name = escape(listing["name"])
    slug = listing["slug"]
    pricing_url = f"{SITE_URL}/pricing/"

    subject = f"Get featured in {escape(city_name)} — limited spots"

    inner = f"""
    <p style="color:#1a1a1a;font-size:16px;line-height:1.6;margin:0 0 16px">
      Hi,
    </p>
    <p style="color:#4b5563;font-size:15px;line-height:1.6;margin:0 0 16px">
      You've been on {SITE_NAME} for a couple of weeks now. How are the quote requests?
    </p>
    <p style="color:#4b5563;font-size:15px;line-height:1.6;margin:0 0 16px">
      I wanted to let you know about our <strong>Sponsored placement</strong> — it pins your listing
      at the top of {escape(city_name)} search results and adds a Featured badge.
      We limit it to <strong>2 spots per city</strong> so it stays meaningful.
    </p>

    <div style="background:#fffbeb;border:1px solid #fde68a;border-radius:10px;padding:20px;margin:0 0 24px">
      <p style="color:#92400e;font-size:14px;font-weight:600;margin:0 0 8px">Sponsored — $79/month</p>
      <ul style="color:#78350f;font-size:14px;line-height:1.8;margin:0;padding-left:20px">
        <li>Pinned #1 in your city</li>
        <li>Featured badge on your listing</li>
        <li>Priority in site-wide search</li>
        <li>Monthly performance report</li>
      </ul>
      <p style="color:#92400e;font-size:13px;margin:12px 0 0">
        The average deposition booking is $800–$1,500. One extra booking pays for a full year.
      </p>
    </div>

    <div style="text-align:center;margin:0 0 24px">
      <a href="{pricing_url}"
         style="display:inline-block;background:#d97706;color:#fff;padding:14px 32px;border-radius:8px;text-decoration:none;font-weight:600;font-size:15px">
        See Pricing & Upgrade
      </a>
    </div>
    <p style="color:#9ca3af;font-size:13px;line-height:1.5;margin:0">
      Not interested? No worries — your free listing stays active. Reply to this email if you have any questions.
    </p>"""

    return subject, wrap_email(inner, listing["email"], slug, listing["name"])


TEMPLATES = {
    "followup-unclaimed": template_followup_unclaimed,
    "followup-incomplete": template_followup_incomplete,
    "followup-upgrade": template_followup_upgrade,
}


def main():
    parser = argparse.ArgumentParser(description="Drip email templates")
    parser.add_argument("--template", choices=list(TEMPLATES.keys()), help="Which template")
    parser.add_argument("--slug", help="Listing slug to use")
    parser.add_argument("--all-templates", action="store_true", help="Preview all templates")
    parser.add_argument("--html", action="store_true", help="Output HTML")
    args = parser.parse_args()

    listings = load_listings()
    cities = load_cities()

    if args.all_templates:
        # Pick a sample listing
        sample = None
        for l in listings.values():
            if l.get("email") and l.get("services") and l.get("certifications"):
                sample = l
                break
        if not sample:
            sample = next(iter(listings.values()))

        city_info = cities.get(sample.get("city", ""), {})
        city_name = city_info.get("city", sample.get("city", ""))

        if args.html:
            print("<html><body style='background:#f0f0f0;padding:20px;font-family:sans-serif'>")
            for tname, tfunc in TEMPLATES.items():
                subject, html = tfunc(sample, city_name)
                print(f"<h2 style='margin:30px 0 10px'>Template: {tname}</h2>")
                print(f"<p><strong>Subject:</strong> {subject}</p>")
                print(html)
                print("<hr>")
            print("</body></html>")
        else:
            for tname, tfunc in TEMPLATES.items():
                subject, _ = tfunc(sample, city_name)
                print(f"Template: {tname}")
                print(f"  Subject: {subject}")
                print(f"  Provider: {sample['name']} <{sample.get('email', 'N/A')}>")
                print()
        return

    if not args.template:
        parser.error("Specify --template or --all-templates")

    slug = args.slug
    if not slug:
        # Pick first listing with email
        for l in listings.values():
            if l.get("email"):
                slug = l["slug"]
                break

    listing = listings.get(slug)
    if not listing:
        print(f"Listing not found: {slug}", file=sys.stderr)
        sys.exit(1)

    city_info = cities.get(listing.get("city", ""), {})
    city_name = city_info.get("city", listing.get("city", ""))

    subject, html = TEMPLATES[args.template](listing, city_name)

    if args.html:
        print(html)
    else:
        print(f"To: {listing.get('email', 'N/A')}")
        print(f"Subject: {subject}")
        print(f"Provider: {listing['name']}")
        print(f"\n--- HTML preview (pipe to file with --html) ---")


if __name__ == "__main__":
    main()
