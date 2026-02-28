#!/usr/bin/env python3
"""
Fetch hero images from Unsplash API and cache to verticals/<slug>/images.json.

Usage:
    python3 scripts/images.py --vertical deposition-videographers --city new-york
    python3 scripts/images.py --vertical deposition-videographers --topic what-does-a-deposition-videographer-do
    python3 scripts/images.py --vertical deposition-videographers --all-cities
    python3 scripts/images.py --vertical deposition-videographers --all-articles --config configs/deposition-videographers.yaml

Requires UNSPLASH_ACCESS_KEY environment variable.
Rate limit: 50 requests/hour (demo app).
"""

import argparse
import json
import os
import time
from pathlib import Path

import httpx

PROJECT_ROOT = Path(__file__).parent.parent
UNSPLASH_API = "https://api.unsplash.com"


def load_cache(vertical: str) -> dict:
    cache_path = PROJECT_ROOT / "verticals" / vertical / "images.json"
    if cache_path.exists():
        return json.load(open(cache_path))
    return {"cities": {}, "articles": {}}


def save_cache(vertical: str, cache: dict):
    cache_path = PROJECT_ROOT / "verticals" / vertical / "images.json"
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    with open(cache_path, "w") as f:
        json.dump(cache, f, indent=2)


def search_unsplash(query: str, access_key: str) -> dict | None:
    """Search Unsplash for a photo. Returns first result or None. Handles rate limits."""
    resp = httpx.get(
        f"{UNSPLASH_API}/search/photos",
        params={
            "query": query,
            "per_page": 1,
            "orientation": "landscape",
        },
        headers={"Authorization": f"Client-ID {access_key}"},
        timeout=30,
    )
    if resp.status_code == 403:
        remaining = resp.headers.get("X-Ratelimit-Remaining", "?")
        print(f"RATE LIMITED (remaining: {remaining}). Waiting 10min...", end=" ", flush=True)
        time.sleep(600)
        # Retry once
        resp = httpx.get(
            f"{UNSPLASH_API}/search/photos",
            params={"query": query, "per_page": 1, "orientation": "landscape"},
            headers={"Authorization": f"Client-ID {access_key}"},
            timeout=30,
        )
    resp.raise_for_status()
    data = resp.json()

    if not data.get("results"):
        return None

    photo = data["results"][0]

    # Trigger download endpoint per Unsplash API guidelines
    download_url = photo.get("links", {}).get("download_location")
    if download_url:
        try:
            httpx.get(
                download_url,
                params={"client_id": access_key},
                timeout=10,
            )
        except Exception:
            pass  # Non-critical — best effort

    return {
        "url": photo["urls"]["regular"],  # 1080w, good for hero
        "photographer": photo["user"]["name"],
        "photographer_url": photo["user"]["links"]["html"],
        "unsplash_url": photo["links"]["html"],
    }


def fetch_city_image(city_slug: str, city_name: str, access_key: str, cache: dict) -> bool:
    """Fetch image for a city. Returns True if new image fetched."""
    if city_slug in cache.get("cities", {}):
        print(f"  SKIP {city_slug} (cached)")
        return False

    query = f"{city_name} skyline"
    print(f"  Fetching {city_slug} ({query})...", end=" ", flush=True)

    result = search_unsplash(query, access_key)
    if result:
        cache.setdefault("cities", {})[city_slug] = result
        print(f"OK — {result['photographer']}")
        return True
    else:
        print("no results")
        return False


def fetch_article_image(topic_slug: str, title: str, access_key: str, cache: dict) -> bool:
    """Fetch image for a blog article. Returns True if new image fetched."""
    if topic_slug in cache.get("articles", {}):
        print(f"  SKIP {topic_slug} (cached)")
        return False

    # Extract meaningful keywords from title (drop common words)
    stop = {"a", "an", "the", "in", "of", "to", "and", "or", "is", "are", "how", "what",
            "does", "do", "when", "where", "why", "which", "you", "your", "it", "its",
            "that", "this", "for", "with", "on", "at", "by", "from", "as", "be", "will",
            "can", "should", "much", "vs", "actually", "really", "they", "them", "their"}
    words = [w.strip("(),:?!\"'") for w in title.lower().split()]
    keywords = [w for w in words if w and w not in stop and not w.isdigit()][:4]
    query = " ".join(keywords)

    print(f"  Fetching {topic_slug} ({query})...", end=" ", flush=True)

    result = search_unsplash(query, access_key)
    if result:
        cache.setdefault("articles", {})[topic_slug] = result
        print(f"OK — {result['photographer']}")
        return True
    else:
        print("no results")
        return False


def load_cities() -> list[dict]:
    cities_path = PROJECT_ROOT / "template" / "src" / "data" / "cities.json"
    with open(cities_path) as f:
        return json.load(f)


def get_article_topics(config_path: str) -> list[dict]:
    """Import and call generate_articles.get_article_topics()."""
    import sys
    sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
    import yaml
    with open(config_path) as f:
        config = yaml.safe_load(f)
    from generate_articles import get_article_topics
    return get_article_topics(config)


def main():
    parser = argparse.ArgumentParser(description="Fetch Unsplash images for directory verticals")
    parser.add_argument("--vertical", required=True, help="Vertical slug")
    parser.add_argument("--city", help="Fetch image for a specific city slug")
    parser.add_argument("--topic", help="Fetch image for a specific article slug")
    parser.add_argument("--all-cities", action="store_true", help="Fetch images for all cities")
    parser.add_argument("--all-articles", action="store_true", help="Fetch images for all articles")
    parser.add_argument("--config", help="Config YAML path (required for --all-articles or --topic)")
    args = parser.parse_args()

    access_key = os.environ.get("UNSPLASH_ACCESS_KEY")
    if not access_key:
        print("Error: UNSPLASH_ACCESS_KEY environment variable not set")
        raise SystemExit(1)

    cache = load_cache(args.vertical)
    fetched = 0

    if args.city:
        cities = load_cities()
        city = next((c for c in cities if c["slug"] == args.city), None)
        if not city:
            print(f"Error: city '{args.city}' not found in cities.json")
            raise SystemExit(1)
        if fetch_city_image(city["slug"], city["city"], access_key, cache):
            fetched += 1

    if args.all_cities:
        cities = load_cities()
        for city in cities:
            if fetch_city_image(city["slug"], city["city"], access_key, cache):
                fetched += 1
                save_cache(args.vertical, cache)
                time.sleep(75)  # Rate limit: 50/hr ≈ 1 per 72s

    if args.topic:
        if not args.config:
            print("Error: --config required for --topic")
            raise SystemExit(1)
        topics = get_article_topics(args.config)
        topic = next((t for t in topics if t["slug"] == args.topic), None)
        if not topic:
            print(f"Error: topic '{args.topic}' not found")
            raise SystemExit(1)
        if fetch_article_image(topic["slug"], topic["title"], access_key, cache):
            fetched += 1

    if args.all_articles:
        if not args.config:
            print("Error: --config required for --all-articles")
            raise SystemExit(1)
        topics = get_article_topics(args.config)
        for topic in topics:
            if fetch_article_image(topic["slug"], topic["title"], access_key, cache):
                fetched += 1
                save_cache(args.vertical, cache)
                time.sleep(75)  # Rate limit: 50/hr ≈ 1 per 72s

    save_cache(args.vertical, cache)
    print(f"\nDone. {fetched} new images fetched. Cache: verticals/{args.vertical}/images.json")


if __name__ == "__main__":
    main()
