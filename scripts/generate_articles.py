#!/usr/bin/env python3
"""
Generate MDX blog articles using a two-step pipeline:
1. Research via Perplexity API (real data, current info, saved to research/)
2. Write via Claude API (voice guide, StoryBrand, authority-site framework)

Outputs hub/spoke content to src/content/blog/.

Usage:
    python3 scripts/generate_articles.py --config configs/deposition-videographers.yaml --vertical deposition-videographers
    python3 scripts/generate_articles.py --config configs/deposition-videographers.yaml --vertical deposition-videographers --research-only
    python3 scripts/generate_articles.py --config configs/deposition-videographers.yaml --vertical deposition-videographers --topic specific-slug

Requires: PERPLEXITY_API_KEY and ANTHROPIC_API_KEY environment variables.
"""

import argparse
import json
import os
import re
import time
from datetime import datetime
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


# ── TOPIC DEFINITIONS ────────────────────────────────────────────────────
# 30 high-value SEO articles organized in hub/spoke clusters
# following the authority-site-expert framework

def get_article_topics(config: dict) -> list[dict]:
    keyword = config.get("primary_keyword", "professional")
    kw = keyword  # shorthand
    name = config["name"]
    industry = config.get("industry", "")
    certs = config.get("certifications", [])
    job_value = config.get("job_value", "")
    cert = certs[0] if certs else "professional certification"
    cert_slug = re.sub(r'[^\w]+', '-', cert.lower()).strip('-')

    # Hub page slug for cross-linking
    hub_slug = f"complete-guide-{kw.replace(' ', '-')}s"
    hub_title = f"The Complete Guide to {kw.title()}s"

    topics = [
        # ── CLUSTER 1: PILLAR / HUB ──────────────────────────────────
        {
            "slug": hub_slug,
            "title": hub_title,
            "hub": None,
            "is_hub": True,
            "cluster": "pillar",
            "search_intent": "informational",
            "research_query": f"comprehensive guide to {kw} services industry overview pricing certifications regulations",
            "prompt": f"Write the DEFINITIVE pillar guide about {kw}s. This is the hub page — it should be 2000+ words, touching every major subtopic and linking to spoke articles. Include: what they do, how to hire, pricing ranges, certifications, state regulations, equipment, and future trends. Include a comparison table of service types.",
            "tags": [kw, "guide", "pillar"],
        },

        # ── CLUSTER 2: HIRING / CHOOSING (commercial intent) ─────────
        {
            "slug": f"how-to-choose-a-{kw.replace(' ', '-')}",
            "title": f"How to Choose a {kw.title()}: What Nobody Tells You",
            "hub": hub_title, "is_hub": False, "cluster": "hiring",
            "search_intent": "commercial",
            "research_query": f"how to choose best {kw} what to look for qualifications questions to ask red flags",
            "prompt": f"Write a guide helping people choose the right {kw}. Include questions to ask (numbered list for featured snippet), red flags, qualifications that matter, and a comparison of certified vs uncertified providers.",
            "tags": [kw, "guide", "tips"],
        },
        {
            "slug": f"questions-to-ask-before-hiring-a-{kw.replace(' ', '-')}",
            "title": f"15 Questions to Ask Before Hiring a {kw.title()}",
            "hub": hub_title, "is_hub": False, "cluster": "hiring",
            "search_intent": "commercial",
            "research_query": f"questions to ask {kw} before hiring interview checklist",
            "prompt": f"Write a numbered list article: 15 critical questions to ask a {kw} before hiring them. Each question should have 2-3 sentences explaining why it matters and what a good answer looks like. Featured snippet bait format.",
            "tags": [kw, "hiring", "checklist"],
        },
        {
            "slug": f"red-flags-when-hiring-a-{kw.replace(' ', '-')}",
            "title": f"7 Red Flags When Hiring a {kw.title()} (And How to Avoid Them)",
            "hub": hub_title, "is_hub": False, "cluster": "hiring",
            "search_intent": "commercial",
            "research_query": f"problems with {kw} bad experience what went wrong complaints common issues",
            "prompt": f"Write about the 7 biggest red flags when hiring a {kw}. Real-world examples of what goes wrong. Each red flag gets its own section with: what it looks like, why it matters, and how to avoid it.",
            "tags": [kw, "hiring", "warnings"],
        },

        # ── CLUSTER 3: PRICING (commercial intent — money keywords) ──
        {
            "slug": f"how-much-does-{kw.replace(' ', '-')}-cost",
            "title": f"How Much Does a {kw.title()} Cost? ({datetime.now().year} Pricing Guide)",
            "hub": hub_title, "is_hub": False, "cluster": "pricing",
            "search_intent": "commercial",
            "research_query": f"{kw} cost pricing rates per hour per day 2026 how much average",
            "prompt": f"Write a definitive pricing guide for {kw} services. Include: a comparison table (service tier | cost range | what's included), factors affecting price, regional differences, hidden fees, how to negotiate. Real data. Job value context: {job_value}.",
            "tags": [kw, "pricing", "guide"],
        },
        {
            "slug": f"{kw.replace(' ', '-')}-cost-by-state",
            "title": f"{kw.title()} Costs by State: Where You'll Pay More (And Less)",
            "hub": hub_title, "is_hub": False, "cluster": "pricing",
            "search_intent": "commercial",
            "research_query": f"{kw} rates by state regional pricing differences cost of living impact",
            "prompt": f"Write about how {kw} pricing varies by state/region. Include a table of approximate rates for major markets. Explain why costs differ (cost of living, competition, regulation). Pro Tip about finding value in less expensive markets.",
            "tags": [kw, "pricing", "states"],
        },
        {
            "slug": f"are-cheap-{kw.replace(' ', '-')}s-worth-it",
            "title": f"Are Cheap {kw.title()}s Worth It? The Real Cost of Cutting Corners",
            "hub": hub_title, "is_hub": False, "cluster": "pricing",
            "search_intent": "commercial",
            "research_query": f"cheap {kw} vs expensive quality difference what happens when you go cheap risks",
            "prompt": f"Anti-hype article about whether budget {kw}s deliver. Be honest — sometimes the cheaper option is fine, sometimes it's a disaster. Include real examples of what goes wrong when you prioritize price over quality.",
            "tags": [kw, "pricing", "quality"],
        },

        # ── CLUSTER 4: CERTIFICATION / CREDENTIALS ───────────────────
        {
            "slug": f"{cert_slug}-certification-guide",
            "title": f"{cert} Certification: Why It Matters (And When It Doesn't)",
            "hub": hub_title, "is_hub": False, "cluster": "certification",
            "search_intent": "informational",
            "research_query": f"{cert} certification requirements how to get what does it mean benefits",
            "prompt": f"Honest guide to the {cert} certification. When it matters, when it's overkill. Requirements, cost, who issues it. Anti-hype framing — certification alone doesn't guarantee quality.",
            "tags": [kw, "certification", cert_slug],
        },
        {
            "slug": f"certified-vs-uncertified-{kw.replace(' ', '-')}",
            "title": f"Certified vs. Uncertified {kw.title()}s: Does the Credential Matter?",
            "hub": hub_title, "is_hub": False, "cluster": "certification",
            "search_intent": "informational",
            "research_query": f"certified vs uncertified {kw} difference does certification matter quality comparison",
            "prompt": f"Direct comparison: certified vs uncertified {kw}s. Include a comparison table. When certification is essential (complex cases), when experience trumps credentials. Real talk, not sales pitch.",
            "tags": [kw, "certification", "comparison"],
        },

        # ── CLUSTER 5: PROCESS / WHAT TO EXPECT ──────────────────────
        {
            "slug": f"what-does-a-{kw.replace(' ', '-')}-do",
            "title": f"What Does a {kw.title()} Actually Do? (Behind the Scenes)",
            "hub": hub_title, "is_hub": False, "cluster": "process",
            "search_intent": "informational",
            "research_query": f"what does a {kw} do job description responsibilities day in the life process workflow",
            "prompt": f"Detailed explainer of what a {kw} actually does. Walk through a typical engagement from booking to delivery. Equipment used, technical requirements, common challenges. Write it like you're explaining to someone who's never hired one.",
            "tags": [kw, industry, "guide"],
        },
        {
            "slug": f"what-to-expect-hiring-a-{kw.replace(' ', '-')}",
            "title": f"What to Expect When You Hire a {kw.title()} (Step by Step)",
            "hub": hub_title, "is_hub": False, "cluster": "process",
            "search_intent": "informational",
            "research_query": f"hiring {kw} process timeline what happens step by step from booking to delivery",
            "prompt": f"Step-by-step walkthrough of the hiring process. From initial call to final deliverables. Timeline expectations, what you need to provide, typical turnaround times. Numbered list format for featured snippet.",
            "tags": [kw, "process", "guide"],
        },
        {
            "slug": f"{kw.replace(' ', '-')}-equipment-explained",
            "title": f"{kw.title()} Equipment: What Matters and What's Marketing",
            "hub": hub_title, "is_hub": False, "cluster": "process",
            "search_intent": "informational",
            "research_query": f"{kw} equipment technology tools cameras software what equipment do they use best",
            "prompt": f"Equipment deep-dive for {kw}s. What actually matters for quality (with specific gear names and specs), what's just marketing fluff. Include comparison table. Anti-hype: expensive gear doesn't fix bad technique.",
            "tags": [kw, "equipment", "technology"],
        },

        # ── CLUSTER 6: LEGAL / COMPLIANCE ─────────────────────────────
        {
            "slug": f"{kw.replace(' ', '-')}-legal-requirements",
            "title": f"{kw.title()} Legal Requirements: What the Rules Actually Say",
            "hub": hub_title, "is_hub": False, "cluster": "legal",
            "search_intent": "informational",
            "research_query": f"{kw} legal requirements regulations state laws rules compliance court admissibility",
            "prompt": f"Guide to legal requirements for {kw} services. State-by-state variations, court rules, admissibility standards. Include 'Important' callouts for critical compliance items. Table of key requirements by state.",
            "tags": [kw, "legal", "compliance"],
        },
        {
            "slug": f"can-a-{kw.replace(' ', '-')}-testify-in-court",
            "title": f"Can a {kw.title()} Testify in Court? (What Attorneys Need to Know)",
            "hub": hub_title, "is_hub": False, "cluster": "legal",
            "search_intent": "informational",
            "research_query": f"{kw} court testimony expert witness role authentication deposition video admissibility rules",
            "prompt": f"Detailed legal analysis of when and how a {kw} might testify in court. Authentication requirements, chain of custody, what courts require. Include case examples where video was challenged.",
            "tags": [kw, "legal", "court"],
        },

        # ── CLUSTER 7: INDUSTRY TRENDS / DATA ────────────────────────
        {
            "slug": f"{kw.replace(' ', '-')}-industry-trends",
            "title": f"{kw.title()} Industry Trends: What's Changing in {datetime.now().year}",
            "hub": hub_title, "is_hub": False, "cluster": "trends",
            "search_intent": "informational",
            "research_query": f"{kw} industry trends 2026 future technology changes remote virtual AI impact market growth",
            "prompt": f"Current trends in the {kw} industry. Remote/virtual services, AI integration, technology upgrades, market consolidation. Data-heavy — include specific stats, growth percentages, technology adoption rates.",
            "tags": [kw, "trends", "industry"],
        },
        {
            "slug": f"remote-vs-in-person-{kw.replace(' ', '-')}",
            "title": f"Remote vs. In-Person {kw.title()}s: Which Is Better?",
            "hub": hub_title, "is_hub": False, "cluster": "trends",
            "search_intent": "informational",
            "research_query": f"remote {kw} vs in person virtual services comparison pros cons quality",
            "prompt": f"Comparison: remote/virtual vs. in-person {kw} services. Include comparison table. When remote works fine, when you absolutely need someone in the room. Post-pandemic reality check.",
            "tags": [kw, "remote", "comparison"],
        },
        {
            "slug": f"ai-impact-on-{kw.replace(' ', '-')}s",
            "title": f"Will AI Replace {kw.title()}s? (The Honest Answer)",
            "hub": hub_title, "is_hub": False, "cluster": "trends",
            "search_intent": "informational",
            "research_query": f"AI impact on {kw} automation artificial intelligence replace jobs future technology disruption",
            "prompt": f"Honest take on AI's impact on the {kw} industry. What AI can automate (transcription, editing), what still requires human judgment. Anti-hype: AI assists but doesn't replace for high-stakes work.",
            "tags": [kw, "AI", "future"],
        },

        # ── CLUSTER 8: CITY-SPECIFIC GUIDES (top 5 markets) ──────────
        {
            "slug": f"best-{kw.replace(' ', '-')}s-new-york",
            "title": f"Best {kw.title()}s in New York ({datetime.now().year} Guide)",
            "hub": hub_title, "is_hub": False, "cluster": "city-guide",
            "search_intent": "commercial",
            "research_query": f"best {kw} New York NYC top rated reviews pricing market",
            "prompt": f"City-specific guide for {kw}s in New York. Market overview, what makes NYC different (pricing, courthouse logistics, competition), tips for hiring locally. Link to /new-york/ directory page.",
            "tags": [kw, "new-york", "city-guide"],
        },
        {
            "slug": f"best-{kw.replace(' ', '-')}s-los-angeles",
            "title": f"Best {kw.title()}s in Los Angeles ({datetime.now().year} Guide)",
            "hub": hub_title, "is_hub": False, "cluster": "city-guide",
            "search_intent": "commercial",
            "research_query": f"best {kw} Los Angeles LA top rated reviews pricing market",
            "prompt": f"City-specific guide for {kw}s in Los Angeles. Market overview, what makes LA different, tips for hiring locally. Link to /los-angeles/ directory page.",
            "tags": [kw, "los-angeles", "city-guide"],
        },
        {
            "slug": f"best-{kw.replace(' ', '-')}s-chicago",
            "title": f"Best {kw.title()}s in Chicago ({datetime.now().year} Guide)",
            "hub": hub_title, "is_hub": False, "cluster": "city-guide",
            "search_intent": "commercial",
            "research_query": f"best {kw} Chicago top rated reviews pricing market",
            "prompt": f"City-specific guide for {kw}s in Chicago. Market overview, local specifics. Link to /chicago/ directory page.",
            "tags": [kw, "chicago", "city-guide"],
        },
        {
            "slug": f"best-{kw.replace(' ', '-')}s-houston",
            "title": f"Best {kw.title()}s in Houston ({datetime.now().year} Guide)",
            "hub": hub_title, "is_hub": False, "cluster": "city-guide",
            "search_intent": "commercial",
            "research_query": f"best {kw} Houston Texas top rated reviews pricing market",
            "prompt": f"City-specific guide for {kw}s in Houston. Texas market overview, local specifics. Link to /houston/ directory page.",
            "tags": [kw, "houston", "city-guide"],
        },
        {
            "slug": f"best-{kw.replace(' ', '-')}s-miami",
            "title": f"Best {kw.title()}s in Miami ({datetime.now().year} Guide)",
            "hub": hub_title, "is_hub": False, "cluster": "city-guide",
            "search_intent": "commercial",
            "research_query": f"best {kw} Miami Florida top rated reviews pricing market",
            "prompt": f"City-specific guide for {kw}s in Miami. Florida market overview, local specifics. Link to /miami/ directory page.",
            "tags": [kw, "miami", "city-guide"],
        },

        # ── CLUSTER 9: COMPARISON / VS ARTICLES ──────────────────────
        {
            "slug": f"{kw.replace(' ', '-')}-vs-court-reporter",
            "title": f"{kw.title()} vs. Court Reporter: Do You Need Both?",
            "hub": hub_title, "is_hub": False, "cluster": "comparison",
            "search_intent": "informational",
            "research_query": f"{kw} vs court reporter difference do you need both roles comparison",
            "prompt": f"Comparison of {kw}s and court reporters. Different roles, when you need both, cost implications. Comparison table. Clear the confusion.",
            "tags": [kw, "comparison", "court-reporter"],
        },
        {
            "slug": f"freelance-vs-agency-{kw.replace(' ', '-')}",
            "title": f"Freelance vs. Agency {kw.title()}: Which Should You Hire?",
            "hub": hub_title, "is_hub": False, "cluster": "comparison",
            "search_intent": "commercial",
            "research_query": f"freelance {kw} vs agency firm comparison pros cons pricing quality",
            "prompt": f"Freelance solo {kw}s vs. agency firms. Comparison table. When each makes sense. Honest pros/cons. Price vs. reliability trade-offs.",
            "tags": [kw, "comparison", "freelance"],
        },

        # ── CLUSTER 10: PRACTICAL / HOW-TO ───────────────────────────
        {
            "slug": f"how-to-prepare-for-a-{kw.replace(' ', '-')}-session",
            "title": f"How to Prepare for a {kw.title()} Session (Attorney's Checklist)",
            "hub": hub_title, "is_hub": False, "cluster": "practical",
            "search_intent": "informational",
            "research_query": f"how to prepare for {kw} session deposition preparation checklist room setup requirements",
            "prompt": f"Practical checklist for attorneys/clients preparing for a {kw} session. Room requirements, what to have ready, timeline, common mistakes. Numbered checklist format — featured snippet bait.",
            "tags": [kw, "preparation", "checklist"],
        },
        {
            "slug": f"common-{kw.replace(' ', '-')}-mistakes",
            "title": f"9 Common {kw.title()} Mistakes (And How to Avoid Them)",
            "hub": hub_title, "is_hub": False, "cluster": "practical",
            "search_intent": "informational",
            "research_query": f"common {kw} mistakes errors problems what goes wrong how to avoid issues",
            "prompt": f"9 most common mistakes when working with a {kw}. From both the hiring side and the provider side. Each mistake: what happens, real-world example, how to prevent it.",
            "tags": [kw, "mistakes", "tips"],
        },
        {
            "slug": f"how-to-review-{kw.replace(' ', '-')}-work",
            "title": f"How to Review a {kw.title()}'s Work (Quality Checklist)",
            "hub": hub_title, "is_hub": False, "cluster": "practical",
            "search_intent": "informational",
            "research_query": f"how to evaluate {kw} quality review work product deliverables what to check",
            "prompt": f"Quality checklist for reviewing {kw} deliverables. What to check, acceptable standards, when to request re-work. Include a downloadable-style checklist format.",
            "tags": [kw, "quality", "checklist"],
        },

        # ── NEWSBAIT / STATISTICS ─────────────────────────────────────
        {
            "slug": f"{kw.replace(' ', '-')}-industry-statistics",
            "title": f"{kw.title()} Industry Statistics ({datetime.now().year}): Market Size, Growth, and Trends",
            "hub": hub_title, "is_hub": False, "cluster": "newsbait",
            "search_intent": "informational",
            "research_query": f"{kw} industry statistics market size growth rate number of professionals revenue 2026",
            "prompt": f"Data-heavy statistics page about the {kw} industry. Market size, growth rate, number of practitioners, average revenue, regional distribution. Include tables and specific numbers. This is linkbait — journalists and bloggers will reference it.",
            "tags": [kw, "statistics", "industry"],
        },
        {
            "slug": f"{kw.replace(' ', '-')}-salary-earnings",
            "title": f"How Much Do {kw.title()}s Make? Salary & Earnings Breakdown",
            "hub": hub_title, "is_hub": False, "cluster": "newsbait",
            "search_intent": "informational",
            "research_query": f"{kw} salary earnings income how much do they make revenue average",
            "prompt": f"Earnings breakdown for {kw}s. Average salary, freelance rates, revenue ranges. By experience level, by region. Comparison table. Useful for both aspiring {kw}s and clients understanding fair pricing.",
            "tags": [kw, "salary", "earnings"],
        },
    ]

    return topics


