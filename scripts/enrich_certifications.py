#!/usr/bin/env python3
"""
Enrich listings with certifications, equipment, coverage area, and years of experience
by scraping company websites and extracting structured data via Claude Haiku.

Usage:
    python3 scripts/enrich_certifications.py --vertical deposition-videographers [--dry-run] [--limit N]
"""

import argparse
import json
import os
import sqlite3
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import httpx

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("Install BeautifulSoup: pip install beautifulsoup4")
    raise SystemExit(1)

PROJECT_ROOT = Path(__file__).parent.parent
CURRENT_YEAR = 2026

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml",
}

# Pages likely to contain certification/equipment/experience info
SCRAPE_PATHS = ["/", "/about", "/about-us", "/services", "/our-services"]

MAX_TEXT_CHARS = 3000


def get_db(vertical: str) -> sqlite3.Connection:
    db_path = PROJECT_ROOT / "verticals" / vertical / "pipeline.db"
    if not db_path.exists():
        print(f"Error: Database not found at {db_path}")
        print("Run scrape.py first.")
        raise SystemExit(1)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def ensure_columns(conn: sqlite3.Connection):
    """Add certification-related columns to raw_listings if they don't exist."""
    existing = {row[1] for row in conn.execute("PRAGMA table_info(raw_listings)").fetchall()}
    columns = {
        "certifications": "TEXT",
        "equipment": "TEXT",
        "coverage_area": "TEXT",
        "years_experience": "INTEGER",
    }
    for col, dtype in columns.items():
        if col not in existing:
            conn.execute(f"ALTER TABLE raw_listings ADD COLUMN {col} {dtype}")
            print(f"  Added column: {col} ({dtype})")
    conn.commit()


def log_enrichment(conn: sqlite3.Connection, listing_id: int, field: str, value: str, source: str):
    conn.execute("""
        INSERT INTO enrichment_log (listing_id, field, value, source)
        VALUES (?, ?, ?, ?)
    """, (listing_id, field, value, source))


def get_already_enriched(conn: sqlite3.Connection) -> set[int]:
    """Return listing IDs that already have certification enrichment logged."""
    rows = conn.execute("""
        SELECT DISTINCT listing_id FROM enrichment_log
        WHERE field = 'certifications'
    """).fetchall()
    return {row[0] for row in rows}


def fetch_page(url: str, client: httpx.Client) -> str | None:
    """Fetch a single page, return text content or None."""
    try:
        resp = client.get(url, follow_redirects=True, timeout=5)
        if resp.status_code == 200 and "text/html" in resp.headers.get("content-type", ""):
            return resp.text
    except Exception:
        pass
    return None


def extract_text(html: str) -> str:
    """Extract visible text from HTML, stripping nav/footer/script noise."""
    soup = BeautifulSoup(html, "html.parser")
    # Remove noisy elements
    for tag in soup.find_all(["script", "style", "nav", "footer", "header", "noscript", "iframe"]):
        tag.decompose()
    text = soup.get_text(separator=" ", strip=True)
    # Collapse whitespace
    text = " ".join(text.split())
    return text


def scrape_website_text(website: str, client: httpx.Client) -> str:
    """Fetch homepage + /about + /services pages and combine text."""
    parsed = urlparse(website)
    base = f"{parsed.scheme}://{parsed.netloc}"
    all_text = []
    seen_paths = set()

    for path in SCRAPE_PATHS:
        url = base.rstrip("/") + path
        # Avoid fetching duplicate URLs (homepage might redirect to /about etc.)
        if url in seen_paths:
            continue
        seen_paths.add(url)

        html = fetch_page(url, client)
        if html:
            text = extract_text(html)
            if text:
                all_text.append(text)

        time.sleep(1)  # 1 req/sec rate limit

    combined = " ".join(all_text)
    # Truncate to ~MAX_TEXT_CHARS
    if len(combined) > MAX_TEXT_CHARS:
        combined = combined[:MAX_TEXT_CHARS] + "..."
    return combined


def call_claude(texts: list[dict], api_key: str) -> list[dict | None]:
    """Send a batch of extraction requests to Claude Haiku.

    Each item in `texts` is {"listing_id": int, "name": str, "text": str}.
    Returns list of parsed JSON results (or None for failures), same order.
    """
    results = []
    for item in texts:
        prompt = f"""Extract the following from this deposition videography company's website. Return JSON only, no markdown fences:
{{
  "certifications": ["CLVS", "NCRA member", etc] or [],
  "equipment": ["Sony FX6", "4K cameras", etc] or [],
  "coverage_area": "description of service area" or null,
  "years_experience": number or null,
  "founded_year": number or null
}}

Only include information explicitly stated on the website. Do not guess.

Company: {item['name']}

Website text:
{item['text']}"""

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
                    "max_tokens": 500,
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
            results.append(result)
        except Exception as e:
            print(f"    Claude error for {item['name']}: {e}")
            results.append(None)

        time.sleep(0.5)  # Rate limit between Claude calls

    return results


