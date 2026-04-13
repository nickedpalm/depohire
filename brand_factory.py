#!/usr/bin/env python3
"""
Directory Factory — Brand Asset Generator
==========================================
Programmatic brand asset pipeline for niche directory sites.
Generates wordmarks, favicons, and social cards from a JSON config.

Design principles:
  - Two-tone font weight split (Bold prefix + Medium suffix)
  - Pixel-accurate alignment via textbbox (not textlength)
  - Adaptive optical kerning based on letter shape analysis
  - WCAG contrast-safe color darkening for light mode
  - Heavy-weight favicon letters for legibility at 16–32px
  - Tight-cropped transparent PNGs (CSS handles centering)
  - Dual export: PNG (canonical) + WebP (performance)

Usage:
    python brand_factory.py                          # defaults
    python brand_factory.py --config brands.json     # custom config
    python brand_factory.py --output dist/assets     # custom output dir

Requires: Pillow >= 10.0, Inter font family in fonts/inter/
"""

import argparse
import json
import os
import colorsys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------------------------
# CONFIG — paths are relative to this script's directory
# ---------------------------------------------------------------------------

SCRIPT_DIR = Path(__file__).resolve().parent

FONT_DIR = SCRIPT_DIR / "fonts" / "inter"
FONTS = {
    "black":    FONT_DIR / "Inter-Black.ttf",
    "extrabold": FONT_DIR / "Inter-ExtraBold.ttf",
    "bold":     FONT_DIR / "Inter-Bold.ttf",
    "semibold": FONT_DIR / "Inter-SemiBold.ttf",
    "medium":   FONT_DIR / "Inter-Medium.ttf",
    "regular":  FONT_DIR / "Inter-Regular.ttf",
}

# InterDisplay variants — optimized for display sizes (wordmarks)
DISPLAY_FONTS = {
    "black":    FONT_DIR / "InterDisplay-Black.ttf",
    "extrabold": FONT_DIR / "InterDisplay-ExtraBold.ttf",
    "bold":     FONT_DIR / "InterDisplay-Bold.ttf",
    "semibold": FONT_DIR / "InterDisplay-SemiBold.ttf",
    "medium":   FONT_DIR / "InterDisplay-Medium.ttf",
    "regular":  FONT_DIR / "InterDisplay-Regular.ttf",
}

# Asset dimensions
WORDMARK_SIZE = (800, 200)
WORDMARK_SMALL_SIZE = (400, 100)
FAVICON_SIZE = (128, 128)
SOCIAL_CARD_SIZE = (1200, 630)

DEFAULT_CONFIG = SCRIPT_DIR / "brands.json"
DEFAULT_OUTPUT = SCRIPT_DIR / "brand_assets"


# ---------------------------------------------------------------------------
# COLOR UTILITIES
# ---------------------------------------------------------------------------

def hex_to_rgb(hex_color: str) -> tuple:
    """Convert hex color string to RGB tuple."""
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def rgb_to_hex(rgb: tuple) -> str:
    """Convert RGB tuple to hex string."""
    return "#{:02x}{:02x}{:02x}".format(*rgb)


def rgb_to_hsl(r, g, b):
    """Convert RGB (0-255) to HSL (H: 0-360, S: 0-1, L: 0-1)."""
    r_, g_, b_ = r / 255.0, g / 255.0, b / 255.0
    h, l, s = colorsys.rgb_to_hls(r_, g_, b_)
    return h * 360, s, l


def hsl_to_rgb(h, s, l):
    """Convert HSL back to RGB (0-255)."""
    r, g, b = colorsys.hls_to_rgb(h / 360.0, l, s)
    return int(r * 255), int(g * 255), int(b * 255)


def relative_luminance(rgb: tuple) -> float:
    """Calculate WCAG 2.1 relative luminance."""
    def linearize(c):
        c = c / 255.0
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = rgb
    return 0.2126 * linearize(r) + 0.7152 * linearize(g) + 0.0722 * linearize(b)


