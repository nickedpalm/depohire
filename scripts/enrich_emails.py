#!/usr/bin/env python3
"""
Email enrichment for DepoHire listings using Perplexity Sonar.

Reads all listing JSON files, finds entries with empty emails,
queries Perplexity to find contact emails, and writes results to
a CSV for review before merging back into JSON.

Usage:
    # Dry run — find emails, write to CSV only
    PERPLEXITY_API_KEY=xxx python3 scripts/enrich_emails.py

    # Merge approved CSV back into JSON files
    python3 scripts/enrich_emails.py --merge enriched_emails.csv

    # Limit to N listings (for testing)
    PERPLEXITY_API_KEY=xxx python3 scripts/enrich_emails.py --limit 10

    # Skip CSV, write directly to JSON (use with care)
    PERPLEXITY_API_KEY=xxx python3 scripts/enrich_emails.py --write-direct
"""

import argparse
import csv
import glob
import json
import os
import re
import sys
import time
from pathlib import Path

import httpx

PROJECT_ROOT = Path(__file__).parent.parent
LISTINGS_DIR = PROJECT_ROOT / "src" / "data" / "listings"
OUTPUT_CSV   = PROJECT_ROOT / "scripts" / "enriched_emails.csv"

# ─── Perplexity query ───────────────────────────────────────────────────────

def query_email(api_key: str, name: str, city: str, state: str, website: str) -> dict:
    """
    Ask Perplexity Sonar to find the contact email for a business.
    Returns dict with keys: email, confidence, source, notes
    """
    website_hint = f" Their website is {website}." if website and website != "Not provided" else ""
    prompt = f"""Find the contact email address for this business:

Business: {name}
Location: {city}, {state}
{website_hint}

Search their website, any legal directories, Google Business profile, or other sources.
Return ONLY a JSON object with no markdown, no explanation:
{{
  "email": "contact@example.com or null if not found",
  "confidence": "high/medium/low",
  "source": "where you found it (e.g. website contact page, google listing)",
  "notes": "any relevant notes or null"
}}

Only return a real email address you actually found. If you cannot find one, return null for email."""

    try:
        resp = httpx.post(
            "https://api.perplexity.ai/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "sonar",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a research assistant. Return only valid JSON. No markdown fences, no explanation."
                    },
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.1,
            },
            timeout=30,
        )
        resp.raise_for_status()
        raw = resp.json()["choices"][0]["message"]["content"].strip()

        # Strip markdown fences
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()

        result = json.loads(raw)
        return result

    except json.JSONDecodeError as e:
        print(f"    JSON parse error: {e} — raw: {raw[:100]}")
        return {"email": None, "confidence": "low", "source": "parse_error", "notes": str(e)}
    except Exception as e:
        print(f"    API error: {e}")
        return {"email": None, "confidence": "low", "source": "api_error", "notes": str(e)}


# ─── Email validation ────────────────────────────────────────────────────────

