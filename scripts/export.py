#!/usr/bin/env python3
"""
Export pipeline: SQLite → JSON files for Astro.
Reads from pipeline.db and writes per-city JSON files to the vertical's
src/data/listings/ directory.

Usage:
    python3 scripts/export.py --vertical deposition-videographers
"""

import argparse
import json
import re
import sqlite3
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent


def slugify(text: str) -> str:
    """Convert text to URL-safe slug."""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    text = re.sub(r'-+', '-', text)
    return text.strip('-')


def get_db(vertical: str) -> sqlite3.Connection:
    db_path = PROJECT_ROOT / "verticals" / vertical / "pipeline.db"
    if not db_path.exists():
        print(f"Error: Database not found at {db_path}")
        raise SystemExit(1)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def get_enrichments(conn: sqlite3.Connection, listing_id: int) -> dict:
    """Get the latest enrichment values for a listing."""
    rows = conn.execute("""
        SELECT field, value FROM enrichment_log
        WHERE listing_id = ?
        ORDER BY enriched_at DESC
    """, (listing_id,)).fetchall()

    enrichments = {}
    for row in rows:
        if row["field"] not in enrichments:
            enrichments[row["field"]] = row["value"]
    return enrichments


def get_sentiment(conn: sqlite3.Connection, listing_id: int) -> dict | None:
    """Get sentiment analysis for a listing."""
    row = conn.execute("""
        SELECT label, score, keywords, highlights, summary
        FROM sentiment WHERE listing_id = ?
    """, (listing_id,)).fetchone()
    if not row:
        return None
    return {
        "label": row["label"],
        "score": row["score"],
        "keywords": json.loads(row["keywords"]) if row["keywords"] else [],
        "highlights": json.loads(row["highlights"]) if row["highlights"] else [],
        "summary": row["summary"] or "",
    }


def get_review_count(conn: sqlite3.Connection, listing_id: int) -> int:
    """Get the number of reviews for a listing."""
    return conn.execute(
        "SELECT COUNT(*) FROM reviews WHERE listing_id = ?", (listing_id,)
    ).fetchone()[0]


def export_listings(vertical: str):
    conn = get_db(vertical)
    output_dir = PROJECT_ROOT / "verticals" / vertical / "src" / "data" / "listings"
    output_dir.mkdir(parents=True, exist_ok=True)

    listings = conn.execute("""
        SELECT * FROM raw_listings
        WHERE vertical = ?
        ORDER BY city, name
    """, (vertical,)).fetchall()

    print(f"Exporting {len(listings)} listings for {vertical}")

    # Group by city
    by_city: dict[str, list] = {}
    for row in listings:
        enrichments = get_enrichments(conn, row["id"])
        raw = json.loads(row["raw_data"]) if row["raw_data"] else {}

        sentiment = get_sentiment(conn, row["id"])

        listing = {
            "slug": slugify(f"{row['name']}-{row['city']}"),
            "name": row["name"],
            "city": row["city"],
            "state": row["state"],
            "address": row["address"] or "",
            "lat": row["lat"] or 0,
            "lng": row["lng"] or 0,
            "phone": row["phone"] or "",
            "website": row["website"] or "",
            "email": enrichments.get("email", raw.get("email", "")),
            "rating": float(enrichments.get("rating", raw.get("rating", 0))),
            "review_count": int(enrichments.get("review_count", raw.get("user_ratings_total", 0))),
            "description": raw.get("description", ""),
            "certifications": raw.get("certifications", []),
            "services": raw.get("services", []),
            "years_experience": raw.get("years_experience"),
            "claimed": False,
            "source": row["source"],
            "scraped_at": row["scraped_at"],
            "sentiment": sentiment,
        }

        city = row["city"] or "unknown"
        by_city.setdefault(city, []).append(listing)

    # Write per-city JSON files
    for city, city_listings in by_city.items():
        output_file = output_dir / f"{city}.json"
        with open(output_file, "w") as f:
            json.dump(city_listings, f, indent=2, default=str)
        print(f"  {city}: {len(city_listings)} listings → {output_file.name}")

    # Clean up city files that no longer have listings
    existing_files = set(output_dir.glob("*.json"))
    expected_files = {output_dir / f"{city}.json" for city in by_city}
    for stale in existing_files - expected_files:
        stale.unlink()
        print(f"  Removed stale: {stale.name}")

    conn.close()
    print(f"\nExported to {output_dir}")


def main():
    parser = argparse.ArgumentParser(description="Export listings from SQLite to JSON for Astro")
    parser.add_argument("--vertical", required=True, help="Vertical slug")
    args = parser.parse_args()
    export_listings(args.vertical)


if __name__ == "__main__":
    main()
