#!/usr/bin/env python3
"""
Generate MDX city landing pages using LLM (Anthropic Claude API).
Reads vertical config + cities.json + voice guide, outputs to src/content/cities/.

Usage:
    python3 scripts/generate_cities.py --config configs/deposition-videographers.yaml --vertical deposition-videographers [--city new-york]

Requires ANTHROPIC_API_KEY environment variable.
"""

import argparse
import json
import os
from pathlib import Path

import httpx
import yaml

PROJECT_ROOT = Path(__file__).parent.parent


def load_config(config_path: str) -> dict:
    with open(config_path) as f:
        return yaml.safe_load(f)


def load_voice_guide() -> str:
    guide_path = PROJECT_ROOT / "configs" / "voice-guide.md"
    if guide_path.exists():
        return guide_path.read_text()
    return ""


def load_cities(city_filter: str | None = None) -> list[dict]:
    cities_path = PROJECT_ROOT / "template" / "src" / "data" / "cities.json"
    with open(cities_path) as f:
        cities = json.load(f)
    if city_filter:
        cities = [c for c in cities if c["slug"] == city_filter]
    return cities


def generate_city_page(config: dict, city: dict, api_key: str, voice_guide: str) -> str:
    """Generate MDX content for a city page using Claude API."""
    keyword = config.get("primary_keyword", "professional")
    keyword_title = keyword.title()

    prompt = f"""You are writing a city landing page for a {config['name']} directory.
The page is for {city['city']}, {city['stateName']} (population: {city['population']:,}).

Business context:
{config.get('city_page_prompt_context', '')}

Primary keyword: {keyword}
Job value: {config.get('job_value', '')}
Certifications: {', '.join(config.get('certifications', []))}

## VOICE & STYLE GUIDE
{voice_guide[:3000]}

## STORYBRAND FRAMING
The reader is the HERO — they're an attorney, project manager, or business owner who needs to find a qualified {keyword} in {city['city']}. This directory is the GUIDE. Frame the content around their problem (finding someone qualified, fast, without getting burned), present the directory as the solution, and give them a clear plan of action.

## STRUCTURE (NO frontmatter — just body content):

1. **Opening paragraph** (2-3 sentences): Lead with the reader's problem — hiring a {keyword} in {city['city']} is harder than it should be. Position the directory as the guide. Use a specific, vivid detail about the local market.

2. **"## How to Choose a {keyword_title} in {city['city']}"** — 4-5 bullet points of actionable advice. Be specific to {city['city']}/{city['stateName']}. Include a "Pro Tip" callout.

3. **"## What to Expect"** — Pricing context ({config.get('job_value', '')}), process overview, turnaround. 2-3 sentences. Include a "Reality Check" callout about common pricing mistakes.

4. **"## Local Market Overview"** — 1-2 sentences about {city['city']}'s legal/business market relevant to this service. Reference something specific about the city.

Keep it practical, confident, and slightly irreverent per the voice guide. Around 500-700 words total.
Do NOT include any frontmatter or YAML headers. Start directly with the content paragraph.
Do NOT use phrases like "In this article" or "Let's dive in" or "Without further ado"."""

    resp = httpx.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": "claude-haiku-4-5-20251001",
            "max_tokens": 2000,
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=90,
    )
    resp.raise_for_status()
    return resp.json()["content"][0]["text"]


def load_images(vertical: str) -> dict:
    images_path = PROJECT_ROOT / "verticals" / vertical / "images.json"
    if images_path.exists():
        return json.load(open(images_path))
    return {"cities": {}, "articles": {}}


def build_frontmatter(config: dict, city: dict, images: dict | None = None) -> str:
    keyword = config.get("primary_keyword", "professional")
    year = __import__("datetime").datetime.now().year

    image_lines = ""
    if images:
        city_images = images.get("cities", {})
        img = city_images.get(city["slug"])
        if img:
            image_lines = f'image: "{img["url"]}"\nimageCredit: "Photo by [{img["photographer"]}]({img["photographer_url"]}) on [Unsplash]({img["unsplash_url"]})"\n'

    return f"""---
title: "Best {config['name']} in {city['city']}, {city['state']} ({year})"
city: "{city['city']}"
state: "{city['state']}"
stateSlug: "{city['stateSlug']}"
slug: "{city['slug']}"
metaDescription: "Find the best {keyword}s in {city['city']}, {city['state']}. Compare verified professionals, read real reviews, and request quotes. Updated {year}."
population: {city['population']}
{image_lines}---

"""


def main():
    parser = argparse.ArgumentParser(description="Generate MDX city landing pages via LLM")
    parser.add_argument("--config", required=True, help="Path to vertical YAML config")
    parser.add_argument("--vertical", required=True, help="Vertical slug")
    parser.add_argument("--city", help="Specific city slug (default: all)")
    parser.add_argument("--dry-run", action="store_true", help="Print output instead of writing files")
    parser.add_argument("--force", action="store_true", help="Overwrite existing files")
    args = parser.parse_args()

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY environment variable not set")
        raise SystemExit(1)

    config = load_config(args.config)
    voice_guide = load_voice_guide()
    cities = load_cities(args.city)
    images = load_images(args.vertical)
    output_dir = PROJECT_ROOT / "verticals" / args.vertical / "src" / "content" / "cities"
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Generating city pages for {config['name']} — {len(cities)} cities")

    for city in cities:
        output_file = output_dir / f"{city['slug']}.mdx"

        if output_file.exists() and not args.force and not args.dry_run:
            print(f"  SKIP {city['city']}, {city['state']} (already exists, use --force)")
            continue

        print(f"  Generating {city['city']}, {city['state']}...", end=" ", flush=True)

        try:
            body = generate_city_page(config, city, api_key, voice_guide)
            frontmatter = build_frontmatter(config, city, images)
            content = frontmatter + body

            if args.dry_run:
                print()
                print(content[:500])
                print("...")
            else:
                with open(output_file, "w") as f:
                    f.write(content)
                print("OK")

        except Exception as e:
            print(f"ERROR: {e}")

    print(f"\nCity pages written to {output_dir}")


if __name__ == "__main__":
    main()
