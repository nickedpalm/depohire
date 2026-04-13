#!/usr/bin/env python3
"""
Generate brand assets — clean wordmark logos with line-art profession icons.

Layout: [Line-art Icon] [thin divider] [BrandName / Find Local ...]
Style: Geometric blueprint icons, thin navy strokes, no fills/gradients.

Usage:
    python3 scripts/generate_assets.py --config configs/court-reporters.yaml
    python3 scripts/generate_assets.py --all
"""

import argparse
import colorsys
import math
import re
import yaml
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

PROJECT_ROOT = Path(__file__).parent.parent
FONTS_DIR = PROJECT_ROOT / "template" / "src" / "assets" / "fonts"

# ── Fonts ─────────────────────────────────────────────────────────────
FONT_BOLD = str(FONTS_DIR / "Inter-Bold.ttf")
FONT_REGULAR = str(FONTS_DIR / "Inter-Regular.ttf")

# ── Colors ────────────────────────────────────────────────────────────
NAVY = (13, 45, 94)              # #0d2d5e — icon strokes + brand text
DIVIDER_GRAY = (203, 213, 225)   # #cbd5e1 — thin vertical line
TAG_GRAY = (100, 116, 139)       # #64748b — tagline text
WHITE = (255, 255, 255)

# ── All 24 verticals ─────────────────────────────────────────────────
VERTICALS = [
    {"brand": "DepoHire",        "slug": "deposition-videographers", "tagline": "Find Local Deposition Videographers",     "full_tagline": "Find local deposition videographers",                      "category": "legal"},
    {"brand": "StenoScout",      "slug": "court-reporters",          "tagline": "Find Local Court Reporters",               "full_tagline": "Find certified court reporters and stenographers near you", "category": "legal"},
    {"brand": "LegalTerp",       "slug": "legal-interpreters",       "tagline": "Find Local Legal Interpreters",            "full_tagline": "Find certified legal interpreters near you",                "category": "legal"},
    {"brand": "ServeCircuit",    "slug": "process-servers",          "tagline": "Find Local Process Servers",               "full_tagline": "Find reliable process servers near you",                    "category": "legal"},
    {"brand": "ExpertSlate",     "slug": "expert-witnesses",         "tagline": "Find Local Expert Witnesses",              "full_tagline": "Find qualified expert witnesses for your case",             "category": "legal"},
    {"brand": "ForensicLedger",  "slug": "forensic-accountants",     "tagline": "Find Local Forensic Accountants",          "full_tagline": "Find forensic accountants and financial investigators",     "category": "legal"},
    {"brand": "LNCScout",        "slug": "legal-nurse-consultants",  "tagline": "Find Local Legal Nurse Consultants",       "full_tagline": "Find legal nurse consultants near you",                     "category": "legal"},
    {"brand": "DocketTech",      "slug": "legal-technology",         "tagline": "Find Local Legal Tech Providers",          "full_tagline": "Find legal technology providers and consultants",           "category": "legal"},
    {"brand": "BedsideImaging",  "slug": "mobile-imaging",           "tagline": "Find Local Mobile Imaging Techs",          "full_tagline": "Find mobile imaging technicians near you",                  "category": "healthcare"},
    {"brand": "EHRIntel",        "slug": "ehr-consultants",          "tagline": "Find Local EHR Consultants",               "full_tagline": "Find EHR consultants and implementation specialists",       "category": "healthcare"},
    {"brand": "LocumTrust",      "slug": "locum-tenens",             "tagline": "Find Local Locum Tenens Providers",        "full_tagline": "Find locum tenens providers and staffing agencies",         "category": "healthcare"},
    {"brand": "ChairsideIT",     "slug": "dental-it",                "tagline": "Find Local Dental IT Specialists",         "full_tagline": "Find dental IT specialists near you",                       "category": "healthcare"},
    {"brand": "RCMIntel",        "slug": "medical-billing",          "tagline": "Find Local Medical Billing Specialists",   "full_tagline": "Find medical billing and RCM specialists",                  "category": "healthcare"},
    {"brand": "NDTIntel",        "slug": "ndt-inspectors",           "tagline": "Find Local NDT Inspectors",                "full_tagline": "Find NDT inspectors and testing services",                  "category": "industrial"},
    {"brand": "SCADAIntel",      "slug": "scada-consultants",        "tagline": "Find Local SCADA Consultants",             "full_tagline": "Find SCADA security consultants",                           "category": "industrial"},
    {"brand": "AeriScout",       "slug": "drone-surveyors",          "tagline": "Find Local Drone Surveyors",               "full_tagline": "Find drone surveyors and aerial mapping services",          "category": "industrial"},
    {"brand": "RouteStat",       "slug": "traffic-engineers",        "tagline": "Find Local Traffic Engineers",             "full_tagline": "Find traffic engineers and transportation consultants",     "category": "industrial"},
    {"brand": "CalLedger",       "slug": "calibration-services",     "tagline": "Find Local Calibration Services",          "full_tagline": "Find calibration labs and metrology services",              "category": "industrial"},
    {"brand": "MoldRegistry",    "slug": "mold-inspectors",          "tagline": "Find Local Mold Inspectors",               "full_tagline": "Find certified mold inspectors near you",                   "category": "environmental"},
    {"brand": "RadonTrust",      "slug": "radon-inspectors",         "tagline": "Find Local Radon Inspectors",              "full_tagline": "Find certified radon inspectors and testers",               "category": "environmental"},
    {"brand": "SepticTrust",     "slug": "septic-inspectors",        "tagline": "Find Local Septic Inspectors",             "full_tagline": "Find septic inspectors and system evaluators",              "category": "environmental"},
    {"brand": "EnviVault",       "slug": "environmental-consultants","tagline": "Find Local Environmental Consultants",     "full_tagline": "Find environmental consultants near you",                   "category": "environmental"},
    {"brand": "SurveySlate",     "slug": "land-surveyors",           "tagline": "Find Local Land Surveyors",                "full_tagline": "Find licensed land surveyors near you",                     "category": "property"},
    {"brand": "ChimneyAdvisor",  "slug": "chimney-inspectors",       "tagline": "Find Local Chimney Inspectors",            "full_tagline": "Find certified chimney inspectors near you",                "category": "property"},
]

