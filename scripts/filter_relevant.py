#!/usr/bin/env python3
"""
Relevance filter for directory-factory listings.
Uses Claude Haiku to classify whether each listing actually belongs in the vertical.

Usage:
    python3 scripts/filter_relevant.py --vertical deposition-videographers
    python3 scripts/filter_relevant.py --vertical deposition-videographers --dry-run
"""

import argparse
import json
import os
import sqlite3
import time
from pathlib import Path

import httpx

PROJECT_ROOT = Path(__file__).parent.parent

BATCH_SIZE = 12  # 10-15 per batch, 12 is a good middle ground

CLASSIFICATION_PROMPT = """\
You are classifying businesses for a directory of deposition videographers and legal video services.

For each business below, determine if it is relevant to this directory.

RELEVANT (mark as true):
- Deposition videographers / legal videographers
- Legal video specialists (day-in-the-life videos, settlement documentaries)
- Court reporters or reporting firms that explicitly offer video services
- Litigation support companies that provide video deposition services
- Companies specializing in legal media / legal video production

NOT RELEVANT (mark as false):
- Wedding or event videographers
- General video production companies (corporate, commercial, music videos)
- Process servers or skip tracing
- Law firms or attorneys (they are clients, not providers)
- Private investigators or surveillance companies
- Real estate photography/media companies
- Court interpreters or translators (unless they also do video)
- IT / tech support companies
- Notary services (unless bundled with legal video)
- General court reporting firms with no mention of video

When in doubt, lean toward marking relevant — we can always remove later.

Here are the businesses to classify:

{listings_block}

Respond with ONLY a valid JSON array. No markdown, no explanation. Each element:
{{"name": "Business Name", "relevant": true/false, "reason": "brief reason"}}
"""


def get_db(vertical: str) -> sqlite3.Connection:
    db_path = PROJECT_ROOT / "verticals" / vertical / "pipeline.db"
    if not db_path.exists():
        print(f"Error: Database not found at {db_path}")
        raise SystemExit(1)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def ensure_column(conn: sqlite3.Connection):
    """Add is_relevant column if it doesn't exist."""
    cols = [row[1] for row in conn.execute("PRAGMA table_info(raw_listings)").fetchall()]
    if "is_relevant" not in cols:
        conn.execute("ALTER TABLE raw_listings ADD COLUMN is_relevant INTEGER DEFAULT 1")
        conn.commit()
        print("Added is_relevant column to raw_listings")


def get_unclassified(conn: sqlite3.Connection, vertical: str) -> list[sqlite3.Row]:
    """Get listings that haven't been through relevance classification."""
    return conn.execute("""
        SELECT id, name, city, state, address, phone, website, raw_data
        FROM raw_listings
        WHERE vertical = ?
          AND id NOT IN (
            SELECT listing_id FROM enrichment_log WHERE field = 'relevance_check'
          )
        ORDER BY id
    """, (vertical,)).fetchall()


def build_listing_block(listings: list[sqlite3.Row]) -> str:
    """Format listings for the prompt."""
    lines = []
    for i, row in enumerate(listings, 1):
        raw = json.loads(row["raw_data"]) if row["raw_data"] else {}
        desc = raw.get("description", "")
        services = raw.get("services", [])
        services_str = ", ".join(services) if services else ""

        parts = [f"{i}. {row['name']}"]
        if row["city"] or row["state"]:
            parts.append(f"   Location: {row['city'] or '?'}, {row['state'] or '?'}")
        if row["website"]:
            parts.append(f"   Website: {row['website']}")
        if desc:
            parts.append(f"   Description: {desc[:200]}")
        if services_str:
            parts.append(f"   Services: {services_str[:200]}")
        if row["address"]:
            parts.append(f"   Address: {row['address']}")

        lines.append("\n".join(parts))
    return "\n\n".join(lines)


def classify_batch(listings: list[sqlite3.Row], api_key: str) -> list[dict] | None:
    """Send a batch to Claude Haiku and parse the response."""
    block = build_listing_block(listings)
    prompt = CLASSIFICATION_PROMPT.format(listings_block=block)

    for attempt in range(3):
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
                    "max_tokens": 2048,
                    "messages": [{"role": "user", "content": prompt}],
                },
                timeout=60,
            )

            if resp.status_code == 429:
                retry_after = int(resp.headers.get("retry-after", 30))
                print(f"  Rate limited. Waiting {retry_after}s...")
                time.sleep(retry_after)
                continue

            if resp.status_code == 529:
                print(f"  API overloaded (529). Waiting 30s... (attempt {attempt + 1}/3)")
                time.sleep(30)
                continue

            resp.raise_for_status()
            raw_text = resp.json()["content"][0]["text"].strip()

            # Strip markdown code fences if present
            if raw_text.startswith("```"):
                raw_text = raw_text.split("\n", 1)[1].rsplit("```", 1)[0].strip()

            results = json.loads(raw_text)
            if not isinstance(results, list):
                print(f"  Warning: Expected JSON array, got {type(results).__name__}")
                return None
            return results

        except httpx.HTTPStatusError as e:
            print(f"  API error (HTTP {e.response.status_code}): {e}")
            if attempt < 2:
                time.sleep(5 * (attempt + 1))
                continue
            return None
        except json.JSONDecodeError as e:
            print(f"  JSON parse error: {e}")
            print(f"  Raw response: {raw_text[:300]}")
            return None
        except httpx.TimeoutException:
            print(f"  Request timed out (attempt {attempt + 1}/3)")
            if attempt < 2:
                time.sleep(5)
                continue
            return None
        except Exception as e:
            print(f"  Unexpected error: {e}")
            return None

    return None


