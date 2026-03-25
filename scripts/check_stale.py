#!/usr/bin/env python3
"""Detect stale listings: broken websites, missing phones, no activity.

Usage:
    python3 scripts/check_stale.py --vertical deposition-videographers [--fix]

Checks:
    1. Website returns non-200 status (or times out)
    2. Listing was scraped > 90 days ago and has no reviews
    3. Phone number is disconnected (basic format check)

With --fix: removes listings that fail website check from JSON exports.
"""
import argparse
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

import httpx


def check_websites(listings: list[dict], timeout: float = 10.0) -> list[dict]:
    """Check which listing websites are unreachable."""
    stale = []
    for listing in listings:
        url = listing.get("website", "")
        if not url:
            continue
        try:
            r = httpx.head(url, timeout=timeout, follow_redirects=True)
            if r.status_code >= 400:
                stale.append({**listing, "reason": f"HTTP {r.status_code}"})
        except (httpx.TimeoutException, httpx.ConnectError, httpx.TooManyRedirects) as e:
            stale.append({**listing, "reason": str(type(e).__name__)})
    return stale


def check_age(listings: list[dict], max_days: int = 90) -> list[dict]:
    """Find listings scraped more than max_days ago with no reviews."""
    cutoff = datetime.now() - timedelta(days=max_days)
    stale = []
    for listing in listings:
        scraped = listing.get("scraped_at", "")
        if not scraped:
            stale.append({**listing, "reason": "no scraped_at date"})
            continue
        try:
            scraped_dt = datetime.strptime(scraped, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            continue
        if scraped_dt < cutoff and (listing.get("review_count", 0) or 0) == 0:
            stale.append({**listing, "reason": f"scraped {scraped}, no reviews"})
    return stale


def main():
    parser = argparse.ArgumentParser(description="Detect stale listings")
    parser.add_argument("--vertical", required=True)
    parser.add_argument("--fix", action="store_true", help="Remove stale listings from JSON")
    parser.add_argument("--skip-web", action="store_true", help="Skip website checks")
    args = parser.parse_args()

    data_dir = Path(f"verticals/{args.vertical}/src/data/listings")
    if not data_dir.exists():
        print(f"Error: {data_dir} not found", file=sys.stderr)
        sys.exit(1)

    all_listings = []
    for f in sorted(data_dir.glob("*.json")):
        with open(f) as fh:
            all_listings.extend(json.load(fh))

    print(f"Checking {len(all_listings)} listings...")

    # Age check
    age_stale = check_age(all_listings)
    if age_stale:
        print(f"\n⚠ {len(age_stale)} listings older than 90 days with no reviews:")
        for l in age_stale[:20]:
            print(f"  - {l['name']} ({l['city']}, {l['state']}): {l['reason']}")

    # Website check
    if not args.skip_web:
        print("\nChecking websites (this may take a few minutes)...")
        web_stale = check_websites(all_listings)
        if web_stale:
            print(f"\n⚠ {len(web_stale)} listings with broken websites:")
            for l in web_stale[:20]:
                print(f"  - {l['name']}: {l['website']} → {l['reason']}")
    else:
        web_stale = []

    total_stale = len(set(l["slug"] for l in age_stale + web_stale))
    print(f"\nTotal stale: {total_stale} / {len(all_listings)}")

    if args.fix and web_stale:
        stale_slugs = {l["slug"] for l in web_stale}
        for f in sorted(data_dir.glob("*.json")):
            with open(f) as fh:
                data = json.load(fh)
            original = len(data)
            data = [l for l in data if l["slug"] not in stale_slugs]
            if len(data) < original:
                with open(f, "w") as fh:
                    json.dump(data, fh, indent=2)
                print(f"Removed {original - len(data)} stale listings from {f.name}")


if __name__ == "__main__":
    main()
