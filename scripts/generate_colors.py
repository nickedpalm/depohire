#!/usr/bin/env python3
"""
Generate a full Tailwind color scale + derived theme values from a single primary hex color.

Produces colors.json consumed by tailwind.config.js and CustomStyles.astro.

Usage:
    python3 scripts/generate_colors.py "#4f46e5"
    python3 scripts/generate_colors.py --config configs/court-reporters.yaml
"""

import colorsys
import json
import sys
from pathlib import Path


# ── Color math ───────────────────────────────────────────────────────────

def hex_to_rgb(h: str) -> tuple:
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def rgb_to_hex(r: int, g: int, b: int) -> str:
    return f"#{r:02x}{g:02x}{b:02x}"


def rgb_to_hsl(r, g, b):
    r1, g1, b1 = r / 255, g / 255, b / 255
    h, l, s = colorsys.rgb_to_hls(r1, g1, b1)
    return (h * 360, s, l)


def hsl_to_rgb(h, s, l):
    r, g, b = colorsys.hls_to_rgb(h / 360, l, s)
    return (max(0, min(255, int(round(r * 255)))),
            max(0, min(255, int(round(g * 255)))),
            max(0, min(255, int(round(b * 255)))))


def is_warm(h):
    return h < 60 or h > 300


# ── Tailwind scale generation ────────────────────────────────────────────
# Given a primary hex (used as the 600 shade), generate a full 50-950 scale
# by adjusting lightness and saturation in HSL space.

SHADE_CONFIG = {
    # shade: (lightness, saturation_mult)
    50:  (0.97, 0.40),
    100: (0.93, 0.50),
    200: (0.86, 0.60),
    300: (0.76, 0.70),
    400: (0.62, 0.85),
    500: (0.50, 0.95),
    600: (None, 1.00),   # use original lightness
    700: (0.38, 1.00),
    800: (0.30, 0.90),
    900: (0.22, 0.80),
    950: (0.14, 0.70),
}


def generate_scale(primary_hex: str) -> dict:
    """Generate a Tailwind-style color scale (50-950) from a primary hex."""
    r, g, b = hex_to_rgb(primary_hex)
    h, s, l = rgb_to_hsl(r, g, b)

    scale = {}
    for shade, (target_l, s_mult) in SHADE_CONFIG.items():
        if target_l is None:
            # Use original values for the 600 shade
            scale[shade] = primary_hex
        else:
            new_s = min(s * s_mult, 1.0)
            new_rgb = hsl_to_rgb(h, new_s, target_l)
            scale[shade] = rgb_to_hex(*new_rgb)

    return scale


# ── Derived theme values ─────────────────────────────────────────────────

def generate_theme_colors(primary_hex: str) -> dict:
    """Generate the complete theme color data from a single primary hex."""
    r, g, b = hex_to_rgb(primary_hex)
    h, s, l = rgb_to_hsl(r, g, b)

    scale = generate_scale(primary_hex)

    # Secondary: slightly darker version of primary
    sec_rgb = hsl_to_rgb(h, min(s, 0.9), max(l - 0.08, 0.1))
    secondary_hex = rgb_to_hex(*sec_rgb)

    # Accent: shift hue by 60 degrees
    accent_h = (h + 60) % 360
    accent_rgb = hsl_to_rgb(accent_h, min(s * 0.8, 0.8), 0.45)
    accent_hex = rgb_to_hex(*accent_rgb)

    # Navy shades (very dark, desaturated versions of the hue)
    navy_800 = rgb_to_hex(*hsl_to_rgb(h, min(s * 0.5, 0.4), 0.22))
    navy_900 = rgb_to_hex(*hsl_to_rgb(h, min(s * 0.4, 0.35), 0.15))
    navy_950 = rgb_to_hex(*hsl_to_rgb(h, min(s * 0.35, 0.3), 0.10))

    # Hero gradient: darkest → mid-dark → primary
    grad_start = rgb_to_hex(*hsl_to_rgb(h, min(s * 0.35, 0.3), 0.08))
    grad_mid = rgb_to_hex(*hsl_to_rgb(h, min(s * 0.5, 0.5), 0.18))
    grad_end = primary_hex

    # Box shadow color (primary at low opacity — store as RGB for rgba())
    shadow_rgb = hex_to_rgb(scale[600])

    # CSS custom property values
    primary_rgb = hex_to_rgb(primary_hex)
    secondary_rgb = hex_to_rgb(secondary_hex)
    accent_rgb = hex_to_rgb(accent_hex)

    return {
        "primary": scale,
        "navy": {
            "800": navy_800,
            "900": navy_900,
            "950": navy_950,
        },
        "secondary": secondary_hex,
        "accent": accent_hex,
        "heroGradient": {
            "start": grad_start,
            "mid": grad_mid,
            "end": grad_end,
        },
        "shadow": {
            "r": shadow_rgb[0],
            "g": shadow_rgb[1],
            "b": shadow_rgb[2],
        },
        "cssVars": {
            "primary": f"rgb({primary_rgb[0]} {primary_rgb[1]} {primary_rgb[2]})",
            "secondary": f"rgb({secondary_rgb[0]} {secondary_rgb[1]} {secondary_rgb[2]})",
            "accent": f"rgb({accent_rgb[0]} {accent_rgb[1]} {accent_rgb[2]})",
        },
    }


def write_colors_json(primary_hex: str, output_path: Path):
    """Generate and write colors.json."""
    colors = generate_theme_colors(primary_hex)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(colors, f, indent=2)
    print(f"  Wrote {output_path}")
    return colors


# ── CLI ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/generate_colors.py <hex> | --config <path>")
        sys.exit(1)

    if sys.argv[1] == "--config":
        import yaml
        with open(sys.argv[2]) as f:
            config = yaml.safe_load(f)
        primary = config.get("primary_color", "#2563eb")
        slug = config["slug"]
        output = Path(__file__).parent.parent / "verticals" / slug / "colors.json"
    else:
        primary = sys.argv[1]
        output = Path("colors.json")

    colors = write_colors_json(primary, output)
    print(json.dumps(colors, indent=2))