def contrast_ratio(rgb1: tuple, rgb2: tuple) -> float:
    """Calculate WCAG contrast ratio between two colors."""
    l1 = relative_luminance(rgb1)
    l2 = relative_luminance(rgb2)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def ensure_contrast(color_rgb: tuple, bg_rgb: tuple, min_ratio: float = 4.5) -> tuple:
    """
    Darken or lighten a color to meet WCAG contrast minimum against background.
    For light backgrounds, darkens. For dark backgrounds, lightens.
    """
    ratio = contrast_ratio(color_rgb, bg_rgb)
    if ratio >= min_ratio:
        return color_rgb

    h, s, l = rgb_to_hsl(*color_rgb)
    bg_lum = relative_luminance(bg_rgb)
    step = -0.02 if bg_lum > 0.5 else 0.02

    for _ in range(100):
        l = max(0.0, min(1.0, l + step))
        candidate = hsl_to_rgb(h, s, l)
        if contrast_ratio(candidate, bg_rgb) >= min_ratio:
            return candidate

    return color_rgb  # fallback


# ---------------------------------------------------------------------------
# TEXT RENDERING UTILITIES
# ---------------------------------------------------------------------------

def load_font(weight: str, size: int, display: bool = True) -> ImageFont.FreeTypeFont:
    """Load a font with fallback chain: Display → Body → system default."""
    fonts = DISPLAY_FONTS if display else FONTS
    path = fonts.get(weight)
    if path and path.exists():
        return ImageFont.truetype(str(path), size)
    # Fallback to non-display variant
    path = FONTS.get(weight)
    if path and path.exists():
        return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def measure_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont) -> tuple:
    """Get (width, height) of rendered text using textbbox for pixel accuracy."""
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def _compute_word_gap(prefix: str, suffix: str) -> float:
    """Compute adaptive optical gap based on letter shapes at the junction.

    Three tiers:
      - Both sides open (e.g., c+A, t+V): gap = 0
      - One side open  (e.g., m+T, n+V): gap = 1
      - Neither open   (e.g., o+H, e+C): gap = 2

    Capital 'T' override:
      The crossbar creates massive dead space beneath it, making any
      mathematical gap look optically wider than it is. We subtract 3px
      to tuck the preceding letter under the crossbar.
    """
    open_right = set("cCrfFtTvVwWyY7")
    open_left = set("TVFWYAJ")
    top_heavy_left = set("T")

    r_open = prefix[-1] in open_right if prefix else False
    l_open = suffix[0] in open_left if suffix else False

    if r_open and l_open:
        gap = 0
    elif r_open or l_open:
        gap = 1
    else:
        gap = 2

    # Top-heavy suffix adjustment — 3px pullback to tuck under crossbar
    if suffix and suffix[0] in top_heavy_left:
        gap -= 3

    return gap


def draw_two_tone_wordmark(
    draw: ImageDraw.ImageDraw,
    canvas_size: tuple,
    prefix: str,
    suffix: str,
    prefix_color: tuple,
    suffix_color: tuple,
    font_size: int,
    optical_adjust: int = -2,
):
    """
    Draw a two-tone wordmark: Bold prefix + Medium suffix.
    Uses textbbox() pixel bounds for horizontal placement.
    """
    prefix = prefix.strip()
    suffix = suffix.strip()

    font_heavy = load_font("bold", font_size)
    font_secondary = load_font("medium", font_size)

    bbox1 = draw.textbbox((0, 0), prefix, font=font_heavy)
    bbox2 = draw.textbbox((0, 0), suffix, font=font_secondary)

    w1_pixel_width = bbox1[2] - bbox1[0]
    w2_pixel_width = bbox2[2] - bbox2[0]
    word_gap = _compute_word_gap(prefix, suffix)

    total_width = w1_pixel_width + word_gap + w2_pixel_width
    canvas_w, canvas_h = canvas_size

    start_x = (canvas_w - total_width) / 2 - bbox1[0]

    text_height = bbox1[3] - bbox1[1]
    start_y = (canvas_h - text_height) / 2 - bbox1[1] + optical_adjust

    draw.text((start_x, start_y), prefix, font=font_heavy, fill=prefix_color)

    w2_start_x = start_x + bbox1[2] + word_gap - bbox2[0]
    draw.text((w2_start_x, start_y), suffix, font=font_secondary, fill=suffix_color)

    return total_width