# ── Primary brand colors ─────────────────────────────────────────────
COLOR_PRIMARIES = {
    "deposition-videographers": "#2563eb",
    "court-reporters":          "#4f46e5",
    "legal-interpreters":       "#0d9488",
    "process-servers":          "#3b82f6",
    "expert-witnesses":         "#7c3aed",
    "forensic-accountants":     "#059669",
    "legal-nurse-consultants":  "#db2777",
    "mobile-imaging":           "#0284c7",
    "ehr-consultants":          "#2563eb",
    "locum-tenens":             "#e11d48",
    "dental-it":                "#0891b2",
    "medical-billing":          "#7c3aed",
    "ndt-inspectors":           "#ea580c",
    "scada-consultants":        "#dc2626",
    "drone-surveyors":          "#0ea5e9",
    "traffic-engineers":        "#ca8a04",
    "calibration-services":     "#4b5563",
    "mold-inspectors":          "#16a34a",
    "radon-inspectors":         "#d97706",
    "septic-inspectors":        "#92400e",
    "environmental-consultants":"#15803d",
    "land-surveyors":           "#65a30d",
    "chimney-inspectors":       "#b91c1c",
    "legal-technology":         "#2563eb",
}


# ══════════════════════════════════════════════════════════════════════
#  Color math
# ══════════════════════════════════════════════════════════════════════

def hex_to_rgb(h: str) -> tuple:
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def rgb_to_hsl(r, g, b):
    r1, g1, b1 = r / 255, g / 255, b / 255
    h, l, s = colorsys.rgb_to_hls(r1, g1, b1)
    return (h * 360, s, l)

def hsl_to_rgb(h, s, l):
    r, g, b = colorsys.hls_to_rgb(h / 360, l, s)
    return (int(r * 255), int(g * 255), int(b * 255))

def is_warm(h):
    return h < 60 or h > 300

def compute_bright(primary_rgb):
    h, s, l = rgb_to_hsl(*primary_rgb)
    return hsl_to_rgb(h, min(s * 0.85, 0.8), max(l, 0.75))

def compute_dark(primary_rgb):
    h, s, l = rgb_to_hsl(*primary_rgb)
    if is_warm(h):
        return hsl_to_rgb(h, min(s, 0.7), 0.15)
    return hsl_to_rgb(h, min(s, 0.6), 0.12)

def compute_darkest(primary_rgb):
    h, s, l = rgb_to_hsl(*primary_rgb)
    if is_warm(h):
        return hsl_to_rgb(h, min(s * 0.5, 0.4), 0.08)
    return hsl_to_rgb(h, min(s * 0.4, 0.35), 0.06)

def get_colors(slug: str) -> dict:
    primary = hex_to_rgb(COLOR_PRIMARIES.get(slug, "#2563eb"))
    return {
        "primary": primary,
        "bright": compute_bright(primary),
        "dark": compute_dark(primary),
        "darkest": compute_darkest(primary),
    }


# ══════════════════════════════════════════════════════════════════════
#  Font helpers
# ══════════════════════════════════════════════════════════════════════

def _load_font(path: str, size: int) -> ImageFont.FreeTypeFont:
    p = Path(path)
    if not p.exists():
        print(f"  WARNING: Font not found: {p}")
        return ImageFont.load_default()
    try:
        return ImageFont.truetype(str(p), size)
    except Exception as e:
        print(f"  WARNING: Failed to load {p.name}: {e}")
        return ImageFont.load_default()

def font_bold(size: int) -> ImageFont.FreeTypeFont:
    return _load_font(FONT_BOLD, size)

def font_regular(size: int) -> ImageFont.FreeTypeFont:
    return _load_font(FONT_REGULAR, size)

def split_brand(name: str) -> tuple:
    parts = re.findall(r'[A-Z][a-z]+|[A-Z]+(?=[A-Z][a-z])|[A-Z]+$', name)
    if len(parts) >= 2:
        return (''.join(parts[:-1]), parts[-1])
    mid = len(name) // 2
    return (name[:mid], name[mid:])

def load_config(path: str) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


# ══════════════════════════════════════════════════════════════════════
#  Line-Art Icon Drawing Functions
#  Each draws within bounding box (x, y) to (x+s, y+s)
#  Parameters: draw, x, y, s (size), c (color), w (stroke width)
# ══════════════════════════════════════════════════════════════════════

def _icon_video_camera(d, x, y, s, c, w):
    """DepoHire — video camera"""
    # Camera body
    bx, by = x, y + int(s * 0.22)
    bw, bh = int(s * 0.62), int(s * 0.56)
    d.rounded_rectangle([(bx, by), (bx + bw, by + bh)], radius=int(s * 0.06), outline=c, width=w)
    # Lens cone
    lx = bx + bw
    d.line([(lx, by + int(bh * 0.2)), (x + s, y + int(s * 0.38))], fill=c, width=w)
    d.line([(lx, by + int(bh * 0.8)), (x + s, y + int(s * 0.62))], fill=c, width=w)
    d.line([(x + s, y + int(s * 0.38)), (x + s, y + int(s * 0.62))], fill=c, width=w)
    # Record indicator
    r = max(int(s * 0.04), 2)
    cx, cy = bx + int(bw * 0.2), by + int(s * 0.08)
    d.ellipse([(cx - r, cy - r), (cx + r, cy + r)], fill=c)


def _icon_stenotype(d, x, y, s, c, w):
    """StenoScout — stenotype machine"""
    # Machine body
    bx, by = x + int(s * 0.1), y + int(s * 0.3)
    bw, bh = int(s * 0.8), int(s * 0.35)
    d.rounded_rectangle([(bx, by), (bx + bw, by + bh)], radius=int(s * 0.05), outline=c, width=w)
    # Keys row (7 small rectangles on top)
    kw = int(s * 0.08)
    kh = int(s * 0.12)
    ky = by - kh + w
    gap = (bw - kw * 7) // 8
    for i in range(7):
        kx = bx + gap + i * (kw + gap)
        d.rectangle([(kx, ky), (kx + kw, by)], outline=c, width=max(w - 1, 1))
    # Paper strip coming out top-center
    px = bx + bw // 2 - int(s * 0.06)
    pw = int(s * 0.12)
    d.rectangle([(px, y + int(s * 0.05)), (px + pw, ky - int(s * 0.02))], outline=c, width=w)
    # Legs
    d.line([(bx + int(bw * 0.25), by + bh), (bx + int(bw * 0.15), y + s)], fill=c, width=w)
    d.line([(bx + int(bw * 0.75), by + bh), (bx + int(bw * 0.85), y + s)], fill=c, width=w)


