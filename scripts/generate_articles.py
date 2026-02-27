#!/usr/bin/env python3
"""
Generate MDX blog articles using LLM (Anthropic Claude API).
Reads vertical config, outputs to src/content/blog/.

Usage:
    python3 scripts/generate_articles.py --config configs/deposition-videographers.yaml --vertical deposition-videographers

Requires ANTHROPIC_API_KEY environment variable.
"""

import argparse
import json
import os
import re
from datetime import datetime
from pathlib import Path

import httpx
import yaml

PROJECT_ROOT = Path(__file__).parent.parent

# Article topics per vertical — generated from config keywords
def get_article_topics(config: dict) -> list[dict]:
    keyword = config.get("primary_keyword", "professional")
    name = config["name"]
    industry = config.get("industry", "")
    certs = config.get("certifications", [])

    topics = [
        {
            "slug": f"what-does-a-{keyword.replace(' ', '-')}-do",
            "title": f"What Does a {keyword.title()} Do?",
            "prompt": f"Write a comprehensive guide explaining what a {keyword} does, their responsibilities, equipment used, and why they're important in {industry} settings.",
            "tags": [keyword, industry, "guide"],
        },
        {
            "slug": f"how-much-does-{keyword.replace(' ', '-')}-cost",
            "title": f"How Much Does {keyword.title().rstrip('s')} Services Cost?",
            "prompt": f"Write a pricing guide for {keyword} services. Include typical rate ranges, factors that affect pricing (duration, equipment, turnaround), and tips for getting quotes. Job value context: {config.get('job_value', '')}.",
            "tags": [keyword, "pricing", "guide"],
        },
        {
            "slug": f"how-to-choose-a-{keyword.replace(' ', '-')}",
            "title": f"How to Choose a {keyword.title()}: A Complete Guide",
            "prompt": f"Write a guide helping people choose the right {keyword}. Cover qualifications, certifications ({', '.join(certs)}), questions to ask, red flags, and what to look for.",
            "tags": [keyword, "guide", "tips"],
        },
    ]

    # Add certification article if applicable
    if certs:
        cert = certs[0]
        cert_slug = re.sub(r'[^\w]+', '-', cert.lower()).strip('-')
        topics.append({
            "slug": f"{cert_slug}-certification-guide",
            "title": f"{cert} Certification: What You Should Know",
            "prompt": f"Write a guide about the {cert} certification. Explain what it is, who issues it, requirements, benefits for professionals and clients, and why it matters when hiring a {keyword}.",
            "tags": [keyword, "certification", cert_slug],
        })

    return topics


def generate_article(topic: dict, config: dict, api_key: str) -> str:
    """Generate article content using Claude API."""
    context = config.get("city_page_prompt_context", "")

    prompt = f"""{topic['prompt']}

Industry context:
{context}

Write a professional blog article with:
- An engaging introduction (2-3 sentences)
- 3-5 H2 sections with substantive content
- Practical advice and specific details
- A brief conclusion

Target length: 800-1200 words. Professional tone, factual, SEO-friendly.
Do NOT include frontmatter. Start directly with the introduction paragraph.
Do NOT include the title as an H1 — it's handled by the layout."""

    resp = httpx.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": "claude-haiku-4-5-20251001",
            "max_tokens": 3000,
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=90,
    )
    resp.raise_for_status()
    return resp.json()["content"][0]["text"]


def build_frontmatter(topic: dict, config: dict) -> str:
    today = datetime.now().strftime("%Y-%m-%d")
    keyword = config.get("primary_keyword", "professional")
    return f"""---
title: "{topic['title']}"
description: "{topic['prompt'][:150].rstrip('.')}."
pubDate: {today}
author: "Editorial Team"
tags: {json.dumps(topic['tags'])}
---

"""


def main():
    parser = argparse.ArgumentParser(description="Generate blog articles via LLM")
    parser.add_argument("--config", required=True, help="Path to vertical YAML config")
    parser.add_argument("--vertical", required=True, help="Vertical slug")
    parser.add_argument("--topic", help="Specific topic slug (default: all)")
    parser.add_argument("--dry-run", action="store_true", help="Print output instead of writing")
    args = parser.parse_args()

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY environment variable not set")
        raise SystemExit(1)

    config = load_config(args.config)
    topics = get_article_topics(config)
    output_dir = PROJECT_ROOT / "verticals" / args.vertical / "src" / "content" / "blog"
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.topic:
        topics = [t for t in topics if t["slug"] == args.topic]

    print(f"Generating {len(topics)} articles for {config['name']}")

    for topic in topics:
        output_file = output_dir / f"{topic['slug']}.mdx"

        if output_file.exists() and not args.dry_run:
            print(f"  SKIP {topic['title']} (already exists)")
            continue

        print(f"  Generating: {topic['title']}...", end=" ", flush=True)

        try:
            body = generate_article(topic, config, api_key)
            frontmatter = build_frontmatter(topic, config)
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

    print(f"\nArticles written to {output_dir}")


def load_config(config_path: str) -> dict:
    with open(config_path) as f:
        return yaml.safe_load(f)


if __name__ == "__main__":
    main()
