#!/usr/bin/env python3
"""
Enrich listings with Google Maps Place Details API.
Fetches phone, website, ratings, hours, business status, and Maps URL.

Usage:
    python3 scripts/enrich_places.py --vertical deposition-videographers [--dry-run] [--limit N]

Requires: GOOGLE_MAPS_API_KEY environment variable.
Free within Google's $200/month Maps Platform credit.
"""

import argparse
import json
import os
import sqlite3
import time
from pathlib import Path

import httpx

PROJECT_ROOT = Path(__file__).parent.parent

DETAILS_URL = "https://maps.googleapis.com/maps/api/place/details/json"
FIELDS = "formatted_phone_number,website,rating,user_ratings_total,opening_hours,business_status,url"


def get_db(vertical: str) -> sqlite3.Connection:
    db_path = PROJECT_ROOT / "verticals" / vertical / "pipeline.db"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def get_listings_to_enrich(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute("""
        SELECT id, name, city, state, phone, website, raw_data
        FROM raw_listings
        WHERE raw_data LIKE '%place_id%'
        ORDER BY city, name
    """).fetchall()

    to_enrich = []
    for row in rows:
        raw = json.loads(row["raw_data"]) if row["raw_data"] else {}
        place_id = raw.get("place_id")
        if not place_id:
            continue
        to_enrich.append({
            "id": row["id"],
            "name": row["name"],
            "city": row["city"],
            "place_id": place_id,
            "has_phone": bool(row["phone"]),
            "has_website": bool(row["website"]),
            "has_rating": bool(raw.get("rating")) and raw.get("rating", 0) > 0,
        })
    return to_enrich


def fetch_place_details(place_id: str, api_key: str) -> dict | None:
    try:
        resp = httpx.get(DETAILS_URL, params={
            "place_id": place_id,
            "fields": FIELDS,
            "key": api_key,
        }, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        if data.get("status") != "OK":
            return None
        return data.get("result", {})
    except Exception as e:
        print(f"    ERROR: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(description="Enrich listings with Google Place Details")
    parser.add_argument("--vertical", required=True, help="Vertical slug")
    parser.add_argument("--dry-run", action="store_true", help="Show stats without calling API")
    parser.add_argument("--limit", type=int, default=0, help="Limit API calls (0=all)")
    args = parser.parse_args()

    api_key = os.environ.get("GOOGLE_MAPS_API_KEY")
    if not api_key and not args.dry_run:
        print("Error: GOOGLE_MAPS_API_KEY not set")
        raise SystemExit(1)

    conn = get_db(args.vertical)
    to_enrich = get_listings_to_enrich(conn)

    needs_phone = sum(1 for l in to_enrich if not l["has_phone"])
    needs_website = sum(1 for l in to_enrich if not l["has_website"])
    needs_rating = sum(1 for l in to_enrich if not l["has_rating"])

    print(f"Listings with place_id: {len(to_enrich)}")
    print(f"  Missing phone: {needs_phone}")
    print(f"  Missing website: {needs_website}")
    print(f"  Missing/zero rating: {needs_rating}")

    if args.dry_run:
        print("\nDry run — no API calls made.")
        conn.close()
        return

    if args.limit:
        to_enrich = to_enrich[:args.limit]
        print(f"\nLimited to {args.limit} API calls")

    stats = {"phone": 0, "website": 0, "rating": 0, "hours": 0, "closed": 0, "errors": 0}

    print(f"\nEnriching {len(to_enrich)} listings...")
    for i, listing in enumerate(to_enrich):
        if (i + 1) % 50 == 0 or (i + 1) == len(to_enrich):
            print(f"  Progress: {i + 1}/{len(to_enrich)} (phones: +{stats['phone']}, websites: +{stats['website']}, ratings: +{stats['rating']})")

        details = fetch_place_details(listing["place_id"], api_key)
        if not details:
            stats["errors"] += 1
            continue

        phone = details.get("formatted_phone_number")
        website = details.get("website")
        rating = details.get("rating")
        review_count = details.get("user_ratings_total")
        maps_url = details.get("url")
        business_status = details.get("business_status")
        hours = details.get("opening_hours", {}).get("weekday_text")

        # Build update query
        updates = []
        params = []

        if phone and not listing["has_phone"]:
            updates.append("phone = ?")
            params.append(phone)
            stats["phone"] += 1

        if website and not listing["has_website"]:
            updates.append("website = ?")
            params.append(website)
            stats["website"] += 1

        if maps_url:
            updates.append("google_maps_url = ?")
            params.append(maps_url)

        if business_status:
            updates.append("business_status = ?")
            params.append(business_status)
            if business_status in ("CLOSED_PERMANENTLY", "CLOSED_TEMPORARILY"):
                stats["closed"] += 1

        # Update raw_data with rating, review_count, hours
        raw_row = conn.execute("SELECT raw_data FROM raw_listings WHERE id = ?", (listing["id"],)).fetchone()
        raw = json.loads(raw_row["raw_data"]) if raw_row["raw_data"] else {}
        changed_raw = False

        if rating and not listing["has_rating"]:
            raw["rating"] = rating
            stats["rating"] += 1
            changed_raw = True

        if review_count and not raw.get("user_ratings_total"):
            raw["user_ratings_total"] = review_count
            changed_raw = True

        if hours:
            raw["opening_hours_text"] = hours
            stats["hours"] += 1
            changed_raw = True

        if changed_raw:
            updates.append("raw_data = ?")
            params.append(json.dumps(raw))

        if updates:
            params.append(listing["id"])
            conn.execute(f"UPDATE raw_listings SET {', '.join(updates)} WHERE id = ?", params)

        # Commit every 100 rows
        if (i + 1) % 100 == 0:
            conn.commit()

        # Rate limit: ~10 req/sec
        if (i + 1) % 10 == 0:
            time.sleep(1)

    conn.commit()
    conn.close()

    print(f"\nDone!")
    print(f"  Phones added: {stats['phone']}")
    print(f"  Websites added: {stats['website']}")
    print(f"  Ratings added: {stats['rating']}")
    print(f"  Hours added: {stats['hours']}")
    print(f"  Closed businesses found: {stats['closed']}")
    print(f"  Errors: {stats['errors']}")
    print(f"\nNext: run scripts/enrich_websites.py to scrape emails + contact forms")
    print(f"Then: run scripts/export.py --vertical {args.vertical}")


if __name__ == "__main__":
    main()
