#!/usr/bin/env python3
"""
Build a self-contained HTML gallery from brand_assets/ + brands.json.
All images are embedded as base64 data URIs — no external dependencies.

Usage:
    python build_gallery.py
    python build_gallery.py --config brands.json --assets brand_assets --output gallery.html
"""

import argparse
import json
import base64
import os
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent


def img_b64(path):
    """Read an image file and return a data URI string."""
    if not os.path.exists(path):
        return ""
    ext = Path(path).suffix.lstrip(".")
    mime = {"png": "image/png", "webp": "image/webp"}.get(ext, "image/png")
    with open(path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode()
    return f"data:{mime};base64,{encoded}"


def brand_card(b, assets_dir):
    slug = b["slug"]
    d = os.path.join(assets_dir, slug)
    accent = b["accent_color"]
    name = b["prefix"] + b["suffix"]
    domain = b.get("domain", "")

    wm_dark = img_b64(os.path.join(d, "wordmark-dark.png"))
    wm_light = img_b64(os.path.join(d, "wordmark-light.png"))
    wm_dark_sm = img_b64(os.path.join(d, "wordmark-dark-sm.png"))
    wm_light_sm = img_b64(os.path.join(d, "wordmark-light-sm.png"))
    fav_128 = img_b64(os.path.join(d, "favicon-128.png"))
    fav_32 = img_b64(os.path.join(d, "favicon-32.png"))
    social = img_b64(os.path.join(d, "social-card.png"))

    return f'''
    <div class="brand-card" id="{slug}">
      <div class="card-header">
        <div class="brand-name-row">
          <img src="{fav_128}" class="header-favicon" alt="{name} favicon">
          <div>
            <h3 class="brand-name">{name}</h3>
            <span class="brand-domain">{domain}</span>
          </div>
          <span class="color-swatch" style="background:{accent};" title="{accent}"></span>
        </div>
      </div>

      <div class="asset-section">
        <div class="section-label">Wordmarks</div>
        <div class="wordmark-grid">
          <div class="wm-cell dark">
            <img src="{wm_dark}" alt="{name} dark wordmark">
          </div>
          <div class="wm-cell light">
            <img src="{wm_light}" alt="{name} light wordmark">
          </div>
          <div class="wm-cell dark small">
            <img src="{wm_dark_sm}" alt="{name} dark wordmark small">
          </div>
          <div class="wm-cell light small">
            <img src="{wm_light_sm}" alt="{name} light wordmark small">
          </div>
        </div>
      </div>

      <div class="asset-section">
        <div class="section-label">Favicon &amp; Social Card</div>
        <div class="extras-row">
          <div class="favicon-group">
            <img src="{fav_128}" class="fav-lg" alt="favicon 128" title="128px">
            <img src="{fav_32}" class="fav-sm" alt="favicon 32" title="32px (actual size)">
          </div>
          <div class="social-card-wrap">
            <img src="{social}" alt="{name} social card">
          </div>
        </div>
      </div>
    </div>
    '''


def build_gallery(config_path, assets_dir, output_path):
    with open(config_path) as f:
        brands = json.load(f)

    # Group by category
    categories = {}
    for b in brands:
        cat = b.get("category", "Other")
        categories.setdefault(cat, []).append(b)

    # Build category sections
    sections_html = ""
    for cat, cat_brands in categories.items():
        cards = "\n".join(brand_card(b, assets_dir) for b in cat_brands)
        sections_html += f'''
        <section class="category-section">
          <h2 class="category-title">{cat}</h2>
          <div class="cards-grid">
            {cards}
          </div>
        </section>
        '''

    # Nav
    nav_links = ""
    for cat in categories:
        nav_links += f'<a href="#{list(categories[cat])[0]["slug"]}" class="nav-pill">{cat} <span class="count">{len(categories[cat])}</span></a>\n'

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Directory Factory — Brand Assets Gallery</title>
<style>
  :root {{
    --bg: #0a0b0f;
    --surface: #14151a;
    --surface2: #1c1d24;
    --border: #2a2b33;
    --text: #e4e4e7;
    --text-muted: #71717a;
    --accent: #6C5CE7;
  }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Inter', 'Segoe UI', sans-serif;
    background: var(--bg);
    color: var(--text);
    line-height: 1.5;
  }}
  .page-header {{
    padding: 48px 40px 32px;
    border-bottom: 1px solid var(--border);
    background: var(--surface);
  }}
  .page-header h1 {{ font-size: 28px; font-weight: 700; letter-spacing: -0.5px; }}
  .page-header p {{ color: var(--text-muted); font-size: 14px; margin-top: 6px; }}
  .stats {{ display: flex; gap: 24px; margin-top: 16px; font-size: 13px; color: var(--text-muted); }}
  .stats strong {{ color: var(--text); font-weight: 600; }}
  .nav-bar {{
    display: flex; gap: 8px; padding: 16px 40px;
    border-bottom: 1px solid var(--border);
    background: var(--surface);
    flex-wrap: wrap; position: sticky; top: 0; z-index: 100;
  }}
  .nav-pill {{
    padding: 6px 14px; background: var(--surface2);
    border: 1px solid var(--border); border-radius: 6px;
    color: var(--text); text-decoration: none;
    font-size: 13px; font-weight: 500; transition: all 0.15s;
  }}
  .nav-pill:hover {{ background: var(--border); }}
  .nav-pill .count {{ color: var(--text-muted); font-weight: 400; margin-left: 4px; }}
  .main {{ max-width: 1400px; margin: 0 auto; padding: 0 40px 80px; }}
  .category-section {{ margin-top: 48px; }}
  .category-title {{
    font-size: 18px; font-weight: 600; color: var(--text-muted);
    text-transform: uppercase; letter-spacing: 1.5px;
    margin-bottom: 20px; padding-bottom: 12px;
    border-bottom: 1px solid var(--border);
  }}
  .cards-grid {{ display: grid; grid-template-columns: 1fr; gap: 24px; }}
  .brand-card {{
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 12px; overflow: hidden;
  }}
  .card-header {{ padding: 20px 24px; border-bottom: 1px solid var(--border); }}
  .brand-name-row {{ display: flex; align-items: center; gap: 14px; }}
  .header-favicon {{ width: 40px; height: 40px; border-radius: 8px; }}
  .brand-name {{ font-size: 20px; font-weight: 700; letter-spacing: -0.3px; }}
  .brand-domain {{ font-size: 13px; color: var(--text-muted); }}
  .color-swatch {{
    width: 28px; height: 28px; border-radius: 6px;
    margin-left: auto; border: 2px solid rgba(255,255,255,0.1); flex-shrink: 0;
  }}
  .asset-section {{ padding: 20px 24px; }}
  .asset-section + .asset-section {{ border-top: 1px solid var(--border); }}
  .section-label {{
    font-size: 11px; font-weight: 600; text-transform: uppercase;
    letter-spacing: 1px; color: var(--text-muted); margin-bottom: 12px;
  }}
  .wordmark-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }}
  .wm-cell {{
    border-radius: 8px; padding: 16px 24px;
    display: flex; align-items: center; justify-content: center; min-height: 72px;
  }}
  .wm-cell.dark {{ background: #0F1117; }}
  .wm-cell.light {{ background: #ffffff; border: 1px solid var(--border); }}
  .wm-cell img {{ max-width: 100%; height: auto; display: block; }}
  .wm-cell.small {{ min-height: 52px; padding: 12px 20px; }}
  .wm-cell.small img {{ max-height: 36px; width: auto; }}
  .extras-row {{ display: flex; gap: 16px; align-items: flex-start; }}
  .favicon-group {{ display: flex; flex-direction: column; align-items: center; gap: 8px; flex-shrink: 0; }}
  .fav-lg {{ width: 64px; height: 64px; border-radius: 10px; }}
  .fav-sm {{ width: 32px; height: 32px; border-radius: 4px; }}
  .social-card-wrap {{ flex: 1; min-width: 0; }}
  .social-card-wrap img {{ width: 100%; height: auto; border-radius: 8px; border: 1px solid var(--border); }}
  @media (min-width: 900px) {{ .cards-grid {{ grid-template-columns: 1fr 1fr; }} }}
</style>
</head>
<body>
<div class="page-header">
  <h1>Directory Factory — Brand Assets Gallery</h1>
  <p>Programmatically generated brand assets &middot; Inter typeface &middot; WCAG contrast-safe</p>
  <div class="stats">
    <span><strong>{len(brands)}</strong> brands</span>
    <span><strong>{len(brands) * 16}</strong> files</span>
    <span><strong>{len(categories)}</strong> categories</span>
    <span>PNG + WebP dual export</span>
  </div>
</div>
<nav class="nav-bar">
  {nav_links}
</nav>
<main class="main">
  {sections_html}
</main>
</body>
</html>
'''

    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
    with open(output_path, "w") as f:
        f.write(html)

    size_kb = os.path.getsize(output_path) / 1024
    print(f"Gallery built: {output_path} ({size_kb:.0f} KB)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build brand assets HTML gallery")
    parser.add_argument("--config", default=str(SCRIPT_DIR / "brands.json"))
    parser.add_argument("--assets", default=str(SCRIPT_DIR / "brand_assets"))
    parser.add_argument("--output", default=str(SCRIPT_DIR / "brand_gallery.html"))
    args = parser.parse_args()

    build_gallery(args.config, args.assets, args.output)