# ---------------------------------------------------------------------------
# ASSET GENERATORS
# ---------------------------------------------------------------------------

def _get_wordmark_colors(brand: dict, mode: str):
    """Return (prefix_color, suffix_color) for dark or light mode.

    Dark mode:  white prefix + brand-color suffix
    Light mode: WCAG-adjusted brand-color prefix + dark gray suffix
    """
    if mode == "dark":
        prefix_color = (243, 244, 246)  # #F3F4F6 — soft white
        suffix_color = hex_to_rgb(brand["accent_color"])
    else:
        accent = hex_to_rgb(brand["accent_color"])
        prefix_color = ensure_contrast(accent, (255, 255, 255), min_ratio=4.5)
        suffix_color = (31, 41, 55)  # #1F2937
    return prefix_color, suffix_color


def generate_wordmark(brand: dict, mode: str = "dark") -> Image.Image:
    """Generate a tight-cropped transparent wordmark PNG."""
    prefix_color, suffix_color = _get_wordmark_colors(brand, mode)

    canvas_w, canvas_h = 1000, 200
    img = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    font_heavy = load_font("bold", 56)
    font_secondary = load_font("medium", 56)

    prefix = brand["prefix"].strip()
    suffix = brand["suffix"].strip()

    bbox1 = draw.textbbox((0, 0), prefix, font=font_heavy)
    bbox2 = draw.textbbox((0, 0), suffix, font=font_secondary)
    word_gap = _compute_word_gap(prefix, suffix)

    x1 = 20 - bbox1[0]
    left, top, right, bottom = bbox1
    text_h = bottom - top
    y = (canvas_h - text_h) / 2 - top

    draw.text((x1, y), prefix, font=font_heavy, fill=prefix_color + (255,))
    x2 = x1 + bbox1[2] + word_gap - bbox2[0]
    draw.text((x2, y), suffix, font=font_secondary, fill=suffix_color + (255,))

    bbox = img.getbbox()
    if bbox:
        pad = 12
        crop = (max(0, bbox[0] - pad), max(0, bbox[1] - pad),
                min(canvas_w, bbox[2] + pad), min(canvas_h, bbox[3] + pad))
        img = img.crop(crop)

    return img


def generate_wordmark_small(brand: dict, mode: str = "dark") -> Image.Image:
    """Generate a smaller tight-cropped transparent wordmark."""
    prefix_color, suffix_color = _get_wordmark_colors(brand, mode)

    canvas_w, canvas_h = 600, 120
    img = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    font_heavy = load_font("bold", 32)
    font_secondary = load_font("medium", 32)

    prefix = brand["prefix"].strip()
    suffix = brand["suffix"].strip()

    bbox1 = draw.textbbox((0, 0), prefix, font=font_heavy)
    bbox2 = draw.textbbox((0, 0), suffix, font=font_secondary)
    word_gap = _compute_word_gap(prefix, suffix)

    x1 = 10 - bbox1[0]
    left, top, right, bottom = bbox1
    text_h = bottom - top
    y = (canvas_h - text_h) / 2 - top

    draw.text((x1, y), prefix, font=font_heavy, fill=prefix_color + (255,))
    x2 = x1 + bbox1[2] + word_gap - bbox2[0]
    draw.text((x2, y), suffix, font=font_secondary, fill=suffix_color + (255,))

    bbox = img.getbbox()
    if bbox:
        pad = 8
        crop = (max(0, bbox[0] - pad), max(0, bbox[1] - pad),
                min(canvas_w, bbox[2] + pad), min(canvas_h, bbox[3] + pad))
        img = img.crop(crop)

    return img