def _icon_speech_bubbles(d, x, y, s, c, w):
    """LegalTerp — two overlapping speech bubbles"""
    # Left bubble (slightly behind)
    b1x, b1y = x, y + int(s * 0.05)
    b1w, b1h = int(s * 0.6), int(s * 0.45)
    d.rounded_rectangle([(b1x, b1y), (b1x + b1w, b1y + b1h)], radius=int(s * 0.1), outline=c, width=w)
    # Left bubble tail
    tx = b1x + int(b1w * 0.3)
    d.line([(tx, b1y + b1h), (tx - int(s * 0.08), b1y + b1h + int(s * 0.12))], fill=c, width=w)
    d.line([(tx - int(s * 0.08), b1y + b1h + int(s * 0.12)), (tx + int(s * 0.1), b1y + b1h)], fill=c, width=w)
    # Right bubble (overlapping, in front)
    b2x, b2y = x + int(s * 0.35), y + int(s * 0.25)
    b2w, b2h = int(s * 0.6), int(s * 0.45)
    d.rounded_rectangle([(b2x, b2y), (b2x + b2w, b2y + b2h)], radius=int(s * 0.1), outline=c, width=w)
    # Right bubble tail
    tx2 = b2x + int(b2w * 0.7)
    d.line([(tx2, b2y + b2h), (tx2 + int(s * 0.08), b2y + b2h + int(s * 0.12))], fill=c, width=w)
    d.line([(tx2 + int(s * 0.08), b2y + b2h + int(s * 0.12)), (tx2 - int(s * 0.1), b2y + b2h)], fill=c, width=w)


