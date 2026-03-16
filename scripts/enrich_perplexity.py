#!/usr/bin/env python3
"""
Use Perplexity API to find missing contact info (email, phone) for listings.
Batches ~5 businesses per query, grouped by city.

Usage:
    python3 scripts/enrich_perplexity.py --vertical deposition-videographers [--dry-run] [--limit N]

Requires: PERPLEXITY_API_KEY environment variable.
"""

import argparse
import json
import os
import re
import sqlite3
import time
from pathlib import Path

import httpx

PROJECT_ROOT = Path(__file__).parent.parent

PERPLEXITY_URL = "https://api.perplexity.ai/chat/completions"
BATCH_SIZE = 5

EMAIL_RE = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b')
PHONE_RE = re.compile(r'(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b')

JUNK_DOMAINS = {
    'example.com', 'example.org', 'gmail.com', 'yahoo.com', 'hotmail.com',
    'outlook.com', 'aol.com', 'icloud.com', 'protonmail.com',
    'sentry.io', 'wixpress.com', 'w3.org', 'schema.org',
    'googleapis.com', 'google.com', 'facebook.com', 'twitter.com',
}


def query_perplexity(prompt: str, api_key: str) -> str | None:
    """Send a query to Perplexity and return the response text."""
    try:
        resp = httpx.post(
            PERPLEXITY_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "sonar",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a research assistant finding business contact information. Return ONLY valid JSON. No markdown, no explanation.",
                    },
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.1,
                "max_tokens": 1000,
            },
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"    API error: {e}")
        return None


def parse_response(text: str, names: list[str]) -> dict:
    """Parse Perplexity response into {name: {email, phone}} dict."""
    results = {}
    if not text:
        return results

    # Try to parse as JSON
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r'^```\w*\n?', '', text)
        text = re.sub(r'\n?```$', '', text)
        text = text.strip()

    try:
        data = json.loads(text)
        if isinstance(data, list):
            for item in data:
                name = item.get("name", item.get("business", ""))
                email = item.get("email", "")
                phone = item.get("phone", "")
                if name:
                    results[name.lower().strip()] = {
                        "email": email if email and "@" in email else "",
                        "phone": phone or "",
                    }
        elif isinstance(data, dict):
            for key, val in data.items():
                if isinstance(val, dict):
                    results[key.lower().strip()] = {
                        "email": val.get("email", "") or "",
                        "phone": val.get("phone", "") or "",
                    }
    except json.JSONDecodeError:
        # Fall back to regex extraction
        for name in names:
            section = text.lower()
            idx = section.find(name.lower())
            if idx == -1:
                continue
            chunk = text[idx:idx + 300]
            emails = EMAIL_RE.findall(chunk)
            phones = PHONE_RE.findall(chunk)
            email = emails[0] if emails else ""
            phone = phones[0] if phones else ""
            if email or phone:
                results[name.lower().strip()] = {"email": email, "phone": phone}

    return results


def is_valid_email(email: str) -> bool:
    if not email or "@" not in email:
        return False
    domain = email.split("@")[-1].lower()
    if domain in JUNK_DOMAINS:
        return False
    if email.endswith(('.png', '.jpg', '.gif', '.svg', '.css', '.js')):
        return False
    return len(email) <= 80


