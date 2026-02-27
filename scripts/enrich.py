#!/usr/bin/env python3
"""
Enrichment pipeline for directory-factory.
Takes raw listings from pipeline.db and adds website, email, reviews, social links,
and LLM-powered sentiment analysis.

Usage:
    python3 scripts/enrich.py --vertical deposition-videographers [--listing-id 123]
    python3 scripts/enrich.py --vertical deposition-videographers --sentiment-only
"""

import argparse
import json
import os
import re
import sqlite3
from pathlib import Path

import httpx

PROJECT_ROOT = Path(__file__).parent.parent


def get_db(vertical: str) -> sqlite3.Connection:
    db_path = PROJECT_ROOT / "verticals" / vertical / "pipeline.db"
    if not db_path.exists():
        print(f"Error: Database not found at {db_path}")
        print("Run scrape.py first.")
        raise SystemExit(1)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    # Ensure reviews + sentiment tables exist
    conn.executescript("""
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


def log_enrichment(conn: sqlite3.Connection, listing_id: int, field: str, value: str, source: str):
    conn.execute("""
        INSERT INTO enrichment_log (listing_id, field, value, source)
        VALUES (?, ?, ?, ?)
    """, (listing_id, field, value, source))


def enrich_from_website(conn: sqlite3.Connection, listing: sqlite3.Row):
    """Visit the listing's website and extract email, phone, social links."""
    if not listing["website"]:
        return

    listing_id = listing["id"]
    url = listing["website"]

    try:
        resp = httpx.get(url, timeout=10, follow_redirects=True)
        resp.raise_for_status()
        html = resp.text

        # Extract emails
        emails = set(re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', html))
        # Filter out common false positives
        emails = {e for e in emails if not e.endswith('.png') and not e.endswith('.jpg')}

        if emails:
            email = sorted(emails)[0]  # Pick first alphabetically
            conn.execute("UPDATE raw_listings SET raw_data = json_set(COALESCE(raw_data, '{}'), '$.email', ?) WHERE id = ?",
                         (email, listing_id))
            log_enrichment(conn, listing_id, "email", email, "website_scrape")
            print(f"    Found email: {email}")

        # Extract phone numbers
        phones = re.findall(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', html)
        if phones and not listing["phone"]:
            phone = phones[0]
            conn.execute("UPDATE raw_listings SET phone = ? WHERE id = ?", (phone, listing_id))
            log_enrichment(conn, listing_id, "phone", phone, "website_scrape")
            print(f"    Found phone: {phone}")

        # Extract social links
        social_patterns = {
            "facebook": r'https?://(?:www\.)?facebook\.com/[a-zA-Z0-9._-]+',
            "linkedin": r'https?://(?:www\.)?linkedin\.com/(?:company|in)/[a-zA-Z0-9._-]+',
            "twitter": r'https?://(?:www\.)?(?:twitter|x)\.com/[a-zA-Z0-9._-]+',
            "instagram": r'https?://(?:www\.)?instagram\.com/[a-zA-Z0-9._-]+',
            "youtube": r'https?://(?:www\.)?youtube\.com/(?:@|channel/)[a-zA-Z0-9._-]+',
        }

        for platform, pattern in social_patterns.items():
            matches = re.findall(pattern, html)
            if matches:
                log_enrichment(conn, listing_id, f"social_{platform}", matches[0], "website_scrape")

    except Exception as e:
        print(f"    Error enriching {url}: {e}")


def enrich_from_raw_data(conn: sqlite3.Connection, listing: sqlite3.Row):
    """Extract structured data from the raw_data JSON (e.g., Google Maps response)."""
    if not listing["raw_data"]:
        return

    listing_id = listing["id"]
    raw = json.loads(listing["raw_data"])

    # Google Maps fields
    if listing["source"] == "google_maps":
        rating = raw.get("rating")
        if rating:
            log_enrichment(conn, listing_id, "rating", str(rating), "google_maps")

        review_count = raw.get("user_ratings_total")
        if review_count:
            log_enrichment(conn, listing_id, "review_count", str(review_count), "google_maps")

        # Business status
        status = raw.get("business_status")
        if status and status != "OPERATIONAL":
            log_enrichment(conn, listing_id, "business_status", status, "google_maps")
            print(f"    Warning: {listing['name']} status is {status}")

        # Extract reviews from Google Maps response
        reviews = raw.get("reviews", [])
        for review in reviews:
            try:
                conn.execute("""
                    INSERT OR IGNORE INTO reviews (listing_id, source, author, rating, text, date)
                    VALUES (?, 'google_maps', ?, ?, ?, ?)
                """, (
                    listing_id,
                    review.get("author_name", ""),
                    review.get("rating"),
                    review.get("text", ""),
                    review.get("relative_time_description", ""),
                ))
            except sqlite3.IntegrityError:
                pass

    # Extract reviews embedded in raw_data from any source
    for review in raw.get("reviews", []) if listing["source"] != "google_maps" else []:
        try:
            conn.execute("""
                INSERT OR IGNORE INTO reviews (listing_id, source, author, rating, text, date)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                listing_id,
                listing["source"],
                review.get("author", ""),
                review.get("rating"),
                review.get("text", ""),
                review.get("date", ""),
            ))
        except sqlite3.IntegrityError:
            pass


def extract_reviews_from_website(conn: sqlite3.Connection, listing: sqlite3.Row):
    """Scrape review/testimonial text from a listing's website."""
    if not listing["website"]:
        return

    listing_id = listing["id"]
    url = listing["website"]

    # Try common testimonial page paths
    testimonial_paths = ["", "/testimonials", "/reviews", "/about"]
    for path in testimonial_paths:
        try:
            target = url.rstrip("/") + path
            resp = httpx.get(target, timeout=10, follow_redirects=True)
            if resp.status_code != 200:
                continue

            from bs4 import BeautifulSoup
            soup = BeautifulSoup(resp.text, "lxml")

            # Look for common review/testimonial patterns
            selectors = [
                'blockquote',
                '[class*="testimonial"]',
                '[class*="review"]',
                '[class*="quote"]',
                '[data-testimonial]',
            ]

            for selector in selectors:
                elements = soup.select(selector)
                for el in elements:
                    text = el.get_text(strip=True)
                    if 20 < len(text) < 2000:  # Plausible review length
                        try:
                            conn.execute("""
                                INSERT OR IGNORE INTO reviews (listing_id, source, author, text)
                                VALUES (?, 'website', '', ?)
                            """, (listing_id, text))
                        except sqlite3.IntegrityError:
                            pass

        except Exception:
            pass


def analyze_sentiment(conn: sqlite3.Connection, listing_id: int, listing_name: str):
    """Run LLM sentiment analysis on all reviews for a listing."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return

    # Check if already analyzed
    existing = conn.execute("SELECT 1 FROM sentiment WHERE listing_id = ?", (listing_id,)).fetchone()
    if existing:
        return

    reviews = conn.execute("""
        SELECT text, rating, author, source FROM reviews
        WHERE listing_id = ? AND text != ''
        ORDER BY rating DESC
    """, (listing_id,)).fetchall()

    if not reviews:
        return

    review_texts = []
    ratings = []
    for r in reviews:
        review_texts.append(f"[{r['source']}] {r['author']}: {r['text']}" if r['author'] else f"[{r['source']}] {r['text']}")
        if r['rating']:
            ratings.append(r['rating'])

    prompt = f"""Analyze the sentiment of these reviews for "{listing_name}".

Reviews:
{chr(10).join(review_texts[:20])}

Respond with ONLY valid JSON (no markdown, no explanation):
{{
  "label": "positive" or "mixed" or "negative",
  "score": 0.0 to 1.0 (0=very negative, 1=very positive),
  "keywords": ["keyword1", "keyword2", ...],
  "highlights": [
    {{"text": "best quote from reviews (max 150 chars)", "sentiment": "positive"}},
    {{"text": "another notable quote", "sentiment": "positive" or "negative"}}
  ],
  "summary": "One sentence summary of overall sentiment and reputation"
}}

Extract 3-6 keywords that describe what reviewers mention most (e.g., "professional", "on-time", "great quality").
Pick 2-4 highlight quotes — prefer short, impactful excerpts. Include negative ones if they exist."""

    try:
        resp = httpx.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-haiku-4-5-20251001",
                "max_tokens": 800,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=30,
        )
        resp.raise_for_status()
        raw_text = resp.json()["content"][0]["text"].strip()

        # Strip markdown code fences if present
        if raw_text.startswith("```"):
            raw_text = raw_text.split("\n", 1)[1].rsplit("```", 1)[0].strip()

        result = json.loads(raw_text)

        conn.execute("""
            INSERT OR REPLACE INTO sentiment (listing_id, label, score, keywords, highlights, summary)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            listing_id,
            result["label"],
            result["score"],
            json.dumps(result.get("keywords", [])),
            json.dumps(result.get("highlights", [])),
            result.get("summary", ""),
        ))
        print(f"    Sentiment: {result['label']} ({result['score']:.2f}) — {result.get('summary', '')[:60]}")

    except Exception as e:
        print(f"    Sentiment analysis error: {e}")

    # Fallback: if no API key or LLM fails, compute simple sentiment from ratings
    if not conn.execute("SELECT 1 FROM sentiment WHERE listing_id = ?", (listing_id,)).fetchone():
        if ratings:
            avg = sum(ratings) / len(ratings)
            label = "positive" if avg >= 4.0 else "mixed" if avg >= 3.0 else "negative"
            score = min(1.0, max(0.0, (avg - 1) / 4))
            conn.execute("""
                INSERT OR REPLACE INTO sentiment (listing_id, label, score, keywords, highlights, summary)
                VALUES (?, ?, ?, '[]', '[]', ?)
            """, (listing_id, label, score, f"Average rating: {avg:.1f}/5 from {len(ratings)} reviews"))
            print(f"    Sentiment (from ratings): {label} ({score:.2f})")


def main():
    parser = argparse.ArgumentParser(description="Enrich scraped listings with additional data")
    parser.add_argument("--vertical", required=True, help="Vertical slug")
    parser.add_argument("--listing-id", type=int, help="Enrich a specific listing (default: all)")
    parser.add_argument("--sentiment-only", action="store_true", help="Only run sentiment analysis (skip scraping)")
    args = parser.parse_args()

    conn = get_db(args.vertical)

    if args.listing_id:
        listings = conn.execute("SELECT * FROM raw_listings WHERE id = ?", (args.listing_id,)).fetchall()
    else:
        listings = conn.execute("SELECT * FROM raw_listings WHERE vertical = ?", (args.vertical,)).fetchall()

    print(f"Enriching {len(listings)} listings for {args.vertical}")

    for listing in listings:
        print(f"  {listing['name']} ({listing['city']}, {listing['state']})")

        if not args.sentiment_only:
            enrich_from_raw_data(conn, listing)
            enrich_from_website(conn, listing)
            extract_reviews_from_website(conn, listing)
            conn.commit()

        # Sentiment analysis (requires reviews in DB or ANTHROPIC_API_KEY)
        review_count = conn.execute(
            "SELECT COUNT(*) FROM reviews WHERE listing_id = ?", (listing["id"],)
        ).fetchone()[0]
        if review_count > 0:
            print(f"    {review_count} reviews found")
            analyze_sentiment(conn, listing["id"], listing["name"])
        conn.commit()

    # Summary
    enrichment_count = conn.execute("""
        SELECT COUNT(DISTINCT listing_id) FROM enrichment_log
        WHERE listing_id IN (SELECT id FROM raw_listings WHERE vertical = ?)
    """, (args.vertical,)).fetchone()[0]
    sentiment_count = conn.execute("""
        SELECT COUNT(*) FROM sentiment
        WHERE listing_id IN (SELECT id FROM raw_listings WHERE vertical = ?)
    """, (args.vertical,)).fetchone()[0]
    review_total = conn.execute("""
        SELECT COUNT(*) FROM reviews
        WHERE listing_id IN (SELECT id FROM raw_listings WHERE vertical = ?)
    """, (args.vertical,)).fetchone()[0]

    print(f"\nEnriched {enrichment_count}/{len(listings)} listings")
    print(f"Reviews: {review_total} total")
    print(f"Sentiment analyzed: {sentiment_count}/{len(listings)} listings")
    conn.close()


if __name__ == "__main__":
    main()