def _icon_envelope(d, x, y, s, c, w):
    """ServeCircuit — envelope with checkmark"""
    # Envelope body
    ex, ey = x + int(s * 0.02), y + int(s * 0.2)
    ew, eh = int(s * 0.96), int(s * 0.6)
    d.rectangle([(ex, ey), (ex + ew, ey + eh)], outline=c, width=w)
    # Flap (V shape)
    d.line([(ex, ey), (ex + ew // 2, ey + int(eh * 0.45))], fill=c, width=w)
    d.line([(ex + ew // 2, ey + int(eh * 0.45)), (ex + ew, ey)], fill=c, width=w)
    # Checkmark in lower-right
    cx = ex + int(ew * 0.65)
    cy = ey + int(eh * 0.65)
    d.line([(cx, cy), (cx + int(s * 0.08), cy + int(s * 0.1))], fill=c, width=w + 1)
    d.line([(cx + int(s * 0.08), cy + int(s * 0.1)), (cx + int(s * 0.22), cy - int(s * 0.08))], fill=c, width=w + 1)


def _icon_podium(d, x, y, s, c, w):
    """ExpertSlate — witness podium with badge"""
    # Podium body (trapezoid)
    top_w = int(s * 0.5)
    bot_w = int(s * 0.65)
    top_y = y + int(s * 0.35)
    bot_y = y + int(s * 0.9)
    cx = x + s // 2
    d.line([(cx - top_w // 2, top_y), (cx + top_w // 2, top_y)], fill=c, width=w)
    d.line([(cx - top_w // 2, top_y), (cx - bot_w // 2, bot_y)], fill=c, width=w)
    d.line([(cx + top_w // 2, top_y), (cx + bot_w // 2, bot_y)], fill=c, width=w)
    d.line([(cx - bot_w // 2, bot_y), (cx + bot_w // 2, bot_y)], fill=c, width=w)
    # Star/badge above
    r = int(s * 0.12)
    sy = y + int(s * 0.15)
    d.ellipse([(cx - r, sy - r), (cx + r, sy + r)], outline=c, width=w)
    # Small star rays
    for angle in range(0, 360, 72):
        rad = math.radians(angle - 90)
        ix = cx + int(r * 0.5 * math.cos(rad))
        iy = sy + int(r * 0.5 * math.sin(rad))
        ox = cx + int(r * 1.5 * math.cos(rad))
        oy = sy + int(r * 1.5 * math.sin(rad))
        d.line([(ix, iy), (ox, oy)], fill=c, width=max(w - 1, 1))


def _icon_magnifying_ledger(d, x, y, s, c, w):
    """ForensicLedger — magnifying glass over open book"""
    # Open book
    bx, by = x + int(s * 0.05), y + int(s * 0.35)
    bw, bh = int(s * 0.6), int(s * 0.55)
    d.rectangle([(bx, by), (bx + bw, by + bh)], outline=c, width=w)
    # Center spine
    d.line([(bx + bw // 2, by), (bx + bw // 2, by + bh)], fill=c, width=w)
    # Text lines on left page
    for i in range(3):
        ly = by + int(bh * 0.2) + i * int(bh * 0.2)
        d.line([(bx + int(bw * 0.08), ly), (bx + int(bw * 0.42), ly)], fill=c, width=max(w - 1, 1))
    # Magnifying glass (overlapping upper-right)
    mr = int(s * 0.18)
    mcx, mcy = x + int(s * 0.72), y + int(s * 0.28)
    d.ellipse([(mcx - mr, mcy - mr), (mcx + mr, mcy + mr)], outline=c, width=w)
    # Handle
    hx = mcx + int(mr * 0.7)
    hy = mcy + int(mr * 0.7)
    d.line([(hx, hy), (hx + int(s * 0.15), hy + int(s * 0.15))], fill=c, width=w + 1)


def _icon_cross_gavel(d, x, y, s, c, w):
    """LNCScout — medical cross + small gavel"""
    # Medical cross
    cw = int(s * 0.2)
    cx, cy = x + int(s * 0.3), y + int(s * 0.4)
    d.rectangle([(cx - cw, cy - cw // 2), (cx + cw, cy + cw // 2)], outline=c, width=w)
    d.rectangle([(cx - cw // 2, cy - cw), (cx + cw // 2, cy + cw)], outline=c, width=w)
    # Gavel (on right side)
    gx = x + int(s * 0.7)
    gy = y + int(s * 0.2)
    # Gavel head
    d.rounded_rectangle([(gx - int(s * 0.12), gy), (gx + int(s * 0.12), gy + int(s * 0.15))],
                        radius=int(s * 0.03), outline=c, width=w)
    # Handle
    d.line([(gx, gy + int(s * 0.15)), (gx, gy + int(s * 0.55))], fill=c, width=w)
    # Strike pad
    d.rounded_rectangle([(x + int(s * 0.5), y + int(s * 0.72)), (x + int(s * 0.9), y + int(s * 0.82))],
                        radius=int(s * 0.02), outline=c, width=w)


def _icon_document_circuit(d, x, y, s, c, w):
    """DocketTech — document with circuit nodes"""
    # Document with folded corner
    dx, dy = x + int(s * 0.12), y + int(s * 0.05)
    dw, dh = int(s * 0.55), int(s * 0.85)
    fold = int(s * 0.12)
    d.line([(dx, dy), (dx + dw - fold, dy)], fill=c, width=w)
    d.line([(dx + dw - fold, dy), (dx + dw, dy + fold)], fill=c, width=w)
    d.line([(dx + dw, dy + fold), (dx + dw, dy + dh)], fill=c, width=w)
    d.line([(dx + dw, dy + dh), (dx, dy + dh)], fill=c, width=w)
    d.line([(dx, dy + dh), (dx, dy)], fill=c, width=w)
    # Fold crease
    d.line([(dx + dw - fold, dy), (dx + dw - fold, dy + fold), (dx + dw, dy + fold)], fill=c, width=max(w - 1, 1))
    # Circuit nodes (3 dots connected by lines)
    nodes = [
        (x + int(s * 0.75), y + int(s * 0.35)),
        (x + int(s * 0.88), y + int(s * 0.55)),
        (x + int(s * 0.75), y + int(s * 0.75)),
    ]
    nr = max(int(s * 0.04), 2)
    for nx, ny in nodes:
        d.ellipse([(nx - nr, ny - nr), (nx + nr, ny + nr)], fill=c)
    d.line([nodes[0], nodes[1]], fill=c, width=max(w - 1, 1))
    d.line([nodes[1], nodes[2]], fill=c, width=max(w - 1, 1))


def _icon_portable_xray(d, x, y, s, c, w):
    """BedsideImaging — portable imaging device on wheels"""
    # Screen/monitor
    mx, my = x + int(s * 0.15), y + int(s * 0.05)
    mw, mh = int(s * 0.7), int(s * 0.45)
    d.rectangle([(mx, my), (mx + mw, my + mh)], outline=c, width=w)
    # Stand
    cx = mx + mw // 2
    d.line([(cx, my + mh), (cx, y + int(s * 0.72))], fill=c, width=w)
    # Base bar
    bx1 = x + int(s * 0.2)
    bx2 = x + int(s * 0.8)
    by = y + int(s * 0.72)
    d.line([(bx1, by), (bx2, by)], fill=c, width=w)
    # Wheels (2 circles)
    wr = max(int(s * 0.06), 2)
    d.ellipse([(bx1 - wr, by), (bx1 + wr, by + wr * 2)], outline=c, width=w)
    d.ellipse([(bx2 - wr, by), (bx2 + wr, by + wr * 2)], outline=c, width=w)
    # Cross on screen
    scx, scy = mx + mw // 2, my + mh // 2
    cr = int(s * 0.08)
    d.line([(scx - cr, scy), (scx + cr, scy)], fill=c, width=w)
    d.line([(scx, scy - cr), (scx, scy + cr)], fill=c, width=w)


def _icon_clipboard_chart(d, x, y, s, c, w):
    """EHRIntel — clipboard with bar chart"""
    # Clipboard body
    cx, cy = x + int(s * 0.12), y + int(s * 0.12)
    cw, ch = int(s * 0.76), int(s * 0.82)
    d.rounded_rectangle([(cx, cy), (cx + cw, cy + ch)], radius=int(s * 0.04), outline=c, width=w)
    # Clip at top
    clw = int(s * 0.3)
    clh = int(s * 0.1)
    clx = cx + (cw - clw) // 2
    d.rounded_rectangle([(clx, cy - clh // 2), (clx + clw, cy + clh // 2)], radius=int(s * 0.03), outline=c, width=w)
    # Bar chart inside (3 bars)
    bar_y_base = cy + int(ch * 0.85)
    bar_w = int(cw * 0.15)
    heights = [0.3, 0.5, 0.35]
    gap = int(cw * 0.08)
    start_x = cx + int(cw * 0.18)
    for i, h_frac in enumerate(heights):
        bx = start_x + i * (bar_w + gap)
        bh = int(ch * h_frac)
        d.rectangle([(bx, bar_y_base - bh), (bx + bar_w, bar_y_base)], outline=c, width=max(w - 1, 1))


def _icon_location_cross(d, x, y, s, c, w):
    """LocumTrust — location pin with medical cross"""
    # Pin outer shape
    cx = x + s // 2
    r = int(s * 0.3)
    top_y = y + int(s * 0.08)
    # Circle part
    d.arc([(cx - r, top_y), (cx + r, top_y + r * 2)], 180, 0, fill=c, width=w)
    # Point
    d.line([(cx - r, top_y + r), (cx, y + int(s * 0.92))], fill=c, width=w)
    d.line([(cx + r, top_y + r), (cx, y + int(s * 0.92))], fill=c, width=w)
    # Medical cross inside
    cr = int(s * 0.1)
    ccy = top_y + r
    d.line([(cx - cr, ccy), (cx + cr, ccy)], fill=c, width=w + 1)
    d.line([(cx, ccy - cr), (cx, ccy + cr)], fill=c, width=w + 1)


def _icon_tooth_circuit(d, x, y, s, c, w):
    """ChairsideIT — tooth outline with tech node"""
    cx = x + int(s * 0.4)
    # Tooth crown (rounded top)
    d.arc([(cx - int(s * 0.25), y + int(s * 0.08)), (cx + int(s * 0.25), y + int(s * 0.48))],
          180, 0, fill=c, width=w)
    # Roots (two lines going down)
    left_top = (cx - int(s * 0.25), y + int(s * 0.28))
    right_top = (cx + int(s * 0.25), y + int(s * 0.28))
    d.line([left_top, (cx - int(s * 0.18), y + int(s * 0.85))], fill=c, width=w)
    d.line([right_top, (cx + int(s * 0.18), y + int(s * 0.85))], fill=c, width=w)
    # Notch at top center
    d.arc([(cx - int(s * 0.08), y + int(s * 0.05)), (cx + int(s * 0.08), y + int(s * 0.2))],
          0, 180, fill=c, width=w)
    # Circuit node (right side)
    nr = max(int(s * 0.05), 2)
    nx, ny = x + int(s * 0.82), y + int(s * 0.35)
    d.ellipse([(nx - nr, ny - nr), (nx + nr, ny + nr)], outline=c, width=w)
    # Connection lines from node
    d.line([(nx, ny + nr), (nx, y + int(s * 0.6))], fill=c, width=max(w - 1, 1))
    d.line([(nx - nr, ny), (cx + int(s * 0.28), y + int(s * 0.28))], fill=c, width=max(w - 1, 1))


def _icon_dollar_cross(d, x, y, s, c, w):
    """RCMIntel — dollar sign in medical cross"""
    cx, cy = x + s // 2, y + s // 2
    # Cross arms
    arm_w = int(s * 0.22)
    arm_l = int(s * 0.38)
    d.rectangle([(cx - arm_w // 2, cy - arm_l), (cx + arm_w // 2, cy + arm_l)], outline=c, width=w)
    d.rectangle([(cx - arm_l, cy - arm_w // 2), (cx + arm_l, cy + arm_w // 2)], outline=c, width=w)
    # Dollar sign in center
    font_s = _load_font(FONT_BOLD, int(s * 0.3))
    d.text((cx, cy), "$", fill=c, font=font_s, anchor="mm")


def _icon_probe_beam(d, x, y, s, c, w):
    """NDTIntel — ultrasonic probe scanning a beam"""
    # I-beam cross section
    bx, by = x + int(s * 0.1), y + int(s * 0.55)
    bw, bh = int(s * 0.8), int(s * 0.35)
    flange = int(s * 0.08)
    # Top flange
    d.line([(bx, by), (bx + bw, by)], fill=c, width=w)
    # Bottom flange
    d.line([(bx, by + bh), (bx + bw, by + bh)], fill=c, width=w)
    # Web
    d.line([(bx + bw // 2, by), (bx + bw // 2, by + bh)], fill=c, width=w)
    # Probe above (handheld device pointing down)
    px = x + int(s * 0.35)
    py_top = y + int(s * 0.08)
    py_bot = by - int(s * 0.05)
    d.rounded_rectangle([(px, py_top), (px + int(s * 0.2), py_bot)], radius=int(s * 0.04), outline=c, width=w)
    # Sound waves from probe
    for i in range(3):
        wy = py_bot + int(s * 0.02) + i * int(s * 0.05)
        arc_r = int(s * 0.06) + i * int(s * 0.04)
        d.arc([(px + int(s * 0.1) - arc_r, wy - arc_r // 2),
               (px + int(s * 0.1) + arc_r, wy + arc_r // 2)], 0, 180, fill=c, width=max(w - 1, 1))


def _icon_control_panel(d, x, y, s, c, w):
    """SCADAIntel — control panel with gear"""
    # Panel body
    px, py = x + int(s * 0.05), y + int(s * 0.1)
    pw, ph = int(s * 0.6), int(s * 0.8)
    d.rounded_rectangle([(px, py), (px + pw, py + ph)], radius=int(s * 0.04), outline=c, width=w)
    # Screen/display at top
    d.rectangle([(px + int(pw * 0.12), py + int(ph * 0.08)),
                 (px + int(pw * 0.88), py + int(ph * 0.4))], outline=c, width=max(w - 1, 1))
    # Buttons row
    for i in range(3):
        bx = px + int(pw * 0.15) + i * int(pw * 0.25)
        by = py + int(ph * 0.55)
        br = max(int(s * 0.04), 2)
        d.ellipse([(bx - br, by - br), (bx + br, by + br)], outline=c, width=max(w - 1, 1))
    # Gear (right side)
    gx, gy = x + int(s * 0.8), y + int(s * 0.35)
    gr = int(s * 0.13)
    d.ellipse([(gx - gr, gy - gr), (gx + gr, gy + gr)], outline=c, width=w)
    ir = int(s * 0.06)
    d.ellipse([(gx - ir, gy - ir), (gx + ir, gy + ir)], outline=c, width=max(w - 1, 1))
    # Gear teeth
    for angle in range(0, 360, 45):
        rad = math.radians(angle)
        ox = gx + int((gr + int(s * 0.04)) * math.cos(rad))
        oy = gy + int((gr + int(s * 0.04)) * math.sin(rad))
        ix = gx + int((gr - int(s * 0.02)) * math.cos(rad))
        iy = gy + int((gr - int(s * 0.02)) * math.sin(rad))
        d.line([(ix, iy), (ox, oy)], fill=c, width=w)


def _icon_drone(d, x, y, s, c, w):
    """AeriScout — quadcopter drone from above"""
    cx, cy = x + s // 2, y + s // 2
    # Center body
    br = int(s * 0.08)
    d.rounded_rectangle([(cx - br, cy - br), (cx + br, cy + br)], radius=br // 2, outline=c, width=w)
    # Four arms (X pattern)
    arm_len = int(s * 0.32)
    for angle in [45, 135, 225, 315]:
        rad = math.radians(angle)
        ax = cx + int(arm_len * math.cos(rad))
        ay = cy + int(arm_len * math.sin(rad))
        d.line([(cx, cy), (ax, ay)], fill=c, width=w)
        # Rotor circle at end
        rr = int(s * 0.1)
        d.ellipse([(ax - rr, ay - rr), (ax + rr, ay + rr)], outline=c, width=max(w - 1, 1))


def _icon_road_chart(d, x, y, s, c, w):
    """RouteStat — perspective road with data nodes"""
    # Road in perspective (two converging lines)
    vanish_x = x + int(s * 0.35)
    vanish_y = y + int(s * 0.15)
    d.line([(vanish_x, vanish_y), (x, y + int(s * 0.92))], fill=c, width=w)
    d.line([(vanish_x, vanish_y), (x + int(s * 0.55), y + int(s * 0.92))], fill=c, width=w)
    # Center dashes
    for i in range(4):
        t = 0.25 + i * 0.18
        dy = vanish_y + int((y + int(s * 0.92) - vanish_y) * t)
        dx = vanish_x + int((x + int(s * 0.275) - vanish_x) * t)
        dash_h = int(s * 0.04) + i
        d.line([(dx, dy), (dx, dy + dash_h)], fill=c, width=max(w - 1, 1))
    # Bar chart on right
    base_y = y + int(s * 0.88)
    bars = [(0.7, 0.35), (0.8, 0.55), (0.9, 0.45)]
    bar_w = int(s * 0.07)
    for frac_x, frac_h in bars:
        bx = x + int(s * frac_x)
        bh = int(s * frac_h)
        d.rectangle([(bx, base_y - bh), (bx + bar_w, base_y)], outline=c, width=max(w - 1, 1))


def _icon_caliper(d, x, y, s, c, w):
    """CalLedger — precision caliper"""
    # Main beam (horizontal)
    beam_y = y + int(s * 0.45)
    d.line([(x + int(s * 0.05), beam_y), (x + int(s * 0.95), beam_y)], fill=c, width=w)
    # Fixed jaw (left, going down)
    fx = x + int(s * 0.05)
    d.line([(fx, beam_y), (fx, y + int(s * 0.85))], fill=c, width=w + 1)
    d.line([(fx, y + int(s * 0.85)), (fx + int(s * 0.15), y + int(s * 0.85))], fill=c, width=w + 1)
    # Sliding jaw
    sx = x + int(s * 0.4)
    d.line([(sx, beam_y), (sx, y + int(s * 0.85))], fill=c, width=w + 1)
    d.line([(sx, y + int(s * 0.85)), (sx - int(s * 0.15), y + int(s * 0.85))], fill=c, width=w + 1)
    # Scale markings on beam
    for i in range(8):
        mx = x + int(s * 0.12) + i * int(s * 0.1)
        mark_h = int(s * 0.06) if i % 2 == 0 else int(s * 0.04)
        d.line([(mx, beam_y - mark_h), (mx, beam_y)], fill=c, width=max(w - 1, 1))
    # Depth rod (thin line extending right from beam)
    d.line([(x + int(s * 0.4), beam_y + w), (x + int(s * 0.4), beam_y + int(s * 0.12))], fill=c, width=max(w - 1, 1))


def _icon_house_magnifier(d, x, y, s, c, w):
    """MoldRegistry — house with magnifying glass"""
    # House body
    hx, hy = x + int(s * 0.05), y + int(s * 0.42)
    hw, hh = int(s * 0.55), int(s * 0.5)
    d.rectangle([(hx, hy), (hx + hw, hy + hh)], outline=c, width=w)
    # Roof
    cx = hx + hw // 2
    d.line([(hx - int(s * 0.05), hy), (cx, y + int(s * 0.12))], fill=c, width=w)
    d.line([(cx, y + int(s * 0.12)), (hx + hw + int(s * 0.05), hy)], fill=c, width=w)
    # Door
    dw = int(hw * 0.25)
    d.rectangle([(cx - dw // 2, hy + hh - int(hh * 0.45)), (cx + dw // 2, hy + hh)], outline=c, width=max(w - 1, 1))
    # Magnifying glass (overlapping right)
    mr = int(s * 0.16)
    mcx, mcy = x + int(s * 0.76), y + int(s * 0.38)
    d.ellipse([(mcx - mr, mcy - mr), (mcx + mr, mcy + mr)], outline=c, width=w)
    d.line([(mcx + int(mr * 0.7), mcy + int(mr * 0.7)),
            (mcx + int(mr * 0.7) + int(s * 0.12), mcy + int(mr * 0.7) + int(s * 0.12))], fill=c, width=w + 1)


def _icon_house_shield(d, x, y, s, c, w):
    """RadonTrust — house with shield/checkmark"""
    # House body
    hx, hy = x + int(s * 0.05), y + int(s * 0.42)
    hw, hh = int(s * 0.55), int(s * 0.5)
    d.rectangle([(hx, hy), (hx + hw, hy + hh)], outline=c, width=w)
    # Roof
    cx = hx + hw // 2
    d.line([(hx - int(s * 0.05), hy), (cx, y + int(s * 0.12))], fill=c, width=w)
    d.line([(cx, y + int(s * 0.12)), (hx + hw + int(s * 0.05), hy)], fill=c, width=w)
    # Shield (right side)
    sx, sy = x + int(s * 0.68), y + int(s * 0.25)
    sw_s, sh = int(s * 0.28), int(s * 0.38)
    # Shield outline (pointed bottom)
    d.line([(sx, sy), (sx + sw_s, sy)], fill=c, width=w)
    d.line([(sx, sy), (sx, sy + int(sh * 0.65))], fill=c, width=w)
    d.line([(sx + sw_s, sy), (sx + sw_s, sy + int(sh * 0.65))], fill=c, width=w)
    d.line([(sx, sy + int(sh * 0.65)), (sx + sw_s // 2, sy + sh)], fill=c, width=w)
    d.line([(sx + sw_s, sy + int(sh * 0.65)), (sx + sw_s // 2, sy + sh)], fill=c, width=w)
    # Checkmark inside shield
    ckx = sx + int(sw_s * 0.25)
    cky = sy + int(sh * 0.45)
    d.line([(ckx, cky), (ckx + int(sw_s * 0.2), cky + int(sh * 0.2))], fill=c, width=w)
    d.line([(ckx + int(sw_s * 0.2), cky + int(sh * 0.2)), (ckx + int(sw_s * 0.55), cky - int(sh * 0.15))], fill=c, width=w)


def _icon_house_tank(d, x, y, s, c, w):
    """SepticTrust — house with underground tank cross-section"""
    # House body
    hx, hy = x + int(s * 0.15), y + int(s * 0.12)
    hw, hh = int(s * 0.7), int(s * 0.35)
    d.rectangle([(hx, hy), (hx + hw, hy + hh)], outline=c, width=w)
    # Roof
    cx = hx + hw // 2
    d.line([(hx - int(s * 0.05), hy), (cx, y + int(s * 0.02))], fill=c, width=w)
    d.line([(cx, y + int(s * 0.02)), (hx + hw + int(s * 0.05), hy)], fill=c, width=w)
    # Ground line
    gy = hy + hh + int(s * 0.05)
    d.line([(x, gy), (x + s, gy)], fill=c, width=w)
    # Underground tank (rounded rectangle below ground)
    tx, ty = x + int(s * 0.1), gy + int(s * 0.08)
    tw, th = int(s * 0.8), int(s * 0.32)
    d.rounded_rectangle([(tx, ty), (tx + tw, ty + th)], radius=int(s * 0.06), outline=c, width=w)
    # Pipe connecting house to tank
    px = cx
    d.line([(px, hy + hh), (px, ty)], fill=c, width=w)
    # Internal divider in tank
    d.line([(tx + tw // 2, ty + int(th * 0.15)), (tx + tw // 2, ty + int(th * 0.85))], fill=c, width=max(w - 1, 1))


def _icon_leaf_shield(d, x, y, s, c, w):
    """EnviVault — leaf inside vault/shield"""
    cx, cy = x + s // 2, y + s // 2
    sw_s, sh = int(s * 0.7), int(s * 0.85)
    # Shield outline
    top_y = y + int(s * 0.05)
    d.line([(cx - sw_s // 2, top_y), (cx + sw_s // 2, top_y)], fill=c, width=w)
    d.line([(cx - sw_s // 2, top_y), (cx - sw_s // 2, top_y + int(sh * 0.55))], fill=c, width=w)
    d.line([(cx + sw_s // 2, top_y), (cx + sw_s // 2, top_y + int(sh * 0.55))], fill=c, width=w)
    d.line([(cx - sw_s // 2, top_y + int(sh * 0.55)), (cx, top_y + sh)], fill=c, width=w)
    d.line([(cx + sw_s // 2, top_y + int(sh * 0.55)), (cx, top_y + sh)], fill=c, width=w)
    # Leaf inside (simple: curved line + center vein)
    leaf_cx, leaf_cy = cx, cy + int(s * 0.02)
    lr = int(s * 0.2)
    # Leaf body using arcs
    d.arc([(leaf_cx - lr, leaf_cy - int(lr * 1.3)), (leaf_cx + int(lr * 0.3), leaf_cy + int(lr * 0.8))],
          30, 240, fill=c, width=w)
    d.arc([(leaf_cx - int(lr * 0.3), leaf_cy - int(lr * 1.3)), (leaf_cx + lr, leaf_cy + int(lr * 0.8))],
          300, 150, fill=c, width=w)
    # Center vein
    d.line([(leaf_cx, leaf_cy - int(lr * 0.8)), (leaf_cx, leaf_cy + int(lr * 0.6))], fill=c, width=max(w - 1, 1))


def _icon_theodolite(d, x, y, s, c, w):
    """SurveySlate — theodolite/transit on tripod"""
    cx = x + s // 2
    # Telescope (small rectangle on top)
    tw, th = int(s * 0.5), int(s * 0.15)
    ty = y + int(s * 0.15)
    d.rectangle([(cx - tw // 2, ty), (cx + tw // 2, ty + th)], outline=c, width=w)
    # Scope circle on right
    sr = int(s * 0.06)
    d.ellipse([(cx + tw // 2 - sr, ty + th // 2 - sr), (cx + tw // 2 + sr, ty + th // 2 + sr)], outline=c, width=w)
    # Base body
    bh = int(s * 0.18)
    bw = int(s * 0.25)
    by = ty + th
    d.rounded_rectangle([(cx - bw // 2, by), (cx + bw // 2, by + bh)], radius=int(s * 0.03), outline=c, width=w)
    # Tripod legs (3 lines from base)
    leg_y = by + bh
    d.line([(cx, leg_y), (cx - int(s * 0.35), y + int(s * 0.95))], fill=c, width=w)
    d.line([(cx, leg_y), (cx + int(s * 0.35), y + int(s * 0.95))], fill=c, width=w)
    d.line([(cx, leg_y), (cx, y + int(s * 0.95))], fill=c, width=w)


def _icon_chimney_check(d, x, y, s, c, w):
    """ChimneyAdvisor — chimney with inspection checkmark"""
    # Chimney stack
    chx = x + int(s * 0.25)
    chw = int(s * 0.35)
    chy = y + int(s * 0.05)
    chh = int(s * 0.75)
    d.rectangle([(chx, chy), (chx + chw, chy + chh)], outline=c, width=w)
    # Cap (wider rectangle on top)
    cap_w = int(s * 0.45)
    cap_h = int(s * 0.06)
    d.rectangle([(chx - int(s * 0.05), chy), (chx + chw + int(s * 0.05), chy + cap_h)], outline=c, width=w)
    # Bricks (a few horizontal lines)
    for i in range(1, 4):
        ly = chy + int(chh * i * 0.25)
        d.line([(chx, ly), (chx + chw, ly)], fill=c, width=max(w - 1, 1))
    # Smoke wisps
    for i in range(2):
        sx = chx + int(chw * 0.3) + i * int(chw * 0.35)
        sy = chy - int(s * 0.02)
        d.arc([(sx - int(s * 0.06), sy - int(s * 0.1)), (sx + int(s * 0.06), sy)], 180, 0, fill=c, width=max(w - 1, 1))
    # Checkmark (right side)
    ckx = x + int(s * 0.68)
    cky = y + int(s * 0.5)
    d.line([(ckx, cky), (ckx + int(s * 0.1), cky + int(s * 0.12))], fill=c, width=w + 1)
    d.line([(ckx + int(s * 0.1), cky + int(s * 0.12)), (ckx + int(s * 0.28), cky - int(s * 0.12))], fill=c, width=w + 1)
    # Small circle around checkmark
    cr = int(s * 0.2)
    ccx = ckx + int(s * 0.14)
    ccy = cky + int(s * 0.02)
    d.ellipse([(ccx - cr, ccy - cr), (ccx + cr, ccy + cr)], outline=c, width=w)


# ── Icon registry ─────────────────────────────────────────────────────
ICON_FUNCTIONS = {
    "deposition-videographers": _icon_video_camera,
    "court-reporters":          _icon_stenotype,
    "legal-interpreters":       _icon_speech_bubbles,
    "process-servers":          _icon_envelope,
    "expert-witnesses":         _icon_podium,
    "forensic-accountants":     _icon_magnifying_ledger,
    "legal-nurse-consultants":  _icon_cross_gavel,
    "legal-technology":         _icon_document_circuit,
    "mobile-imaging":           _icon_portable_xray,
    "ehr-consultants":          _icon_clipboard_chart,
    "locum-tenens":             _icon_location_cross,
    "dental-it":                _icon_tooth_circuit,
    "medical-billing":          _icon_dollar_cross,
    "ndt-inspectors":           _icon_probe_beam,
    "scada-consultants":        _icon_control_panel,
    "drone-surveyors":          _icon_drone,
    "traffic-engineers":        _icon_road_chart,
    "calibration-services":     _icon_caliper,
    "mold-inspectors":          _icon_house_magnifier,
    "radon-inspectors":         _icon_house_shield,
    "septic-inspectors":        _icon_house_tank,
    "environmental-consultants":_icon_leaf_shield,
    "land-surveyors":           _icon_theodolite,
    "chimney-inspectors":       _icon_chimney_check,
}


# ══════════════════════════════════════════════════════════════════════
#  Wordmark Logo Layout
# ══════════════════════════════════════════════════════════════════════

def generate_logo(brand_name: str, slug: str, logo_tagline: str, colors: dict, output_dir: Path):
    """
    Generate two-tone wordmark logo: [Part1 in navy][Part2 in accent] + tagline.
    Outputs: logo.png, logo-dark.png (on transparent), logo-light.png (for dark bg)
    """
    part1, part2 = split_brand(brand_name)
    pad_x, pad_y = 24, 18

    brand_font = font_bold(44)
    tag_font = font_regular(15)

    # Measure text
    dummy = Image.new("RGBA", (1, 1))
    dd = ImageDraw.Draw(dummy)

    bb1 = dd.textbbox((0, 0), part1, font=brand_font, anchor="lt")
    w1, h1 = bb1[2] - bb1[0], bb1[3] - bb1[1]
    bb2 = dd.textbbox((0, 0), part2, font=brand_font, anchor="lt")
    w2 = bb2[2] - bb2[0]
    brand_w = w1 + w2
    brand_h = h1

    total_w = pad_x + brand_w + pad_x
    total_h = pad_y + brand_h + pad_y

    def _draw_wordmark(draw, color1, color2):
        # Part 1 of brand name
        x = pad_x
        y = pad_y
        draw.text((x, y), part1, fill=color1, font=brand_font, anchor="lt")
        # Part 2 right after, in accent color
        draw.text((x + w1, y), part2, fill=color2, font=brand_font, anchor="lt")

    # ── Dark logo (for light backgrounds): navy + accent ──
    img = Image.new("RGBA", (total_w, total_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    _draw_wordmark(draw, NAVY, colors["primary"])
    img.save(output_dir / "logo.png")
    img.save(output_dir / "logo-dark.png")
    print(f"  logo.png / logo-dark.png ({total_w}x{total_h})")

    # ── Light logo (for dark backgrounds): white + bright accent ──
    img_light = Image.new("RGBA", (total_w, total_h), (0, 0, 0, 0))
    draw_light = ImageDraw.Draw(img_light)
    _draw_wordmark(draw_light, WHITE, colors["bright"])
    img_light.save(output_dir / "logo-light.png")
    print(f"  logo-light.png ({total_w}x{total_h})")


# ══════════════════════════════════════════════════════════════════════
#  Favicons (initials on colored background — icons won't read at 16px)
# ══════════════════════════════════════════════════════════════════════

def generate_favicon(brand_name: str, colors: dict, size: int, output_dir: Path, filename: str):
    part1, part2 = split_brand(brand_name)
    initials = part1[0].upper() + part2[0].upper()

    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    radius = max(size // 5, 2)
    draw.rounded_rectangle([(0, 0), (size - 1, size - 1)], radius=radius,
                           fill=colors["primary"])

    font_size = int(size * 0.44)
    fnt = font_bold(font_size)
    draw.text((size // 2, size // 2), initials, fill=WHITE, font=fnt, anchor="mm")

    img.save(output_dir / filename)
    print(f"  {filename} ({size}x{size})")


def generate_ico(output_dir: Path):
    img16 = Image.open(output_dir / "favicon-16x16.png")
    img32 = Image.open(output_dir / "favicon-32x32.png")
    img32.save(output_dir / "favicon.ico", format="ICO", sizes=[(16, 16), (32, 32)])
    print("  favicon.ico")


# ══════════════════════════════════════════════════════════════════════
#  OG Image (1200x630 social share card)
# ══════════════════════════════════════════════════════════════════════

def generate_og_image(brand_name: str, slug: str, full_tagline: str, colors: dict, output_dir: Path):
    """OG image: dark gradient background with centered two-tone wordmark + tagline."""
    part1, part2 = split_brand(brand_name)
    w, h = 1200, 630
    img = Image.new("RGB", (w, h))
    draw = ImageDraw.Draw(img)

    # ── Gradient background ──
    for y_line in range(h):
        ratio = y_line / h
        if ratio < 0.5:
            t = ratio * 2
            r = int(colors["darkest"][0] + (colors["dark"][0] - colors["darkest"][0]) * t)
            g = int(colors["darkest"][1] + (colors["dark"][1] - colors["darkest"][1]) * t)
            b = int(colors["darkest"][2] + (colors["dark"][2] - colors["darkest"][2]) * t)
        else:
            t = (ratio - 0.5) * 2
            r = int(colors["dark"][0] + (colors["primary"][0] - colors["dark"][0]) * t * 0.15)
            g = int(colors["dark"][1] + (colors["primary"][1] - colors["dark"][1]) * t * 0.15)
            b = int(colors["dark"][2] + (colors["primary"][2] - colors["dark"][2]) * t * 0.15)
        draw.line([(0, y_line), (w, y_line)], fill=(r, g, b))

    # ── Two-tone wordmark centered ──
    brand_font = font_bold(72)
    tag_font = font_regular(26)

    bb1 = draw.textbbox((0, 0), part1, font=brand_font, anchor="lt")
    w1 = bb1[2] - bb1[0]
    bb2 = draw.textbbox((0, 0), part2, font=brand_font, anchor="lt")
    w2 = bb2[2] - bb2[0]
    brand_w = w1 + w2
    brand_h = bb1[3] - bb1[1]

    # Center the brand name
    x_start = (w - brand_w) // 2
    y_brand = h // 2 - brand_h // 2 - 25  # offset up slightly for tagline below

    draw.text((x_start, y_brand), part1, fill=WHITE, font=brand_font, anchor="lt")
    draw.text((x_start + w1, y_brand), part2, fill=colors["bright"], font=brand_font, anchor="lt")

    # ── Tagline below ──
    if full_tagline:
        tag_y = y_brand + brand_h + 16
        draw.text((w // 2, tag_y), full_tagline, fill=(210, 210, 230), font=tag_font, anchor="mt")

    img.save(output_dir / "og-image.png", quality=95)
    print(f"  og-image.png ({w}x{h})")


# ══════════════════════════════════════════════════════════════════════
#  Entry points
# ══════════════════════════════════════════════════════════════════════

def generate_assets(config_path: str = None, output_dir: str = None,
                    brand_name: str = None, slug: str = None, tagline: str = "",
                    full_tagline: str = "", category: str = "legal"):
    if config_path:
        config = load_config(config_path)
        brand_name = config.get("brand_name", config["name"])
        slug = config["slug"]
        full_tagline = config.get("tagline", "")
        for v in VERTICALS:
            if v["slug"] == slug:
                tagline = v["tagline"]
                full_tagline = full_tagline or v["full_tagline"]
                category = v["category"]
                break

    colors = get_colors(slug)
    out = Path(output_dir) if output_dir else PROJECT_ROOT / "verticals" / slug / "public"
    out.mkdir(parents=True, exist_ok=True)

    h_val, _, _ = rgb_to_hsl(*colors["primary"])
    tone = "warm" if is_warm(h_val) else "cool"
    print(f"\n{brand_name} ({slug}) [{category}/{tone}]")

    generate_logo(brand_name, slug, tagline, colors, out)
    for size, name in [(16, "favicon-16x16.png"), (32, "favicon-32x32.png"),
                       (180, "apple-touch-icon.png"), (192, "android-chrome-192x192.png"),
                       (512, "android-chrome-512x512.png")]:
        generate_favicon(brand_name, colors, size, out, name)
    generate_ico(out)
    generate_og_image(brand_name, slug, full_tagline, colors, out)
    print(f"  → {out}")


def generate_all():
    output_base = PROJECT_ROOT / "brand-assets"
    output_base.mkdir(exist_ok=True)
    for v in VERTICALS:
        out = output_base / v["slug"]
        out.mkdir(parents=True, exist_ok=True)
        generate_assets(brand_name=v["brand"], slug=v["slug"],
                        tagline=v["tagline"], full_tagline=v["full_tagline"],
                        category=v["category"], output_dir=str(out))
    print(f"\n{'=' * 60}")
    print(f"Generated assets for {len(VERTICALS)} verticals → {output_base}")


def main():
    parser = argparse.ArgumentParser(description="Generate brand assets (wordmark + line-art icons)")
    parser.add_argument("--config", help="Path to vertical YAML config")
    parser.add_argument("--output", help="Output directory")
    parser.add_argument("--all", action="store_true", help="Generate for all 24 verticals")
    args = parser.parse_args()
    if args.all:
        generate_all()
    elif args.config:
        generate_assets(config_path=args.config, output_dir=args.output)
    else:
        parser.error("Either --config or --all is required")


if __name__ == "__main__":
    main()