def main():
    parser = argparse.ArgumentParser(description="Enrich listings with certifications, equipment, coverage area, experience")
    parser.add_argument("--vertical", required=True, help="Vertical slug")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be enriched, don't write")
    parser.add_argument("--limit", type=int, default=0, help="Limit number of listings to process")
    args = parser.parse_args()

    api_key = os.environ.get("ANTHROPIC_API_KEY")

    conn = get_db(args.vertical)
    ensure_columns(conn)

    # Get listings with websites that haven't been enriched for certifications
    already_enriched = get_already_enriched(conn)

    rows = conn.execute("""
        SELECT id, name, city, state, website
        FROM raw_listings
        WHERE vertical = ?
          AND website IS NOT NULL AND website != ''
        ORDER BY city, name
    """, (args.vertical,)).fetchall()

    candidates = [r for r in rows if r["id"] not in already_enriched]

    print(f"Total listings with websites: {len(rows)}")
    print(f"Already enriched: {len(already_enriched)}")
    print(f"To enrich: {len(candidates)}")

    if args.dry_run:
        print("\nDry run -- no changes made.")
        for r in candidates[:20]:
            print(f"  {r['name']} ({r['city']}, {r['state']}) - {r['website']}")
        if len(candidates) > 20:
            print(f"  ... and {len(candidates) - 20} more")
        conn.close()
        return

    if not api_key:
        print("Error: ANTHROPIC_API_KEY env var required")
        raise SystemExit(1)

    if not candidates:
        print("\nNothing to enrich.")
        conn.close()
        return

    if args.limit:
        candidates = candidates[: args.limit]
        print(f"\nLimited to {args.limit} listings")

    stats = {
        "scraped": 0,
        "enriched": 0,
        "certifications": 0,
        "equipment": 0,
        "coverage_area": 0,
        "years_experience": 0,
        "scrape_errors": 0,
        "claude_errors": 0,
    }

    client = httpx.Client(headers=HEADERS, follow_redirects=True)

    print(f"\nProcessing {len(candidates)} listings...\n")

    for i, row in enumerate(candidates):
        listing_id = row["id"]
        name = row["name"]
        website = row["website"]

        print(f"[{i + 1}/{len(candidates)}] {name} ({row['city']}, {row['state']})")

        # Step 1: Scrape website text
        try:
            text = scrape_website_text(website, client)
            stats["scraped"] += 1
        except Exception as e:
            print(f"  Scrape error: {e}")
            stats["scrape_errors"] += 1
            continue

        if not text or len(text.strip()) < 50:
            print("  Insufficient text scraped, skipping")
            continue

        # Step 2: Claude extraction
        results = call_claude([{"listing_id": listing_id, "name": name, "text": text}], api_key)
        result = results[0] if results else None

        if result is None:
            stats["claude_errors"] += 1
            continue

        # Step 3: Compute years_experience from founded_year if needed
        years_exp = result.get("years_experience")
        founded_year = result.get("founded_year")
        if years_exp is None and founded_year is not None:
            try:
                founded_year = int(founded_year)
                if 1900 < founded_year <= CURRENT_YEAR:
                    years_exp = CURRENT_YEAR - founded_year
            except (ValueError, TypeError):
                pass

        # Step 4: Update database
        certs = result.get("certifications", [])
        equip = result.get("equipment", [])
        coverage = result.get("coverage_area")

        updates = []
        params = []

        if certs:
            certs_json = json.dumps(certs)
            updates.append("certifications = ?")
            params.append(certs_json)
            log_enrichment(conn, listing_id, "certifications", certs_json, "website_claude")
            stats["certifications"] += 1
            print(f"  Certifications: {', '.join(certs)}")
        else:
            # Log empty so we don't re-process
            log_enrichment(conn, listing_id, "certifications", "[]", "website_claude")

        if equip:
            equip_json = json.dumps(equip)
            updates.append("equipment = ?")
            params.append(equip_json)
            log_enrichment(conn, listing_id, "equipment", equip_json, "website_claude")
            stats["equipment"] += 1
            print(f"  Equipment: {', '.join(equip)}")

        if coverage:
            updates.append("coverage_area = ?")
            params.append(coverage)
            log_enrichment(conn, listing_id, "coverage_area", coverage, "website_claude")
            stats["coverage_area"] += 1
            print(f"  Coverage: {coverage}")

        if years_exp is not None:
            try:
                years_exp = int(years_exp)
                if 0 < years_exp < 200:
                    updates.append("years_experience = ?")
                    params.append(years_exp)
                    source_note = f"website_claude (founded {founded_year})" if founded_year else "website_claude"
                    log_enrichment(conn, listing_id, "years_experience", str(years_exp), source_note)
                    stats["years_experience"] += 1
                    print(f"  Experience: {years_exp} years")
            except (ValueError, TypeError):
                pass

        if updates:
            params.append(listing_id)
            conn.execute(f"UPDATE raw_listings SET {', '.join(updates)} WHERE id = ?", params)
            stats["enriched"] += 1

        # Commit every 10 listings
        if (i + 1) % 10 == 0:
            conn.commit()

    client.close()
    conn.commit()
    conn.close()

    # Summary
    print(f"\n{'=' * 50}")
    print(f"Enrichment complete!")
    print(f"  Websites scraped: {stats['scraped']}")
    print(f"  Listings enriched: {stats['enriched']}")
    print(f"  With certifications: {stats['certifications']}")
    print(f"  With equipment: {stats['equipment']}")
    print(f"  With coverage area: {stats['coverage_area']}")
    print(f"  With years experience: {stats['years_experience']}")
    print(f"  Scrape errors: {stats['scrape_errors']}")
    print(f"  Claude errors: {stats['claude_errors']}")
    print(f"\nRun: python3 scripts/export.py --vertical {args.vertical}")


if __name__ == "__main__":
    main()