def generate_favicon(brand: dict) -> Image.Image:
    """Generate a favicon: colored square with two bold initials."""
    size = FAVICON_SIZE[0]
    bg_color = hex_to_rgb(brand["accent_color"])

    bg_lum = relative_luminance(bg_color)
    text_color = (255, 255, 255) if bg_lum < 0.5 else (20, 20, 20)

    img = Image.new("RGB", (size, size), bg_color)
    draw = ImageDraw.Draw(img)

    initials = brand.get("favicon_letters", brand["prefix"][0] + brand["suffix"][0])

    font_size = int(size * 0.52)
    font = load_font("black", font_size, display=False)

    bbox = draw.textbbox((0, 0), initials, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    x = (size - tw) / 2 - bbox[0]
    y = (size - th) / 2 - bbox[1] - 1

    draw.text((x, y), initials, font=font, fill=text_color)

    return img


def generate_social_card(brand: dict) -> Image.Image:
    """Generate an OG/social card with wordmark, slogan, domain, and category pill."""
    w, h = SOCIAL_CARD_SIZE
    bg_color = hex_to_rgb(brand.get("dark_bg", "#0F1117"))

    img = Image.new("RGB", (w, h), bg_color)
    draw = ImageDraw.Draw(img)

    # Wordmark — dark mode colors
    prefix_color = (243, 244, 246)
    suffix_color = hex_to_rgb(brand["accent_color"])

    font_heavy = load_font("bold", 80)
    font_secondary = load_font("medium", 80)
    prefix = brand["prefix"].strip()
    suffix = brand["suffix"].strip()

    bbox1 = draw.textbbox((0, 0), prefix, font=font_heavy)
    bbox2 = draw.textbbox((0, 0), suffix, font=font_secondary)
    word_gap = _compute_word_gap(prefix, suffix)

    w1_px = bbox1[2] - bbox1[0]
    w2_px = bbox2[2] - bbox2[0]
    total = w1_px + word_gap + w2_px

    x1 = (w - total) / 2 - bbox1[0]
    text_h = bbox1[3] - bbox1[1]
    y = (h - text_h) / 2 - bbox1[1] - 50

    draw.text((x1, y), prefix, font=font_heavy, fill=prefix_color)
    x2 = x1 + bbox1[2] + word_gap - bbox2[0]
    draw.text((x2, y), suffix, font=font_secondary, fill=suffix_color)

    # Slogan
    slogan = brand.get("slogan", "")
    if slogan:
        slogan_font = load_font("regular", 24, display=True)
        sl_bbox = draw.textbbox((0, 0), slogan, font=slogan_font)
        sl_w = sl_bbox[2] - sl_bbox[0]
        sl_x = (w - sl_w) / 2 - sl_bbox[0]
        sl_y = h * 0.57
        draw.text((sl_x, sl_y), slogan, font=slogan_font, fill=(200, 200, 210))

    # Domain
    domain = brand.get("domain", "")
    if domain:
        domain_font = load_font("medium", 18, display=True)
        d_bbox = draw.textbbox((0, 0), domain, font=domain_font)
        d_w = d_bbox[2] - d_bbox[0]
        d_x = (w - d_w) / 2 - d_bbox[0]
        d_y = h * 0.67
        muted = tuple(min(255, c + 60) for c in bg_color)
        draw.text((d_x, d_y), domain, font=domain_font, fill=muted)

    # Category pill
    category = brand.get("category", "")
    if category:
        cat_font = load_font("semibold", 14, display=False)
        cat_bbox = draw.textbbox((0, 0), category.upper(), font=cat_font)
        cat_w = cat_bbox[2] - cat_bbox[0]
        cat_h = cat_bbox[3] - cat_bbox[1]
        pill_w = cat_w + 24
        pill_h = cat_h + 12
        pill_x = (w - pill_w) / 2
        pill_y = h * 0.76

        pill_color = hex_to_rgb(brand["accent_color"])
        pill_color_muted = tuple(max(0, c - 40) for c in pill_color)
        draw.rounded_rectangle(
            [pill_x, pill_y, pill_x + pill_w, pill_y + pill_h],
            radius=4,
            fill=pill_color_muted + (60,) if len(pill_color_muted) == 3 else pill_color_muted,
        )

        cat_x = pill_x + 12
        cat_y = pill_y + (pill_h - cat_h) / 2 - cat_bbox[1]
        pill_text_color = (255, 255, 255) if relative_luminance(pill_color_muted) < 0.5 else (20, 20, 20)
        draw.text((cat_x, cat_y), category.upper(), font=cat_font, fill=pill_text_color)

    return img


# ---------------------------------------------------------------------------
# EXPORT PIPELINE
# ---------------------------------------------------------------------------

def save_optimized(img: Image.Image, path: str, also_webp: bool = True):
    """Save as optimized PNG + optional WebP derivative."""
    png_path = path if path.endswith(".png") else path + ".png"
    img.save(png_path, "PNG", optimize=True)

    if also_webp:
        webp_path = png_path.rsplit(".", 1)[0] + ".webp"
        img.save(webp_path, "WEBP", quality=90, method=6)


def generate_all_assets(brand: dict, output_base: str):
    """Generate the full asset suite for a single brand."""
    slug = brand["slug"]
    brand_dir = os.path.join(output_base, slug)
    os.makedirs(brand_dir, exist_ok=True)

    assets = {}

    # Wordmarks (dark + light, full + small)
    for mode in ("dark", "light"):
        img = generate_wordmark(brand, mode)
        path = os.path.join(brand_dir, f"wordmark-{mode}.png")
        save_optimized(img, path)
        assets[f"wordmark_{mode}"] = path

        img_sm = generate_wordmark_small(brand, mode)
        path_sm = os.path.join(brand_dir, f"wordmark-{mode}-sm.png")
        save_optimized(img_sm, path_sm)
        assets[f"wordmark_{mode}_sm"] = path_sm

    # Favicon (128, 64, 32, 16)
    favicon = generate_favicon(brand)
    for sz in (128, 64, 32, 16):
        resized = favicon.resize((sz, sz), Image.LANCZOS) if sz != 128 else favicon
        path = os.path.join(brand_dir, f"favicon-{sz}.png")
        save_optimized(resized, path, also_webp=(sz >= 64))
        assets[f"favicon_{sz}"] = path

    # Social card
    social = generate_social_card(brand)
    path = os.path.join(brand_dir, "social-card.png")
    save_optimized(social, path)
    assets["social_card"] = path

    return assets


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def run_factory(config_path: str = None, output_dir: str = None):
    """Run the full factory from a JSON config file."""
    config_path = config_path or str(DEFAULT_CONFIG)
    output_dir = output_dir or str(DEFAULT_OUTPUT)

    with open(config_path, "r") as f:
        brands = json.load(f)

    print(f"Directory Factory — generating assets for {len(brands)} brands")
    print(f"  Config: {config_path}")
    print(f"  Output: {output_dir}\n")

    results = {}
    for brand in brands:
        name = brand["prefix"] + brand["suffix"]
        print(f"  {name}...", end=" ", flush=True)
        assets = generate_all_assets(brand, output_dir)
        results[brand["slug"]] = assets
        total_files = sum(1 for _ in Path(os.path.join(output_dir, brand["slug"])).iterdir())
        print(f"{total_files} files")

    total = sum(
        sum(1 for _ in Path(os.path.join(output_dir, b["slug"])).iterdir())
        for b in brands
    )
    print(f"\nDone — {total} files across {len(brands)} brands")
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Directory Factory — Brand Asset Generator")
    parser.add_argument("--config", default=None, help="Path to brands.json config file")
    parser.add_argument("--output", default=None, help="Output directory for brand assets")
    args = parser.parse_args()

    run_factory(config_path=args.config, output_dir=args.output)
