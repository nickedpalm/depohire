#!/usr/bin/env python3
"""
Geocode listings using OpenStreetMap Nominatim (free, 1 req/sec).
Adds lat/lng to raw_listings in pipeline.db.

Usage:
    python3 scripts/geocode.py --vertical deposition-videographers
    python3 scripts/geocode.py --vertical deposition-videographers --missing-only
"""

import argparse
import json
import sqlite3
import time
from pathlib import Path

import httpx

PROJECT_ROOT = Path(__file__).parent.parent

# Nominatim requires a unique User-Agent
USER_AGENT = "directory-factory/1.0 (geocoding for directory site)"


def get_db(vertical: str) -> sqlite3.Connection:
    db_path = PROJECT_ROOT / "verticals" / vertical / "pipeline.db"
    if not db_path.exists():
        print(f"Error: Database not found at {db_path}")
        raise SystemExit(1)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def load_cities() -> dict:
    """Load cities.json for fallback coordinates."""
    cities_path = PROJECT_ROOT / "template" / "src" / "data" / "cities.json"
    with open(cities_path) as f:
        return {c["slug"]: c for c in json.load(f)}


def geocode_address(address: str, city: str, state: str) -> tuple[float, float] | None:
    """Geocode an address via Nominatim. Returns (lat, lng) or None."""
    query = f"{address}, {city}, {state}, USA" if address else f"{city}, {state}, USA"

    try:
        resp = httpx.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": query, "format": "json", "limit": 1, "countrycodes": "us"},
            headers={"User-Agent": USER_AGENT},
            timeout=10,
        )
        resp.raise_for_status()
        results = resp.json()
        if results:
            return float(results[0]["lat"]), float(results[0]["lon"])
    except Exception as e:
        print(f"    Geocode error: {e}")

    return None


def main():
    parser = argparse.ArgumentParser(description="Geocode listings via Nominatim")
    parser.add_argument("--vertical", required=True, help="Vertical slug")
    parser.add_argument("--missing-only", action="store_true", help="Only geocode listings without coordinates")
    args = parser.parse_args()

    conn = get_db(args.vertical)
    cities = load_cities()

    if args.missing_only:
        listings = conn.execute("""
            SELECT * FROM raw_listings WHERE vertical = ? AND (lat IS NULL OR lat = 0)
        """, (args.vertical,)).fetchall()
    else:
        listings = conn.execute(
            "SELECT * FROM raw_listings WHERE vertical = ?", (args.vertical,)
        ).fetchall()

    print(f"Geocoding {len(listings)} listings for {args.vertical}")

    geocoded = 0
    fallback = 0

    for i, listing in enumerate(listings):
        name = listing["name"]
        city = listing["city"] or ""
        state = listing["state"] or ""
        address = listing["address"] or ""

        # Skip if already has coordinates and not forcing re-geocode
        if args.missing_only and listing["lat"] and listing["lat"] != 0:
            continue

        # Try to geocode with full address first
        coords = None
        if address and len(address) > 5:
            coords = geocode_address(address, "", state)
            time.sleep(1.1)  # Nominatim rate limit

        # Try city + state
        if not coords and city:
            city_name = city.replace("-", " ").title()
            coords = geocode_address("", city_name, state)
            time.sleep(1.1)

        # Fallback to city center from cities.json
        if not coords and city in cities:
            coords = (cities[city]["lat"], cities[city]["lng"])
            fallback += 1

        if coords:
            conn.execute(
                "UPDATE raw_listings SET lat = ?, lng = ? WHERE id = ?",
                (coords[0], coords[1], listing["id"])
            )
            geocoded += 1
            if (i + 1) % 10 == 0:
                print(f"  {i+1}/{len(listings)} processed...")
                conn.commit()

    conn.commit()
    print(f"\nGeocoded: {geocoded}/{len(listings)} ({fallback} used city-center fallback)")
    conn.close()


if __name__ == "__main__":
    main()