# ── PERPLEXITY RESEARCH ──────────────────────────────────────────────────

def research_topic(topic: dict, config: dict, pplx_key: str) -> str:
    """Use Perplexity to research a topic. Returns structured research notes."""
    keyword = config.get("primary_keyword", "professional")

    query = f"""Research the following topic thoroughly for a comprehensive article:

Topic: {topic['title']}
Industry: {config.get('industry', '')} / {keyword}

Search for:
{topic['research_query']}

Provide detailed, factual research notes including:
1. Key statistics and data points (with sources where possible)
2. Current pricing/rates if relevant
3. Industry standards and best practices
4. Common pain points and solutions
5. Expert opinions and real-world examples
6. State/regional variations if applicable
7. Recent trends or changes (2024-2026)

Format as structured research notes. Include specific numbers, names, and verifiable facts. No fluff."""

    resp = httpx.post(
        "https://api.perplexity.ai/chat/completions",
        headers={
            "Authorization": f"Bearer {pplx_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": "sonar",
            "messages": [
                {"role": "system", "content": "You are a thorough research assistant. Provide factual, data-rich research notes with specific numbers and verifiable details."},
                {"role": "user", "content": query},
            ],
            "temperature": 0.1,
        },
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


# ── CLAUDE ARTICLE WRITING ───────────────────────────────────────────────

def generate_article(topic: dict, config: dict, research: str, api_key: str, voice_guide: str) -> str:
    """Generate article using Claude with Perplexity research as source material."""
    context = config.get("city_page_prompt_context", "")
    hub_slug = f"complete-guide-{config.get('primary_keyword', '').replace(' ', '-')}s"
    hub_title = f"The Complete Guide to {config.get('primary_keyword', '').title()}s"

    prompt = f"""Write a high-quality blog article based on the research below.

## ARTICLE DETAILS
Title: {topic['title']}
Search Intent: {topic['search_intent']}
Content Cluster: {topic['cluster']}
Hub Article: {hub_title} (link to: /blog/{hub_slug}/)

## RESEARCH DATA (from Perplexity — use these facts and figures):
{research[:4000]}

## INDUSTRY CONTEXT:
{context}

## ARTICLE INSTRUCTIONS:
{topic['prompt']}

## VOICE & STYLE GUIDE (follow strictly):
{voice_guide[:2500]}

## STORYBRAND FRAMING:
The reader is the HERO — a professional who needs this information to make better decisions. You are the GUIDE who has done the research and is sharing what you found. Frame problems as villains, your advice as the plan, and the reader's success as the happy ending.

## FORMATTING REQUIREMENTS:
1. Open with a specific story or vivid scenario (NOT a definition or generic statement)
2. Include "The Short Version" blockquote near the top
3. Include at least one comparison table (markdown table format)
4. Use "Reality Check" and "Pro Tip" callout blocks (as blockquotes with bold prefix)
5. Include a "Key Takeaways" section near the top (3-4 bullet points)
6. Use data from the research — specific numbers, not vague claims
7. Include internal links: /[city-slug]/ for city pages, /blog/[slug]/ for related articles
8. End with a "Practical Bottom Line" section with clear next steps
9. Cross-link to the hub article and at least one other spoke article
10. Punchy one-liners after dense paragraphs

NEVER use: "In this article", "Let's dive in", "Without further ado", "According to experts"
DO use: "I'll be honest", "Here's what most people miss", "Nobody tells you this"

Target length: {'1500-2000 words' if topic.get('is_hub') else '800-1200 words'}

Do NOT include frontmatter. Start directly with the opening.
Do NOT include the title as an H1."""

    resp = httpx.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": "claude-haiku-4-5-20251001",
            "max_tokens": 5000,
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()["content"][0]["text"]


def load_images(vertical: str) -> dict:
    images_path = PROJECT_ROOT / "verticals" / vertical / "images.json"
    if images_path.exists():
        return json.load(open(images_path))
    return {"cities": {}, "articles": {}}


def build_frontmatter(topic: dict, config: dict, images: dict | None = None) -> str:
    today = datetime.now().strftime("%Y-%m-%d")
    editorial = config.get("editorial_author", {})
    author = editorial.get("name", "Editorial Team")
    hub_line = f'hub: "{topic["hub"]}"' if topic.get("hub") else ""

    image_lines = ""
    if images:
        article_images = images.get("articles", {})
        img = article_images.get(topic["slug"])
        if img:
            image_lines = f'image: "{img["url"]}"\nimageCredit: "Photo by [{img["photographer"]}]({img["photographer_url"]}) on [Unsplash]({img["unsplash_url"]})"\n'

    return f"""---
title: "{topic['title']}"
description: "{topic['prompt'][:150].rstrip('.')}."
pubDate: {today}
author: "{author}"
tags: {json.dumps(topic['tags'])}
{hub_line}
{image_lines}---

"""


def main():
    parser = argparse.ArgumentParser(description="Generate blog articles via Perplexity research + Claude writing")
    parser.add_argument("--config", required=True, help="Path to vertical YAML config")
    parser.add_argument("--vertical", required=True, help="Vertical slug")
    parser.add_argument("--topic", help="Specific topic slug (default: all)")
    parser.add_argument("--dry-run", action="store_true", help="Print output instead of writing")
    parser.add_argument("--force", action="store_true", help="Overwrite existing files")
    parser.add_argument("--research-only", action="store_true", help="Only run Perplexity research, skip writing")
    parser.add_argument("--skip-research", action="store_true", help="Skip research, use cached research files")
    parser.add_argument("--limit", type=int, help="Limit number of articles to generate")
    args = parser.parse_args()

    pplx_key = os.environ.get("PERPLEXITY_API_KEY")
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")

    if not pplx_key and not args.skip_research:
        print("Warning: PERPLEXITY_API_KEY not set — will skip research step")
    if not anthropic_key and not args.research_only:
        print("Error: ANTHROPIC_API_KEY environment variable not set")
        raise SystemExit(1)

    config = load_config(args.config)
    voice_guide = load_voice_guide()
    topics = get_article_topics(config)
    images = load_images(args.vertical)

    # Output directories
    vertical_dir = PROJECT_ROOT / "verticals" / args.vertical
    output_dir = vertical_dir / "src" / "content" / "blog"
    research_dir = vertical_dir / "research"
    output_dir.mkdir(parents=True, exist_ok=True)
    research_dir.mkdir(parents=True, exist_ok=True)

    if args.topic:
        topics = [t for t in topics if t["slug"] == args.topic]

    if args.limit:
        topics = topics[:args.limit]

    # Show plan
    clusters = {}
    for t in topics:
        clusters.setdefault(t["cluster"], []).append(t["title"])
    print(f"Article pipeline for {config['name']} — {len(topics)} articles")
    for cluster, titles in clusters.items():
        print(f"  [{cluster}] {len(titles)} articles")

    for i, topic in enumerate(topics):
        output_file = output_dir / f"{topic['slug']}.mdx"
        research_file = research_dir / f"{topic['slug']}.md"

        if output_file.exists() and not args.force and not args.dry_run and not args.research_only:
            print(f"  [{i+1}/{len(topics)}] SKIP {topic['slug']} (exists, use --force)")
            continue

        print(f"  [{i+1}/{len(topics)}] {topic['title']}")

        # Step 1: Research via Perplexity
        research = ""
        if research_file.exists() and (args.skip_research or not pplx_key):
            research = research_file.read_text()
            print(f"    Research: cached ({len(research)} chars)")
        elif pplx_key and not args.skip_research:
            try:
                print(f"    Researching...", end=" ", flush=True)
                research = research_topic(topic, config, pplx_key)
                research_file.write_text(research)
                print(f"OK ({len(research)} chars)")
                time.sleep(1)  # Rate limit
            except Exception as e:
                print(f"Research ERROR: {e}")
                research = ""

        if args.research_only:
            continue

        # Step 2: Write via Claude
        try:
            print(f"    Writing...", end=" ", flush=True)
            body = generate_article(topic, config, research, anthropic_key, voice_guide)
            frontmatter = build_frontmatter(topic, config, images)
            content = frontmatter + body

            if args.dry_run:
                print()
                print(content[:500])
                print("...")
            else:
                with open(output_file, "w") as f:
                    f.write(content)
                print(f"OK ({len(body)} chars)")

        except Exception as e:
            print(f"Write ERROR: {e}")

    if not args.research_only:
        print(f"\nArticles written to {output_dir}")
    print(f"Research saved to {research_dir}")


if __name__ == "__main__":
    main()
