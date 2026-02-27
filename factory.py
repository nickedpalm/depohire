#!/usr/bin/env python3
"""
Directory Factory CLI — create, scrape, generate, build, and deploy directory verticals.

Usage:
    python3 factory.py create --config configs/deposition-videographers.yaml
    python3 factory.py scrape --vertical deposition-videographers [--city new-york] [--source google_maps]
    python3 factory.py generate --vertical deposition-videographers [--cities] [--articles]
    python3 factory.py build --vertical deposition-videographers
    python3 factory.py deploy --vertical deposition-videographers
    python3 factory.py list
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).parent
TEMPLATE_DIR = PROJECT_ROOT / "template"
VERTICALS_DIR = PROJECT_ROOT / "verticals"
CONFIGS_DIR = PROJECT_ROOT / "configs"
SCRIPTS_DIR = PROJECT_ROOT / "scripts"


def load_config(config_path: str) -> dict:
    with open(config_path) as f:
        return yaml.safe_load(f)


def yaml_to_vertical_json(config: dict) -> dict:
    """Convert YAML config to the vertical.json format expected by Astro."""
    domain = config.get("domain", "example.com")
    editorial = config.get("editorial_author", {})
    return {
        "name": config["name"],
        "slug": config["slug"],
        "domain": domain,
        "siteUrl": f"https://{domain}",
        "tagline": config.get("tagline", f"Find {config['name'].lower()} near you"),
        "description": config.get("description", f"A directory of {config['name'].lower()}"),
        "jobValue": config.get("job_value", ""),
        "industry": config.get("industry", ""),
        "primaryKeyword": config.get("primary_keyword", config["slug"].replace("-", " ")),
        "secondaryKeywords": config.get("secondary_keywords", []),
        "certifications": config.get("certifications", []),
        "extraFields": config.get("extra_fields", []),
        "cityPagePromptContext": config.get("city_page_prompt_context", ""),
        "contactEmail": config.get("contact_email", f"contact@{domain}"),
        "editorialAuthor": {
            "name": editorial.get("name", "Editorial Team"),
            "title": editorial.get("title", "Directory Editor"),
            "bio": editorial.get("bio", f"Expert contributor at {config['name']}."),
            "linkedin": editorial.get("linkedin"),
        },
        "foundedYear": config.get("founded_year", 2026),
    }


# ── CREATE ──────────────────────────────────────────────────────────────────

def cmd_create(args):
    config = load_config(args.config)
    slug = config["slug"]
    vertical_dir = VERTICALS_DIR / slug

    if vertical_dir.exists() and not args.force:
        print(f"Error: {vertical_dir} already exists. Use --force to overwrite.")
        sys.exit(1)

    print(f"Creating vertical: {config['name']} ({slug})")

    # Preserve pipeline.db if it exists
    preserved_db = None
    db_path = vertical_dir / "pipeline.db"
    if db_path.exists():
        preserved_db = db_path.read_bytes()

    # Copy template
    if vertical_dir.exists():
        shutil.rmtree(vertical_dir)
    shutil.copytree(TEMPLATE_DIR, vertical_dir, ignore=shutil.ignore_patterns("node_modules", ".astro", "dist"))

    # Restore pipeline.db
    if preserved_db:
        db_path.write_bytes(preserved_db)
        print(f"  Preserved pipeline.db")

    # Write vertical.json
    vertical_json = yaml_to_vertical_json(config)
    with open(vertical_dir / "vertical.json", "w") as f:
        json.dump(vertical_json, f, indent=2)
    print(f"  Wrote vertical.json")

    # Patch robots.txt with actual site URL
    robots_path = vertical_dir / "public" / "robots.txt"
    if robots_path.exists():
        site_url = f"https://{config.get('domain', 'example.com')}"
        robots_path.write_text(robots_path.read_text().replace("SITE_URL", site_url))
        print(f"  Patched robots.txt")

    # npm install
    print(f"  Running npm install...")
    result = subprocess.run(["npm", "install"], cwd=vertical_dir, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  npm install failed:\n{result.stderr}")
        sys.exit(1)
    print(f"  npm install complete")

    print(f"\nVertical created at {vertical_dir}")
    print(f"  Run: python3 factory.py build --vertical {slug}")


# ── SCRAPE ──────────────────────────────────────────────────────────────────

def cmd_scrape(args):
    config_path = find_config(args.vertical)
    cmd = [sys.executable, str(SCRIPTS_DIR / "scrape.py"), "--config", config_path]
    if args.city:
        cmd += ["--city", args.city]
    if args.source:
        cmd += ["--source", args.source]

    subprocess.run(cmd)

    # Auto-run clean + geocode + enrich + export
    if not args.no_enrich:
        print("\n--- Cleaning city names ---")
        subprocess.run([sys.executable, str(SCRIPTS_DIR / "clean_cities.py"), args.vertical])
        print("\n--- Geocoding ---")
        subprocess.run([sys.executable, str(SCRIPTS_DIR / "geocode.py"), "--vertical", args.vertical, "--missing-only"])
        print("\n--- Enriching ---")
        subprocess.run([sys.executable, str(SCRIPTS_DIR / "enrich.py"), "--vertical", args.vertical])
        print("\n--- Exporting ---")
        subprocess.run([sys.executable, str(SCRIPTS_DIR / "export.py"), "--vertical", args.vertical])


# ── GENERATE ────────────────────────────────────────────────────────────────

def cmd_generate(args):
    config_path = find_config(args.vertical)

    if args.cities or (not args.cities and not args.articles):
        print("--- Generating city pages ---")
        cmd = [sys.executable, str(SCRIPTS_DIR / "generate_cities.py"),
               "--config", config_path, "--vertical", args.vertical]
        if args.city:
            cmd += ["--city", args.city]
        if args.dry_run:
            cmd += ["--dry-run"]
        subprocess.run(cmd)

    if args.articles or (not args.cities and not args.articles):
        print("\n--- Generating articles ---")
        cmd = [sys.executable, str(SCRIPTS_DIR / "generate_articles.py"),
               "--config", config_path, "--vertical", args.vertical]
        if args.dry_run:
            cmd += ["--dry-run"]
        subprocess.run(cmd)


# ── BUILD ───────────────────────────────────────────────────────────────────

def cmd_build(args):
    vertical_dir = VERTICALS_DIR / args.vertical
    if not vertical_dir.exists():
        print(f"Error: Vertical not found at {vertical_dir}")
        sys.exit(1)

    print(f"Building {args.vertical}...")
    result = subprocess.run(["npm", "run", "build"], cwd=vertical_dir, text=True)
    if result.returncode != 0:
        sys.exit(1)
    print(f"\nBuild complete: {vertical_dir / 'dist'}")


# ── DEPLOY ──────────────────────────────────────────────────────────────────

def cmd_deploy(args):
    vertical_dir = VERTICALS_DIR / args.vertical
    dist_dir = vertical_dir / "dist"

    if not dist_dir.exists():
        print(f"Error: Build output not found. Run 'factory.py build --vertical {args.vertical}' first.")
        sys.exit(1)

    subprocess.run([str(SCRIPTS_DIR / "deploy.sh"), args.vertical])


# ── LIST ────────────────────────────────────────────────────────────────────

def cmd_list(args):
    print("Verticals:")
    if not VERTICALS_DIR.exists():
        print("  (none)")
        return

    for d in sorted(VERTICALS_DIR.iterdir()):
        if d.is_dir() and (d / "package.json").exists():
            has_build = (d / "dist").exists()
            has_db = (d / "pipeline.db").exists()
            status = []
            if has_build:
                status.append("built")
            if has_db:
                status.append("has data")
            status_str = f" [{', '.join(status)}]" if status else ""
            print(f"  {d.name}{status_str}")


# ── HELPERS ─────────────────────────────────────────────────────────────────

def find_config(vertical: str) -> str:
    """Find the YAML config file for a vertical."""
    path = CONFIGS_DIR / f"{vertical}.yaml"
    if path.exists():
        return str(path)
    path = CONFIGS_DIR / f"{vertical}.yml"
    if path.exists():
        return str(path)
    print(f"Error: Config not found for '{vertical}' in {CONFIGS_DIR}")
    sys.exit(1)


# ── MAIN ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Directory Factory CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # create
    p_create = subparsers.add_parser("create", help="Create a new vertical from template")
    p_create.add_argument("--config", required=True, help="Path to vertical YAML config")
    p_create.add_argument("--force", action="store_true", help="Overwrite existing vertical")
    p_create.set_defaults(func=cmd_create)

    # scrape
    p_scrape = subparsers.add_parser("scrape", help="Scrape listings for a vertical")
    p_scrape.add_argument("--vertical", required=True, help="Vertical slug")
    p_scrape.add_argument("--city", help="Specific city slug")
    p_scrape.add_argument("--source", choices=["google_maps", "google_search", "all"])
    p_scrape.add_argument("--no-enrich", action="store_true", help="Skip auto enrichment/export")
    p_scrape.set_defaults(func=cmd_scrape)

    # generate
    p_gen = subparsers.add_parser("generate", help="Generate content (city pages, articles)")
    p_gen.add_argument("--vertical", required=True, help="Vertical slug")
    p_gen.add_argument("--cities", action="store_true", help="Generate city pages only")
    p_gen.add_argument("--articles", action="store_true", help="Generate articles only")
    p_gen.add_argument("--city", help="Specific city slug (for city pages)")
    p_gen.add_argument("--dry-run", action="store_true", help="Print output instead of writing")
    p_gen.set_defaults(func=cmd_generate)

    # build
    p_build = subparsers.add_parser("build", help="Build a vertical's Astro site")
    p_build.add_argument("--vertical", required=True, help="Vertical slug")
    p_build.set_defaults(func=cmd_build)

    # deploy
    p_deploy = subparsers.add_parser("deploy", help="Deploy a vertical to Cloudflare Pages")
    p_deploy.add_argument("--vertical", required=True, help="Vertical slug")
    p_deploy.set_defaults(func=cmd_deploy)

    # list
    p_list = subparsers.add_parser("list", help="List all verticals")
    p_list.set_defaults(func=cmd_list)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
