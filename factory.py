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
    name = config["name"]
    brand = config.get("brand_name", domain.split(".")[0].capitalize())
    editorial = config.get("editorial_author", {})
    return {
        "name": name,
        "brandName": brand,
        "slug": config["slug"],
        "domain": domain,
        "siteUrl": f"https://{domain}",
        "tagline": config.get("tagline", f"Find {name.lower()} near you"),
        "description": config.get("description", f"A directory of {name.lower()}"),
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
            "bio": editorial.get("bio", f"Expert contributor at {name}."),
            "linkedin": editorial.get("linkedin"),
        },
        "stripeSponsoredLink": config.get("stripe_sponsored_link", ""),
        "stripeCityProLink": config.get("stripe_city_pro_link", ""),
        "turnsiteSitekey": config.get("turnstile_sitekey", ""),
        "googleAnalyticsId": config.get("google_analytics_id", ""),
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

    # Patch robots.txt with actual domain
    domain = config.get("domain", "example.com")
    site_url = f"https://{domain}"
    robots_path = vertical_dir / "public" / "robots.txt"
    if robots_path.exists():
        txt = robots_path.read_text()
        txt = txt.replace("SITE_URL", site_url).replace("SITE_DOMAIN", domain)
        robots_path.write_text(txt)
        print(f"  Patched robots.txt")

    # Patch package.json deploy script with project name
    pkg_path = vertical_dir / "package.json"
    if pkg_path.exists():
        pkg = pkg_path.read_text()
        project_name = config["slug"].replace("_", "-")
        pkg = pkg.replace("PROJECT_NAME", project_name)
        pkg_path.write_text(pkg)
        print(f"  Patched package.json (project: {project_name})")

    # Patch site.webmanifest with brand name
    manifest_path = vertical_dir / "public" / "site.webmanifest"
    if manifest_path.exists():
        brand = config.get("brand_name", domain.split(".")[0].capitalize())
        txt = manifest_path.read_text()
        txt = txt.replace("BRAND_NAME", brand)
        manifest_path.write_text(txt)
        print(f"  Patched site.webmanifest")

    # Generate color theme (colors.json)
    try:
        from scripts.generate_colors import write_colors_json
        primary_color = config.get("primary_color", "#2563eb")
        write_colors_json(primary_color, vertical_dir / "colors.json")
    except Exception as e:
        print(f"  Warning: Color generation failed: {e}")

    # Generate brand assets (logo, favicons, OG image)
    try:
        from scripts.generate_assets import generate_assets
        generate_assets(args.config)
    except Exception as e:
        print(f"  Warning: Asset generation failed: {e}")
        print(f"  Run manually: python3 scripts/generate_assets.py --config {args.config}")

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

def _source_fingerprint(vertical_dir: Path, config_path: Path) -> str:
    """Hash the inputs that could change what gets built/deployed.

    Covers the vertical's src/public/data dirs, its config, and package manifests.
    Uses file path + size + mtime (ns) — fast and sufficient for change detection.
    """
    import hashlib
    h = hashlib.sha256()
    targets = [
        vertical_dir / "src",
        vertical_dir / "public",
        vertical_dir / "data",
        vertical_dir / "package.json",
        vertical_dir / "package-lock.json",
        vertical_dir / "astro.config.ts",
        vertical_dir / "astro.config.mjs",
        config_path,
    ]
    entries = []
    for target in targets:
        if not target.exists():
            continue
        if target.is_file():
            st = target.stat()
            entries.append(f"{target}|{st.st_size}|{st.st_mtime_ns}")
        else:
            for p in sorted(target.rglob("*")):
                if p.is_file() and "node_modules" not in p.parts and ".astro" not in p.parts:
                    st = p.stat()
                    entries.append(f"{p}|{st.st_size}|{st.st_mtime_ns}")
    for e in sorted(entries):
        h.update(e.encode())
    return h.hexdigest()


def cmd_deploy(args):
    vertical_dir = VERTICALS_DIR / args.vertical
    dist_dir = vertical_dir / "dist"

    if not dist_dir.exists():
        print(f"Error: Build output not found. Run 'factory.py build --vertical {args.vertical}' first.")
        sys.exit(1)

    config_path = CONFIGS_DIR / f"{args.vertical}.yaml"

    # Change detection: skip deploy if source fingerprint matches the last successful deploy.
    # Avoids wasteful daily wrangler deploys when nothing has changed. Pass --force to override.
    # Stored outside the vertical dir (which is a git-tracked deploy target) to keep it out of git.
    hashes_dir = PROJECT_ROOT / ".deploy-hashes"
    hashes_dir.mkdir(exist_ok=True)
    hash_file = hashes_dir / f"{args.vertical}.hash"
    current_hash = _source_fingerprint(vertical_dir, config_path)
    if not args.force and hash_file.exists():
        last_hash = hash_file.read_text().strip()
        if last_hash == current_hash:
            print(f"Skipping deploy: source unchanged since last successful deploy (hash: {current_hash[:12]}).")
            print("Run with --force to deploy anyway.")
            return

    # Derive CF Pages project name from the vertical's domain (e.g. depohire.com -> depohire).
    # The custom domain CNAMEs to a specific project whose name is the domain stem, not the
    # vertical slug. Defaulting to the slug silently publishes to an unused project.
    project_name = args.vertical
    if config_path.exists():
        try:
            with open(config_path) as f:
                cfg = yaml.safe_load(f) or {}
            domain = cfg.get("domain", "")
            if domain:
                project_name = domain.split(".")[0]
        except Exception as e:
            print(f"Warning: could not read domain from {config_path}: {e}. Using vertical slug.")

    result = subprocess.run([str(SCRIPTS_DIR / "deploy.sh"), args.vertical, project_name])
    if result.returncode == 0:
        hash_file.write_text(current_hash)


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


# ── DOCTOR ──────────────────────────────────────────────────────────────────

def cmd_doctor(args):
    from scripts.doctor import run as doctor_run
    verticals = [args.vertical] if args.vertical else None
    sys.exit(doctor_run(verticals=verticals, include_optional=args.optional))


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
    p_deploy.add_argument("--force", action="store_true", help="Deploy even if source hasn't changed since last successful deploy")
    p_deploy.set_defaults(func=cmd_deploy)

    # list
    p_list = subparsers.add_parser("list", help="List all verticals")
    p_list.set_defaults(func=cmd_list)

    # doctor
    p_doctor = subparsers.add_parser("doctor", help="Run health checks against env, APIs, and verticals.")
    p_doctor.add_argument("--vertical", help="Specific vertical slug")
    p_doctor.add_argument("--optional", action="store_true", help="Include optional checks (Google Places, Listmonk, Stripe)")
    p_doctor.set_defaults(func=cmd_doctor)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
