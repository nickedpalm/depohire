#!/usr/bin/env python3
"""
Clean up city assignments in pipeline.db — map messy Perplexity city names
to our cities.json slugs, and drop unmappable "statewide" entries into
the largest city for that state.
"""

import json
import sqlite3
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent


def main():
    vertical = sys.argv[1] if len(sys.argv) > 1 else "deposition-videographers"
    db_path = PROJECT_ROOT / "verticals" / vertical / "pipeline.db"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    # Load cities.json
    with open(PROJECT_ROOT / "template" / "src" / "data" / "cities.json") as f:
        cities = json.load(f)

    city_slugs = {c["slug"] for c in cities}
    city_by_name = {c["city"].lower(): c["slug"] for c in cities}

    # Largest city per state (fallback for "statewide" entries)
    biggest_by_state = {}
    for c in cities:
        if c["state"] not in biggest_by_state or c["population"] > biggest_by_state[c["state"]][1]:
            biggest_by_state[c["state"]] = (c["slug"], c["population"])

    # Manual mappings for common Perplexity quirks
    manual_map = {
        "new-york-city": "new-york",
        "new-yorknew-jersey": "new-york",
        "st-louis": "kansas-city",  # Closest in our cities.json for MO
        "st-petersburg": "tampa",
        "south-florida": "miami",
        "sarasota": "tampa",
        "cherry-hill": "philadelphia",  # South Jersey → Philly metro
        "southern-nj": "philadelphia",
        "monmouth-county": "new-york",
        "trenton": "philadelphia",
        "rockville": "washington-dc",
        "towson": "baltimore",
        "richmond": "virginia-beach",
        "northern-virginia-alexandria-area": "washington-dc",
        "kirkland": "seattle",
        "hillsboro": "portland",
        "chandler": "phoenix",
        "aurora": "denver",
        "ann-arbor": "detroit",
        "wayne": "detroit",
        "kenosha": "milwaukee",
        "columbia": "nashville",
        "dayton": "columbus",
        "arlington": "dallas",
        "kings-grant": "virginia-beach",
        "zebulon": "raleigh",
        "greensboro": "charlotte",
        "augusta": "atlanta",
        "burlington": "boston",
        "lake-charles": "new-orleans",
        "metairie": "new-orleans",
        "lafayette": "new-orleans",
        "livingston": "new-york",
        "atlantic-city": "philadelphia",
        "harrisburg": "pittsburgh",
        "new-jersey": "new-york",
        "statewide-nj": "new-york",
        "southern-new-england-serves-ma": "boston",
        "minnesota-and-western-wisconsin": "minneapolis",
        "williamsburgtidewaterhampton-roads-region": "virginia-beach",
        "wisconsin": "milwaukee",
        "wisconsin-statewide": "milwaukee",
        "wisconsin-statewide-including-green-bay": "milwaukee",
        "central-ohio": "columbus",
        "central-pa": "philadelphia",
        "central-texas": "austin",
        "madison": "milwaukee",
        "knoxville": "nashville",
    }

    rows = conn.execute("SELECT id, city, state FROM raw_listings").fetchall()
    fixed = 0

    for row in rows:
        city = row["city"]
        state = row["state"]
        new_city = None

        if city in city_slugs:
            continue  # Already good

        # Try manual map
        if city in manual_map:
            new_city = manual_map[city]
        # Try matching city name
        elif city and city.replace("-", " ") in city_by_name:
            new_city = city_by_name[city.replace("-", " ")]
        # Statewide / not-specified / junk → biggest city in state
        elif not city or "statewide" in (city or "") or "not-specified" in (city or "") or "nationwide" in (city or "") or "multiple" in (city or "") or "specific-city" in (city or ""):
            if state in biggest_by_state:
                new_city = biggest_by_state[state][0]

        if new_city and new_city != city:
            try:
                conn.execute("UPDATE raw_listings SET city = ? WHERE id = ?", (new_city, row["id"]))
                fixed += 1
            except sqlite3.IntegrityError:
                # Duplicate after remap — delete the duplicate
                conn.execute("DELETE FROM raw_listings WHERE id = ?", (row["id"],))
                fixed += 1

    conn.commit()
    print(f"Fixed {fixed}/{len(rows)} city assignments")

    # Show remaining unmapped
    unmapped = conn.execute("""
        SELECT DISTINCT city, state, COUNT(*) as cnt FROM raw_listings
        WHERE city NOT IN ({})
        GROUP BY city, state ORDER BY cnt DESC
    """.format(",".join(f"'{s}'" for s in city_slugs))).fetchall()

    if unmapped:
        print(f"\nStill unmapped ({len(unmapped)}):")
        for r in unmapped:
            print(f"  {r['city']} ({r['state']}) — {r['cnt']} listings")

    conn.close()


if __name__ == "__main__":
    main()
