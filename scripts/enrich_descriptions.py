#!/usr/bin/env python3
"""
Scrape listing websites and generate professional descriptions using Claude Haiku.

Finds listings that have a website but no description in raw_data, fetches the
homepage (plus /about and /services if available), extracts text content, and
sends it to Claude Haiku to generate a 2-3 sentence business description.

Usage:
    python3 scripts/enrich_descriptions.py --vertical deposition-videographers [--limit N] [--dry-run]

Requires: ANTHROPIC_API_KEY env var.
"""

import argparse
import json
import os
import sqlite3
import time
from pathlib import Path
from urllib.parse import urlparse

import httpx

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("Install BeautifulSoup: pip install beautifulsoup4")
    raise SystemExit(1)

PROJECT_ROOT = Path(__file__).parent.parent

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

# Subpages to try for additional content
EXTRA_PATHS = ["/about", "/about-us", "/services", "/our-services"]

CLAUDE_PROMPT = (
    "Write a 2-3 sentence professional description for this deposition videography "
    "business based on their website content. Focus on their services, experience, and "
    "what makes them stand out. If the website doesn't appear to be related to "
    "deposition videography, respond with IRRELEVANT."
)


def get_db(vertical: str) -> sqlite3.Connection:
    db_path = PROJECT_ROOT / "verticals" / vertical / "pipeline.db"
    if not db_path.exists():
        print(f"Error: Database not found at {db_path}")
        raise SystemExit(1)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def log_enrichment(conn: sqlite3.Connection, listing_id: int, field: str, value: str, source: str):
    conn.execute("""
        INSERT INTO enrichment_log (listing_id, field, value, source)
        VALUES (?, ?, ?, ?)
    """, (listing_id, field, value, source))


def extract_text(html: str) -> str:
    """Extract readable text from HTML, stripping boilerplate elements."""
    soup = BeautifulSoup(html, "html.parser")

    # Remove non-content elements
    for tag in soup.find_all(["nav", "footer", "header", "script", "style",
                               "noscript", "iframe", "svg", "form"]):
        tag.decompose()

    # Also strip common boilerplate by class/id patterns
    for el in soup.find_all(attrs={"class": lambda c: c and any(
        x in str(c).lower() for x in ["cookie", "popup", "modal", "banner", "sidebar", "widget"]
    )}):
        el.decompose()

    text = soup.get_text(separator=" ", strip=True)

    # Collapse whitespace
    text = " ".join(text.split())
    return text


def fetch_page(url: str, client: httpx.Client) -> str | None:
    """Fetch a URL and return HTML if successful."""
    try:
        resp = client.get(url, follow_redirects=True, timeout=5)
        content_type = resp.headers.get("content-type", "")
        if resp.status_code == 200 and "text/html" in content_type:
            return resp.text
    except (httpx.TimeoutException, httpx.ConnectError, httpx.TooManyRedirects,
            httpx.ReadError, httpx.DecodingError, Exception):
        pass
    return None


def scrape_website_text(website: str, client: httpx.Client) -> str:
    """Scrape the homepage and extra pages, return combined text (truncated)."""
    all_text = []

    # Homepage
    html = fetch_page(website, client)
    if html:
        text = extract_text(html)
        if text:
            all_text.append(text)

    # Try subpages for richer content
    parsed = urlparse(website)
    base = f"{parsed.scheme}://{parsed.netloc}"
    for path in EXTRA_PATHS:
        sub_url = base + path
        html = fetch_page(sub_url, client)
        if html:
            text = extract_text(html)
            if text and len(text) > 50:  # Skip near-empty pages
                all_text.append(text)
                break  # One good subpage is enough
        time.sleep(0.3)

    combined = " ".join(all_text)
    # Truncate to ~2000 chars for the LLM prompt
    if len(combined) > 2000:
        combined = combined[:2000] + "..."
    return combined


def generate_descriptions_batch(
    batch: list[dict], api_key: str
) -> list[dict]:
    """Send a batch of listings to Claude Haiku and return descriptions.

    Each item in batch: {"listing_id": int, "name": str, "city": str, "text": str}
    Returns: list of {"listing_id": int, "description": str | None}
    """
    results = []

    for item in batch:
        listing_id = item["listing_id"]
        name = item["name"]
        city = item["city"]
        text = item["text"]

        if not text or len(text) < 30:
            results.append({"listing_id": listing_id, "description": None})
            continue

        user_msg = (
            f"Business: {name} ({city})\n\n"
            f"Website content:\n{text}\n\n"
            f"{CLAUDE_PROMPT}"
        )

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
                    "max_tokens": 300,
                    "messages": [{"role": "user", "content": user_msg}],
                },
                timeout=30,
            )
            resp.raise_for_status()
            reply = resp.json()["content"][0]["text"].strip()

            if reply.upper().startswith("IRRELEVANT"):
                results.append({"listing_id": listing_id, "description": None})
            else:
                results.append({"listing_id": listing_id, "description": reply})

        except Exception as e:
            print(f"    Claude API error for {name}: {e}")
            results.append({"listing_id": listing_id, "description": None})

    return results


