#!/usr/bin/env python3
"""
Generate MDX city landing pages using LLM (Anthropic Claude API).
Reads vertical config + cities.json, outputs to src/content/cities/.

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


def load_cities(city_filter: str | None = None) -> list[dict]:
    cities_path = PROJECT_ROOT / "template" / "src" / "data" / "cities.json"
    with open(cities_path) as f:
        cities = json.load(f)
    if city_filter:
        cities = [c for c in cities if c["slug"] == city_filter]
    return cities


def generate_city_page(config: dict, city: dict, api_key: str) -> str:
    """Generate MDX content for a city page using Claude API."""
    prompt = f"""Write a city landing page for a {config['name']} directory.
The page is for {city['city']}, {city['stateName']} (population: {city['population']:,}).

Business context:
{config.get('city_page_prompt_context', '')}

Primary keyword: {config.get('primary_keyword', '')}
Job value: {config.get('job_value', '')}

Write in this structure (NO frontmatter — just the body content):
1. Opening paragraph about the city's relevant legal/business market (2-3 sentences)
2. "## How to Choose a {config.get('primary_keyword', 'professional').title()} in {city['city']}" — 4-5 bullet points
3. "## What to Expect" — pricing, process, 2-3 sentences
4. "## Frequently Asked Questions" — 2-3 Q&A pairs using bold question format

Keep it factual, professional, and SEO-friendly. Around 400-500 words total.
Do NOT include any frontmatter or YAML headers. Start directly with the content paragraph."""

    resp = httpx.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": "claude-haiku-4-5-20251001",
            "max_tokens": 1500,
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()["content"][0]["text"]


def build_frontmatter(config: dict, city: dict) -> str:
    keyword = config.get("primary_keyword", "professional")
    return f"""---
title: "{config['name']} in {city['city']}, {city['state']}"
city: "{city['city']}"
state: "{city['state']}"
stateSlug: "{city['stateSlug']}"
slug: "{city['slug']}"
metaDescription: "Find the best {keyword}s in {city['city']}, {city['state']}. Compare certified professionals, read reviews, and request quotes."
population: {city['population']}
---

"""


def main():
    parser = argparse.ArgumentParser(description="Generate MDX city landing pages via LLM")
    parser.add_argument("--config", required=True, help="Path to vertical YAML config")
    parser.add_argument("--vertical", required=True, help="Vertical slug")
    parser.add_argument("--city", help="Specific city slug (default: all)")
    parser.add_argument("--dry-run", action="store_true", help="Print output instead of writing files")
    args = parser.parse_args()

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY environment variable not set")
        raise SystemExit(1)

    config = load_config(args.config)
    cities = load_cities(args.city)
    output_dir = PROJECT_ROOT / "verticals" / args.vertical / "src" / "content" / "cities"
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Generating city pages for {config['name']} — {len(cities)} cities")

    for city in cities:
        output_file = output_dir / f"{city['slug']}.mdx"

        if output_file.exists() and not args.dry_run:
            print(f"  SKIP {city['city']}, {city['state']} (already exists)")
            continue

        print(f"  Generating {city['city']}, {city['state']}...", end=" ", flush=True)

        try:
            body = generate_city_page(config, city, api_key)
            frontmatter = build_frontmatter(config, city)
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
