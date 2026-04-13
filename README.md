# Directory Factory

Programmatic brand asset pipeline for niche directory sites. Generates wordmarks, favicons, and social cards from a JSON config using Python + Pillow.

## What it generates

For each brand in `brands.json`, the factory outputs **16 files**:

| Asset | Variants | Format |
|-------|----------|--------|
| Wordmark (full) | dark + light | PNG + WebP |
| Wordmark (small) | dark + light | PNG + WebP |
| Favicon | 128, 64, 32, 16px | PNG (+ WebP for 64+) |
| Social card | OG image 1200×630 | PNG + WebP |

## Design system

- **Typography**: Inter Display (Bold prefix + Medium suffix) — two-tone weight split
- **Optical kerning**: Adaptive gap based on letter shape analysis at word junctions
- **T-crossbar compensation**: Automatic 3px tuck for suffixes starting with capital T
- **Color**: WCAG 4.5:1 contrast enforcement with automatic HSL darkening
- **Dark mode**: White prefix + brand-color suffix
- **Light mode**: WCAG-adjusted brand-color prefix + dark gray suffix
- **Favicons**: Black weight monogram on brand-color background
- **Export**: Transparent RGBA PNGs (tight-cropped) + WebP performance variants

## Quick start

```bash
pip install -r requirements.txt
python brand_factory.py
python build_gallery.py
open brand_gallery.html
```

## Custom config

```bash
python brand_factory.py --config my-brands.json --output dist/assets
```

### brands.json schema

```json
[
  {
    "slug": "depohire",
    "prefix": "Depo",
    "suffix": "Hire",
    "accent_color": "#2563eb",
    "dark_bg": "#0F1117",
    "favicon_letters": "DH",
    "domain": "depohire.com",
    "category": "Legal",
    "slogan": "Find deposition videographers, fast."
  }
]
```

## Folder structure

```
directory-factory/
├── brand_factory.py      # Main generator
├── build_gallery.py      # HTML gallery builder
├── brands.json           # Brand configuration (24 brands)
├── requirements.txt
├── fonts/
│   └── inter/            # Inter + InterDisplay font files
└── brand_assets/         # Generated output (gitignored)
    ├── depohire/
    │   ├── wordmark-dark.png
    │   ├── wordmark-dark.webp
    │   ├── wordmark-light.png
    │   ├── wordmark-light.webp
    │   ├── wordmark-dark-sm.png
    │   ├── wordmark-dark-sm.webp
    │   ├── wordmark-light-sm.png
    │   ├── wordmark-light-sm.webp
    │   ├── favicon-128.png
    │   ├── favicon-64.png
    │   ├── favicon-32.png
    │   ├── favicon-16.png
    │   ├── social-card.png
    │   └── social-card.webp
    └── ...
```

## Font license

Inter is licensed under the [SIL Open Font License 1.1](https://github.com/rsms/inter/blob/master/LICENSE.txt).