def main():
    parser = argparse.ArgumentParser(description="Enrich contact info via Perplexity API")
    parser.add_argument("--vertical", required=True, help="Vertical slug")
    parser.add_argument("--dry-run", action="store_true", help="Show plan without calling API")
    parser.add_argument("--limit", type=int, default=0, help="Limit number of API calls")
    parser.add_argument("--email-only", action="store_true", help="Only find missing emails")
    parser.add_argument("--phone-only", action="store_true", help="Only find missing phones")
    args = parser.parse_args()

    api_key = os.environ.get("PERPLEXITY_API_KEY")
    if not api_key and not args.dry_run:
        print("Error: PERPLEXITY_API_KEY not set")
        raise SystemExit(1)

    db_path = PROJECT_ROOT / "verticals" / args.vertical / "pipeline.db"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")

    # Get listings needing contact info
    rows = conn.execute("""
        SELECT id, name, city, state, phone, email, website
        FROM raw_listings
        WHERE (email IS NULL OR email = '' OR phone IS NULL OR phone = '')
        ORDER BY city, name
    """).fetchall()

    need_email = [r for r in rows if not r["email"]]
    need_phone = [r for r in rows if not r["phone"]]

    print(f"Listings missing email: {len(need_email)}")
    print(f"Listings missing phone: {len(need_phone)}")

    # Build batches grouped by city
    if args.email_only:
        targets = need_email
    elif args.phone_only:
        targets = need_phone
    else:
        # Union: anything missing email OR phone
        seen = set()
        targets = []
        for r in rows:
            if r["id"] not in seen:
                seen.add(r["id"])
                targets.append(r)

    print(f"Total to query: {len(targets)}")

    # Group by city
    by_city = {}
    for r in targets:
        by_city.setdefault(r["city"], []).append(r)

    # Build batches
    batches = []
    for city, city_rows in by_city.items():
        for i in range(0, len(city_rows), BATCH_SIZE):
            batches.append(city_rows[i:i + BATCH_SIZE])

    print(f"Batches ({BATCH_SIZE}/batch): {len(batches)}")
    print(f"Estimated cost: ~${len(batches) * 1 / 1000:.2f}")

    if args.dry_run:
        print("\nDry run — no API calls.")
        conn.close()
        return

    if args.limit:
        batches = batches[:args.limit]
        print(f"Limited to {args.limit} API calls")

    stats = {"email": 0, "phone": 0, "queries": 0, "errors": 0}

    print(f"\nQuerying Perplexity for {len(batches)} batches...")
    for i, batch in enumerate(batches):
        if (i + 1) % 20 == 0 or (i + 1) == len(batches):
            print(f"  Progress: {i + 1}/{len(batches)} (emails: +{stats['email']}, phones: +{stats['phone']})")

        city = batch[0]["city"]
        state = batch[0]["state"]
        names = [r["name"] for r in batch]

        # Build fields to find
        fields = []
        for r in batch:
            missing = []
            if not r["email"]:
                missing.append("email")
            if not r["phone"]:
                missing.append("phone")
            fields.append(f"- {r['name']} (need: {', '.join(missing)})")

        prompt = f"""Find the business contact email address and phone number for these companies in {city}, {state}:

{chr(10).join(fields)}

Return a JSON array with objects like: {{"name": "Business Name", "email": "contact@example.com", "phone": "(555) 123-4567"}}
If you cannot find a piece of info, use an empty string. Only include real, verified contact info you find online."""

        text = query_perplexity(prompt, api_key)
        stats["queries"] += 1

        if not text:
            stats["errors"] += 1
            time.sleep(1)
            continue

        results = parse_response(text, names)

        # Match results back to listings and update DB
        for row in batch:
            name_lower = row["name"].lower().strip()
            info = results.get(name_lower)
            if not info:
                # Try fuzzy match
                for key, val in results.items():
                    if key in name_lower or name_lower in key:
                        info = val
                        break
            if not info:
                continue

            updates = []
            params = []

            if not row["email"] and info.get("email") and is_valid_email(info["email"]):
                updates.append("email = ?")
                params.append(info["email"].lower().strip())
                stats["email"] += 1

            if not row["phone"] and info.get("phone") and len(re.sub(r'\D', '', info["phone"])) >= 10:
                updates.append("phone = ?")
                params.append(info["phone"])
                stats["phone"] += 1

            if updates:
                # Update contact_method if we found email
                if not row["email"] and info.get("email") and is_valid_email(info["email"]):
                    updates.append("contact_method = 'email'")

                params.append(row["id"])
                conn.execute(
                    f"UPDATE raw_listings SET {', '.join(updates)} WHERE id = ?",
                    params,
                )

        # Commit every 20 batches
        if (i + 1) % 20 == 0:
            conn.commit()

        # Rate limit: ~1 req/sec
        time.sleep(1)

    conn.commit()
    conn.close()

    print(f"\nDone!")
    print(f"  API queries: {stats['queries']}")
    print(f"  Emails found: {stats['email']}")
    print(f"  Phones found: {stats['phone']}")
    print(f"  Errors: {stats['errors']}")
    print(f"\nRun: python3 scripts/export.py --vertical {args.vertical}")


if __name__ == "__main__":
    main()