EMAIL_RE = re.compile(r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$')
# Common false positives to reject
JUNK_DOMAINS = {
    'example.com', 'test.com', 'email.com', 'domain.com',
    'yourcompany.com', 'company.com', 'sentry.io', 'sentry-next.wixpress.com',
}

def is_valid_email(email) -> bool:
    if not email or not isinstance(email, str):
        return False
    email = email.strip().lower()
    if not EMAIL_RE.match(email):
        return False
    domain = email.split('@')[1]
    if domain in JUNK_DOMAINS:
        return False
    # Reject image/asset false positives
    if email.endswith(('.png', '.jpg', '.gif', '.svg', '.webp', '.js', '.css')):
        return False
    return True


# ─── Load / save JSON listings ───────────────────────────────────────────────

def load_all_listings() -> list[dict]:
    """Load all listing JSON files. Returns flat list with __file__ key injected."""
    listings = []
    for f in sorted(glob.glob(str(LISTINGS_DIR / "*.json"))):
        city_listings = json.load(open(f))
        for l in city_listings:
            l['__file'] = f
        listings.extend(city_listings)
    return listings


def save_listings_file(filepath: str, listings: list[dict]):
    """Save listings back to JSON file, stripping internal __file key."""
    clean = [{k: v for k, v in l.items() if k != '__file'} for l in listings]
    with open(filepath, 'w') as f:
        json.dump(clean, f, indent=2)
    print(f"  Saved {filepath}")


# ─── Main: enrich ────────────────────────────────────────────────────────────

def run_enrichment(api_key: str, limit: int = None, write_direct: bool = False):
    all_listings = load_all_listings()

    # Only process listings without emails and with a name + city
    targets = [
        l for l in all_listings
        if not l.get('email')
        and l.get('name')
        and l.get('city')
    ]

    if limit:
        targets = targets[:limit]

    total = len(targets)
    has_website = sum(1 for l in targets if l.get('website') and l['website'] != 'Not provided')
    print(f"\nDepoHire Email Enrichment — Perplexity Sonar")
    print(f"{'='*50}")
    print(f"Total listings without email: {total}")
    print(f"  With website URL: {has_website}")
    print(f"  Without website:  {total - has_website}")
    if limit:
        print(f"  (Limited to first {limit})")
    print()

    results = []
    found = 0
    not_found = 0
    errors = 0

    for i, listing in enumerate(targets):
        name    = listing['name']
        city    = listing.get('city', '')
        state   = listing.get('state', '')
        website = listing.get('website', '')
        slug    = listing.get('slug', '')

        print(f"[{i+1}/{total}] {name} ({city}, {state})", end=' ... ', flush=True)

        result = query_email(api_key, name, city, state, website)
        email = result.get('email')

        if is_valid_email(email):
            print(f"✓ {email} ({result.get('confidence', '?')} — {result.get('source', '?')})")
            found += 1
        else:
            email = None
            print(f"✗ not found")
            not_found += 1

        row = {
            'slug':       slug,
            'name':       name,
            'city':       city,
            'state':      state,
            'website':    website,
            'email':      email or '',
            'confidence': result.get('confidence', ''),
            'source':     result.get('source', ''),
            'notes':      result.get('notes', '') or '',
            '__file':     listing['__file'],
        }
        results.append(row)

        # Write direct if requested
        if write_direct and email:
            listing['email'] = email

        # Rate limit — Perplexity sonar is billed per request
        if i < total - 1:
            time.sleep(0.5)

    # ── Summary ──
    print(f"\n{'='*50}")
    print(f"Results: {found} found / {not_found} not found / {errors} errors")
    print(f"Find rate: {found/total*100:.1f}%")

    if write_direct:
        # Group by file and save
        by_file: dict[str, list] = {}
        for listing in all_listings:
            by_file.setdefault(listing['__file'], []).append(listing)
        for filepath, file_listings in by_file.items():
            # Only save files that had changes
            if any(r['__file'] == filepath and r['email'] for r in results):
                save_listings_file(filepath, file_listings)
        print(f"\nWrote emails directly to JSON files.")
    else:
        # Write CSV for review
        csv_fields = ['slug', 'name', 'city', 'state', 'website', 'email', 'confidence', 'source', 'notes', '__file']
        with open(OUTPUT_CSV, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=csv_fields)
            writer.writeheader()
            writer.writerows(results)
        print(f"\nWrote {len(results)} rows to: {OUTPUT_CSV}")
        print(f"Review the CSV, then run:")
        print(f"  python3 scripts/enrich_emails.py --merge {OUTPUT_CSV}")


# ─── Main: merge CSV back into JSON ─────────────────────────────────────────

def run_merge(csv_path: str):
    """Merge reviewed CSV back into listing JSON files."""
    print(f"\nMerging {csv_path} into listing JSON files...")

    # Load CSV
    rows = []
    with open(csv_path, newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get('email') and is_valid_email(row['email']):
                rows.append(row)

    print(f"Found {len(rows)} rows with valid emails to merge.")

    # Build slug → email map
    slug_to_email = {r['slug']: r['email'].strip() for r in rows if r['slug']}

    # Load all JSON files and update
    updated = 0
    files_changed = set()

    for filepath in sorted(glob.glob(str(LISTINGS_DIR / "*.json"))):
        listings = json.load(open(filepath))
        changed = False
        for listing in listings:
            slug = listing.get('slug', '')
            if slug in slug_to_email and not listing.get('email'):
                listing['email'] = slug_to_email[slug]
                print(f"  ✓ {listing['name']} ({listing.get('city')}) → {slug_to_email[slug]}")
                updated += 1
                changed = True
                files_changed.add(filepath)

        if changed:
            with open(filepath, 'w') as f:
                json.dump(listings, f, indent=2)

    print(f"\nUpdated {updated} listings across {len(files_changed)} files.")
    print("Next: rebuild and deploy — run npm run build in /tmp/depohire-build")


# ─── Entry point ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='Enrich DepoHire listing emails via Perplexity Sonar')
    parser.add_argument('--limit',        type=int, help='Max listings to process (for testing)')
    parser.add_argument('--write-direct', action='store_true', help='Write to JSON directly instead of CSV')
    parser.add_argument('--merge',        type=str, help='Path to reviewed CSV to merge back into JSON')
    args = parser.parse_args()

    if args.merge:
        run_merge(args.merge)
        return

    api_key = os.environ.get('PERPLEXITY_API_KEY')
    if not api_key:
        print("Error: PERPLEXITY_API_KEY environment variable not set")
        print("Usage: PERPLEXITY_API_KEY=xxx python3 scripts/enrich_emails.py")
        sys.exit(1)

    run_enrichment(api_key, limit=args.limit, write_direct=args.write_direct)


if __name__ == '__main__':
    main()