def match_results(listings: list[sqlite3.Row], results: list[dict]) -> dict[int, dict]:
    """Match Claude's response back to listing IDs by name."""
    # Build name → result map (lowercase for fuzzy matching)
    result_map = {}
    for r in results:
        name_key = r.get("name", "").strip().lower()
        result_map[name_key] = r

    matched = {}
    for row in listings:
        name_lower = row["name"].strip().lower()
        # Try exact match first
        if name_lower in result_map:
            matched[row["id"]] = result_map[name_lower]
            continue
        # Try substring match
        for rname, rdata in result_map.items():
            if rname in name_lower or name_lower in rname:
                matched[row["id"]] = rdata
                break
        else:
            # No match found — skip, will be retried next run
            print(f"  Warning: No match for listing #{row['id']} '{row['name']}'")

    return matched


def main():
    parser = argparse.ArgumentParser(description="Filter off-topic listings using Claude")
    parser.add_argument("--vertical", required=True, help="Vertical slug")
    parser.add_argument("--dry-run", action="store_true", help="Classify but don't update the database")
    args = parser.parse_args()

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY environment variable is required")
        raise SystemExit(1)

    conn = get_db(args.vertical)
    ensure_column(conn)

    unclassified = get_unclassified(conn, args.vertical)
    total = len(unclassified)

    if total == 0:
        print("All listings have already been classified.")
        # Print current stats
        stats = conn.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN is_relevant = 1 THEN 1 ELSE 0 END) as relevant,
                SUM(CASE WHEN is_relevant = 0 THEN 1 ELSE 0 END) as irrelevant
            FROM raw_listings WHERE vertical = ?
        """, (args.vertical,)).fetchone()
        print(f"  Total: {stats['total']}  Relevant: {stats['relevant']}  Irrelevant: {stats['irrelevant']}")
        conn.close()
        return

    print(f"Found {total} unclassified listings for {args.vertical}")
    if args.dry_run:
        print("DRY RUN — no database changes will be made\n")

    # Process in batches
    batches = [unclassified[i:i + BATCH_SIZE] for i in range(0, total, BATCH_SIZE)]
    classified_relevant = 0
    classified_irrelevant = 0
    failed = 0

    for batch_idx, batch in enumerate(batches):
        print(f"\nBatch {batch_idx + 1}/{len(batches)} ({len(batch)} listings)")

        results = classify_batch(batch, api_key)
        if results is None:
            print(f"  FAILED — skipping batch")
            failed += len(batch)
            continue

        matched = match_results(batch, results)

        for listing_id, classification in matched.items():
            relevant = classification.get("relevant", True)
            reason = classification.get("reason", "")
            is_relevant = 1 if relevant else 0

            name = next(r["name"] for r in batch if r["id"] == listing_id)
            status = "RELEVANT" if relevant else "IRRELEVANT"
            print(f"  [{status}] {name}: {reason}")

            if not args.dry_run:
                conn.execute(
                    "UPDATE raw_listings SET is_relevant = ? WHERE id = ?",
                    (is_relevant, listing_id),
                )
                conn.execute("""
                    INSERT INTO enrichment_log (listing_id, field, value, source)
                    VALUES (?, 'relevance_check', ?, 'claude_haiku')
                """, (listing_id, json.dumps({"relevant": relevant, "reason": reason})))

            if relevant:
                classified_relevant += 1
            else:
                classified_irrelevant += 1

        # Count unmatched as failed
        unmatched = len(batch) - len(matched)
        failed += unmatched

        if not args.dry_run:
            conn.commit()

        # Small delay between batches to be polite to the API
        if batch_idx < len(batches) - 1:
            time.sleep(1)

    # Summary
    print("\n" + "=" * 50)
    print("CLASSIFICATION SUMMARY")
    print("=" * 50)
    print(f"  Processed:  {classified_relevant + classified_irrelevant}/{total}")
    print(f"  Relevant:   {classified_relevant}")
    print(f"  Irrelevant: {classified_irrelevant}")
    if failed:
        print(f"  Failed:     {failed} (will be retried on next run)")
    if args.dry_run:
        print("\n  DRY RUN — no changes were saved")

    # Overall stats
    if not args.dry_run:
        stats = conn.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN is_relevant = 1 THEN 1 ELSE 0 END) as relevant,
                SUM(CASE WHEN is_relevant = 0 THEN 1 ELSE 0 END) as irrelevant
            FROM raw_listings WHERE vertical = ?
        """, (args.vertical,)).fetchone()
        print(f"\n  Database totals — Total: {stats['total']}  Relevant: {stats['relevant']}  Irrelevant: {stats['irrelevant']}")

    conn.close()


if __name__ == "__main__":
    main()