def main():
    parser = argparse.ArgumentParser(
        description="Scrape websites and generate descriptions via Claude Haiku"
    )
    parser.add_argument("--vertical", required=True, help="Vertical slug")
    parser.add_argument("--limit", type=int, default=0, help="Max listings to process")
    parser.add_argument("--dry-run", action="store_true", help="Show candidates only, no scraping")
    args = parser.parse_args()

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key and not args.dry_run:
        print("Error: ANTHROPIC_API_KEY env var required")
        raise SystemExit(1)

    conn = get_db(args.vertical)

    # Find listings with website but no description in raw_data
    rows = conn.execute("""
        SELECT id, name, city, state, website, raw_data
        FROM raw_listings
        WHERE website IS NOT NULL AND website != ''
        ORDER BY city, name
    """).fetchall()

    # Filter to those with empty description AND not already enriched
    already_enriched = set()
    for r in conn.execute("""
        SELECT DISTINCT listing_id FROM enrichment_log WHERE field = 'description'
    """).fetchall():
        already_enriched.add(r["listing_id"])

    candidates = []
    for row in rows:
        if row["id"] in already_enriched:
            continue
        raw = json.loads(row["raw_data"]) if row["raw_data"] else {}
        desc = raw.get("description", "")
        if desc:
            continue  # Already has a description
        candidates.append(row)

    print(f"Total listings with website: {len(rows)}")
    print(f"Already enriched (in enrichment_log): {len(already_enriched)}")
    print(f"Already have description in raw_data: {len(rows) - len(candidates) - len(already_enriched)}")
    print(f"Candidates to enrich: {len(candidates)}")

    if args.dry_run:
        print("\nDry run — showing first 20 candidates:")
        for c in candidates[:20]:
            print(f"  [{c['id']}] {c['name']} ({c['city']}, {c['state']}) — {c['website']}")
        conn.close()
        return

    if not candidates:
        print("\nNo listings need description enrichment.")
        conn.close()
        return

    if args.limit:
        candidates = candidates[:args.limit]
        print(f"\nLimited to {args.limit} listings")

    print(f"\nProcessing {len(candidates)} listings...")

    client = httpx.Client(headers=HEADERS, follow_redirects=True)
    stats = {"scraped": 0, "described": 0, "irrelevant": 0, "empty_page": 0, "errors": 0}

    # Process in batches of 5 for Claude calls
    batch = []

    def flush_batch(batch_items: list[dict], conn: sqlite3.Connection):
        """Send batch to Claude and save results."""
        if not batch_items:
            return
        results = generate_descriptions_batch(batch_items, api_key)
        for result in results:
            lid = result["listing_id"]
            desc = result["description"]
            if desc:
                # Store in raw_data JSON
                conn.execute("""
                    UPDATE raw_listings
                    SET raw_data = json_set(COALESCE(raw_data, '{}'), '$.description', ?)
                    WHERE id = ?
                """, (desc, lid))
                log_enrichment(conn, lid, "description", desc, "website_scrape+claude")
                stats["described"] += 1
            else:
                # Log that we tried but got nothing useful
                log_enrichment(conn, lid, "description", "", "website_scrape+claude")
                if any(b["listing_id"] == lid and b["text"] for b in batch_items):
                    stats["irrelevant"] += 1
                else:
                    stats["empty_page"] += 1
        conn.commit()

    for i, row in enumerate(candidates):
        if (i + 1) % 10 == 0 or (i + 1) == len(candidates):
            print(
                f"  Progress: {i + 1}/{len(candidates)} "
                f"(described: {stats['described']}, irrelevant: {stats['irrelevant']}, "
                f"empty: {stats['empty_page']}, errors: {stats['errors']})"
            )

        try:
            text = scrape_website_text(row["website"], client)
            stats["scraped"] += 1
        except Exception as e:
            print(f"    Scrape error for {row['name']}: {e}")
            stats["errors"] += 1
            # Still log so we don't retry
            log_enrichment(conn, row["id"], "description", "", "website_scrape+claude")
            conn.commit()
            continue

        batch.append({
            "listing_id": row["id"],
            "name": row["name"],
            "city": row["city"] or "",
            "text": text,
        })

        # Flush when batch is full
        if len(batch) >= 5:
            flush_batch(batch, conn)
            batch = []

        # Rate limit: 1 request per second for websites
        time.sleep(1)

    # Flush remaining
    flush_batch(batch, conn)

    client.close()
    conn.close()

    print(f"\nDone!")
    print(f"  Websites scraped: {stats['scraped']}")
    print(f"  Descriptions generated: {stats['described']}")
    print(f"  Irrelevant sites: {stats['irrelevant']}")
    print(f"  Empty/unreadable pages: {stats['empty_page']}")
    print(f"  Errors: {stats['errors']}")
    print(f"\nRun: python3 scripts/export.py --vertical {args.vertical}")


if __name__ == "__main__":
    main()
