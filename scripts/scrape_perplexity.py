#!/usr/bin/env python3
"""
Scrape listings via Perplexity API — web-grounded search for real businesses.
Queries by state to minimize API calls (economical).

Usage:
    python3 scripts/scrape_perplexity.py --config configs/deposition-videographers.yaml --vertical deposition-videographers
    python3 scripts/scrape_perplexity.py --config configs/deposition-videographers.yaml --vertical deposition-videographers --states NY,CA,TX
"""

import argparse
import json
import os
import re
import sqlite3
import sys
import time
from pathlib import Path

import httpx
import yaml

PROJECT_ROOT = Path(__file__).parent.parent

# Top litigation states, ordered by market size — query these first
TOP_STATES = [
    "CA", "NY", "TX", "FL", "IL", "PA", "OH", "GA", "NJ", "MA",
    "NC", "VA", "TN", "MD", "MO", "CO", "AZ", "WA", "MN", "IN",
    "MI", "WI", "OR", "LA", "NV", "KY", "OK", "NE", "NM", "DC",
]


def get_db(vertical: str) -> sqlite3.Connection:
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
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY,
            listing_id INTEGER REFERENCES raw_listings(id),
            source TEXT NOT NULL,
            author TEXT,
            rating REAL,
            text TEXT,
            date TEXT,
            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(listing_id, source, author, date)
        );
        CREATE TABLE IF NOT EXISTS sentiment (
            listing_id INTEGER PRIMARY KEY REFERENCES raw_listings(id),
            label TEXT NOT NULL,
            score REAL NOT NULL,
            keywords JSON,
            highlights JSON,
            summary TEXT,
            analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    return conn


def load_config(config_path: str) -> dict:
    with open(config_path) as f:
        return yaml.safe_load(f)


def load_cities() -> dict:
    """Load cities.json, return lookup by state abbreviation."""
    cities_path = PROJECT_ROOT / "template" / "src" / "data" / "cities.json"
    with open(cities_path) as f:
        cities = json.load(f)
    by_state = {}
    for c in cities:
        by_state.setdefault(c["state"], []).append(c)
    return by_state


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    text = re.sub(r'-+', '-', text)
    return text.strip('-')


def match_city(biz_city: str, state_cities: list[dict]) -> str | None:
    """Match a business city name to our cities.json slugs."""
    biz_lower = biz_city.lower().strip()
    for c in state_cities:
        if c["city"].lower() == biz_lower:
            return c["slug"]
    # Fuzzy: check if city name is contained
    for c in state_cities:
        if biz_lower in c["city"].lower() or c["city"].lower() in biz_lower:
            return c["slug"]
    # No match — use slugified version
    return slugify(biz_city)


def query_perplexity(api_key: str, keyword: str, state: str, state_name: str) -> list[dict]:
    """Query Perplexity for businesses in a state. Returns parsed listings."""

    prompt = f"""Find real {keyword} companies and professionals in {state_name} ({state}).

Search for actual businesses that provide {keyword} services. For each one found, provide:
- Business name
- City
- Phone number (if available)
- Website URL (if available)
- Brief description of their services

Return ONLY a JSON array. No explanation, no markdown. Example format:
[
  {{"name": "Example Video LLC", "city": "Dallas", "phone": "(555) 123-4567", "website": "https://example.com", "description": "Full-service deposition videography"}},
]

Be thorough — include solo practitioners, small firms, and larger companies. Only include real, currently operating businesses."""

    resp = httpx.post(
        "https://api.perplexity.ai/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": "sonar",
            "messages": [
                {"role": "system", "content": "You are a research assistant. Return only valid JSON arrays. No markdown fences, no explanation."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.1,
        },
        timeout=60,
    )
    resp.raise_for_status()
    raw_text = resp.json()["choices"][0]["message"]["content"].strip()

    # Strip markdown fences if present
    if raw_text.startswith("```"):
        raw_text = raw_text.split("\n", 1)[1].rsplit("```", 1)[0].strip()

    # Try to extract JSON array
    try:
        listings = json.loads(raw_text)
        if isinstance(listings, list):
            return listings
    except json.JSONDecodeError:
        # Try to find JSON array in the response
        match = re.search(r'\[.*\]', raw_text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass

    print(f"    Warning: Could not parse response for {state}")
    return []


def main():
    parser = argparse.ArgumentParser(description="Scrape listings via Perplexity API")
    parser.add_argument("--config", required=True, help="Path to vertical YAML config")
    parser.add_argument("--vertical", required=True, help="Vertical slug")
    parser.add_argument("--states", help="Comma-separated state codes (default: top litigation states)")
    parser.add_argument("--limit", type=int, help="Max number of states to query")
    args = parser.parse_args()

    api_key = os.environ.get("PERPLEXITY_API_KEY")
    if not api_key:
        print("Error: PERPLEXITY_API_KEY not set")
        sys.exit(1)

    config = load_config(args.config)
    keyword = config.get("primary_keyword", config["slug"].replace("-", " "))
    cities_by_state = load_cities()
    conn = get_db(args.vertical)

    # Determine which states to query
    if args.states:
        states = [s.strip().upper() for s in args.states.split(",")]
    else:
        states = TOP_STATES

    if args.limit:
        states = states[:args.limit]

    # State name lookup — include states not in cities.json
    state_names = {
        "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas",
        "CA": "California", "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware",
        "DC": "District of Columbia", "FL": "Florida", "GA": "Georgia", "HI": "Hawaii",
        "ID": "Idaho", "IL": "Illinois", "IN": "Indiana", "IA": "Iowa",
        "KS": "Kansas", "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine",
        "MD": "Maryland", "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota",
        "MS": "Mississippi", "MO": "Missouri", "MT": "Montana", "NE": "Nebraska",
        "NV": "Nevada", "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico",
        "NY": "New York", "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio",
        "OK": "Oklahoma", "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island",
        "SC": "South Carolina", "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas",
        "UT": "Utah", "VT": "Vermont", "VA": "Virginia", "WA": "Washington",
        "WV": "West Virginia", "WI": "Wisconsin", "WY": "Wyoming",
    }

    total_found = 0
    print(f"Scraping {config['name']} via Perplexity — {len(states)} states")
    print(f"Keyword: '{keyword}'")
    print()

    for i, state in enumerate(states):
        state_name = state_names.get(state, state)
        print(f"[{i+1}/{len(states)}] {state_name} ({state})...", end=" ", flush=True)

        try:
            listings = query_perplexity(api_key, keyword, state, state_name)
            print(f"{len(listings)} found")

            state_cities = cities_by_state.get(state, [])

            for biz in listings:
                name = biz.get("name", "").strip()
                if not name:
                    continue

                biz_city = biz.get("city", "").strip()
                city_slug = match_city(biz_city, state_cities) if biz_city else None

                try:
                    conn.execute("""
                        INSERT INTO raw_listings (vertical, source, name, city, state, address, phone, website, raw_data)
                        VALUES (?, 'perplexity', ?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(vertical, name, city) DO UPDATE SET
                            phone = COALESCE(excluded.phone, phone),
                            website = COALESCE(excluded.website, website),
                            raw_data = COALESCE(excluded.raw_data, raw_data),
                            scraped_at = CURRENT_TIMESTAMP
                    """, (
                        args.vertical,
                        name,
                        city_slug,
                        state,
                        biz.get("address", ""),
                        biz.get("phone", ""),
                        biz.get("website", ""),
                        json.dumps(biz),
                    ))
                    total_found += 1
                except Exception as e:
                    print(f"    DB error for {name}: {e}")

            conn.commit()

            # Rate limit — be polite
            if i < len(states) - 1:
                time.sleep(1)

        except Exception as e:
            print(f"ERROR: {e}")

    # Summary
    db_total = conn.execute(
        "SELECT COUNT(*) FROM raw_listings WHERE vertical = ?", (args.vertical,)
    ).fetchone()[0]

    print(f"\n{'='*50}")
    print(f"New listings found: {total_found}")
    print(f"Total in database: {db_total}")
    print(f"API calls made: {len(states)}")
    conn.close()


if __name__ == "__main__":
    main()
