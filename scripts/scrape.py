#!/usr/bin/env python3
"""
Scraping pipeline for directory-factory.
Collects business listings from Google Maps, Yelp, and custom sources.
Data is stored in SQLite (pipeline.db).

Usage:
    python3 scripts/scrape.py --config configs/deposition-videographers.yaml [--city new-york | --all]
"""

import argparse
import json
import os
import sqlite3
import sys
import time
from datetime import datetime
from pathlib import Path

import httpx
import yaml

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent


def get_db(vertical: str) -> sqlite3.Connection:
    """Get or create the pipeline database for a vertical."""
    db_path = PROJECT_ROOT / "verticals" / vertical / "pipeline.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS raw_listings (
            id INTEGER PRIMARY KEY,
            vertical TEXT NOT NULL,
            source TEXT NOT NULL,
            name TEXT NOT NULL,
            city TEXT,
            state TEXT,
            address TEXT,
            phone TEXT,
            website TEXT,
            lat REAL,
            lng REAL,
            raw_data JSON,
            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(vertical, name, city)
        );

        CREATE TABLE IF NOT EXISTS enrichment_log (
            id INTEGER PRIMARY KEY,
            listing_id INTEGER REFERENCES raw_listings(id),
            field TEXT NOT NULL,
            value TEXT,
            source TEXT,
            enriched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    return conn


def load_config(config_path: str) -> dict:
    with open(config_path) as f:
        return yaml.safe_load(f)


def load_cities(city_filter: str | None = None) -> list[dict]:
    """Load cities from the template cities.json."""
    cities_path = PROJECT_ROOT / "template" / "src" / "data" / "cities.json"
    with open(cities_path) as f:
        cities = json.load(f)
    if city_filter:
        cities = [c for c in cities if c["slug"] == city_filter]
    return cities


def upsert_listing(conn: sqlite3.Connection, vertical: str, source: str,
                   name: str, city: str, state: str, address: str = None,
                   phone: str = None, website: str = None,
                   lat: float = None, lng: float = None, raw_data: dict = None):
    """Insert or update a listing in the database."""
    conn.execute("""
        INSERT INTO raw_listings (vertical, source, name, city, state, address, phone, website, lat, lng, raw_data)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(vertical, name, city) DO UPDATE SET
            address = COALESCE(excluded.address, address),
            phone = COALESCE(excluded.phone, phone),
            website = COALESCE(excluded.website, website),
            lat = COALESCE(excluded.lat, lat),
            lng = COALESCE(excluded.lng, lng),
            raw_data = COALESCE(excluded.raw_data, raw_data),
            scraped_at = CURRENT_TIMESTAMP
    """, (vertical, source, name, city, state, address, phone, website, lat, lng,
          json.dumps(raw_data) if raw_data else None))


def scrape_google_maps(config: dict, cities: list[dict], conn: sqlite3.Connection):
    """
    Scrape Google Maps Places API for listings.
    Requires GOOGLE_MAPS_API_KEY environment variable.
    Falls back to a stub if no key is set.
    """
    api_key = os.environ.get("GOOGLE_MAPS_API_KEY")
    vertical = config["slug"]

    query_template = None
    for source in config.get("scrape_sources", []):
        if source["type"] == "google_maps":
            query_template = source["query"]
            break

    if not query_template:
        print("  No google_maps source configured, skipping")
        return

    if not api_key:
        print("  GOOGLE_MAPS_API_KEY not set — running in stub mode (no actual API calls)")
        print(f"  Would search for '{query_template}' in {len(cities)} cities")
        return

    print(f"  Searching for '{query_template}' in {len(cities)} cities...")

    for city in cities:
        query = f"{query_template} in {city['city']}, {city['state']}"
        print(f"    {city['city']}, {city['state']}...", end=" ", flush=True)

        try:
            url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
            params = {
                "query": query,
                "key": api_key,
            }
            resp = httpx.get(url, params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()

            results = data.get("results", [])
            print(f"{len(results)} results")

            for place in results:
                name = place.get("name", "")
                address = place.get("formatted_address", "")
                location = place.get("geometry", {}).get("location", {})
                lat = location.get("lat")
                lng = location.get("lng")

                upsert_listing(
                    conn, vertical, "google_maps",
                    name=name, city=city["slug"], state=city["state"],
                    address=address, lat=lat, lng=lng,
                    raw_data=place,
                )

            conn.commit()
            time.sleep(1)  # Rate limiting

        except Exception as e:
            print(f"ERROR: {e}")

    conn.commit()


def scrape_google_search(config: dict, cities: list[dict], conn: sqlite3.Connection):
    """
    Scrape Google search results for business listings.
    Uses Playwright for rendering. Run via docker exec openclaw-gustavo
    or install Playwright locally.
    """
    vertical = config["slug"]
    query_template = config.get("primary_keyword", config["slug"].replace("-", " "))

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("  Playwright not installed — skipping Google search scrape")
        print("  Install with: pip install playwright && playwright install chromium")
        return

    print(f"  Searching Google for '{query_template}' in {len(cities)} cities...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        for city in cities:
            query = f"{query_template} {city['city']} {city['state']}"
            print(f"    {city['city']}, {city['state']}...", end=" ", flush=True)

            try:
                page.goto(f"https://www.google.com/search?q={query}", wait_until="networkidle")
                time.sleep(2)

                # Extract local pack results
                results = page.query_selector_all('[data-attrid="title"]')
                print(f"{len(results)} results")

                for result in results:
                    name = result.inner_text().strip()
                    if name:
                        upsert_listing(
                            conn, vertical, "google_search",
                            name=name, city=city["slug"], state=city["state"],
                        )

                conn.commit()
                time.sleep(3)  # Rate limiting

            except Exception as e:
                print(f"ERROR: {e}")

        browser.close()

    conn.commit()


def main():
    parser = argparse.ArgumentParser(description="Scrape listings for a directory vertical")
    parser.add_argument("--config", required=True, help="Path to vertical YAML config")
    parser.add_argument("--city", help="Specific city slug to scrape (default: all)")
    parser.add_argument("--source", choices=["google_maps", "google_search", "all"],
                        default="all", help="Which source to scrape")
    args = parser.parse_args()

    config = load_config(args.config)
    cities = load_cities(args.city)
    conn = get_db(config["slug"])

    print(f"Scraping {config['name']} — {len(cities)} cities")
    print(f"Database: verticals/{config['slug']}/pipeline.db")
    print()

    if args.source in ("google_maps", "all"):
        print("[Google Maps]")
        scrape_google_maps(config, cities, conn)
        print()

    if args.source in ("google_search", "all"):
        print("[Google Search]")
        scrape_google_search(config, cities, conn)
        print()

    # Summary
    count = conn.execute("SELECT COUNT(*) FROM raw_listings WHERE vertical = ?",
                         (config["slug"],)).fetchone()[0]
    print(f"Total listings in database: {count}")
    conn.close()


if __name__ == "__main__":
    main()
