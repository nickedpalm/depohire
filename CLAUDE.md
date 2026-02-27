# Directory Factory

Template-once, deploy-many directory sites for underserved professional niches.

## Tech Stack
- **Site template:** Astro 5 + Tailwind CSS + Pagefind + Leaflet
- **Pipeline:** Python (httpx, pyyaml, sqlite3, BeautifulSoup)
- **Scraping:** Perplexity API (sonar model), Google Maps API, Playwright
- **Content gen:** Anthropic Claude API (Haiku)
- **Deploy target:** Cloudflare Pages

## Setup
```bash
cd ~/directory-factory
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Key Commands
```bash
source .venv/bin/activate  # always activate venv first
python3 factory.py create --config configs/<vertical>.yaml
python3 factory.py scrape --vertical <slug>
python3 factory.py generate --vertical <slug> [--cities] [--articles]
python3 factory.py build --vertical <slug>
python3 factory.py deploy --vertical <slug>
```

## Key Files
- `factory.py` — CLI entry point
- `template/` — Astro site template (copied per vertical)
- `configs/` — Per-vertical YAML configs
- `scripts/scrape_perplexity.py` — Main scraper (Perplexity API, queries by state)
- `scripts/enrich.py` — Review extraction + LLM sentiment analysis
- `scripts/export.py` — SQLite → JSON for Astro
- `scripts/clean_cities.py` — Map messy city names to cities.json slugs
- `verticals/` — Generated instances (gitignored except configs)

## Env Vars
- `PERPLEXITY_API_KEY` — for scrape_perplexity.py
- `ANTHROPIC_API_KEY` — for generate_cities.py, generate_articles.py, sentiment in enrich.py
- `GOOGLE_MAPS_API_KEY` — for scrape.py (Google Maps Places API)

## Article Pipeline
```bash
# Research + write all 30 articles
PERPLEXITY_API_KEY=... ANTHROPIC_API_KEY=... python3 scripts/generate_articles.py --config configs/deposition-videographers.yaml --vertical deposition-videographers

# Research only (saves to verticals/[slug]/research/)
python3 scripts/generate_articles.py ... --research-only

# Write from cached research
python3 scripts/generate_articles.py ... --skip-research

# Single topic
python3 scripts/generate_articles.py ... --topic how-much-does-deposition-videographer-cost
```

### Current Work
- **In progress:** Nothing currently in progress.
- **Next steps:** Visual QA of AstroWind merge (dev server testing). Re-generate 30 blog articles for full page count. Deploy to Cloudflare Pages. Test Leaflet/Pagefind with View Transitions.
- **Blockers:** None

### Session Log
- **2026-02-27 (4):** Portfolio exports. Updated Project Log with AstroWind merge narrative entry (5 sections: What Was Built, Technologies Used, Skills Demonstrated, Connections, Professional Framing). Updated Skills Matrix (Astro 5 → Advanced with Directory Factory, Tailwind → Advanced with dual color systems, Leaflet → Intermediate). Regenerated Resume Bullets (47 bullets across 8 categories, 14 projects — added Directory Factory bullets for Frontend, Backend, AI/ML, Data Engineering, Content & SEO). Generated LinkedIn Summary (4-paragraph professional summary, 4 experience roles covering all 14 projects with 27 bullets, 7 skill categories). All written to Obsidian vault via CouchDB.
- **2026-02-27 (3):** Merged AstroWind theme into directory factory template — complete overhaul. Cloned AstroWind, stripped demo content (vendor/, demo pages, deploy configs). Created `src/utils/astrowind-config.ts` bridge to replace AstroWind's virtual module system (`astrowind:config`) with our `vertical.json` config. Ported 17 directory components to `src/components/directory/`, 11 pages using `PageLayout`, merged content schema (blog + cities collections), adapted `utils/blog.ts` for field mapping (`pubDate`→`publishDate`, `description`→`excerpt`, `hub`→`category`). Rewrote `navigation.ts`, `astro.config.ts`, `tailwind.config.js` (dual color system: CSS vars + numeric scale). Fixed build errors: dynamic import in ListingDetail, missing @astrolib/analytics stub, SiteVerification stub. Template builds: 94 pages, zero errors. Deposition-videographers vertical builds: 329 pages, zero errors. Deleted backup and upstream clone.
- **2026-02-27 (2):** Blog styling overhaul. Installed `@tailwindcss/typography` and configured prose theme in `tailwind.config.mjs` (primary-colored links, tighter heading margins, styled table borders with striped rows). Added callout CSS in `global.css` for 4 callout types (info/warning/success/danger) with color-coded left borders and tinted backgrounds. Added client-side script in `BlogPost.astro` that detects bold-prefixed blockquotes (e.g. "Pro Tip:", "Reality Check:") and applies callout classes, plus wraps tables in `overflow-x-auto` divs. Narrowed prose to `max-w-3xl`, added reading time estimate. Redesigned `blog/index.astro` with featured pillar hero card, category-grouped 2-column card grid, and tag pills. Updated both `template/` and `verticals/deposition-videographers/` (10 files). Build: 356 pages, zero errors.
- **2026-02-27:** Implemented all 10 SEO improvements from authority-site-expert: FAQ schema on city pages, trust pages (about/privacy/editorial-guidelines), Organization schema site-wide, enriched LocalBusiness schema, hub/spoke content structure, featured snippet formatting, internal linking, dynamic year in titles, author attribution, statistics page. Integrated StoryBrand framework into homepage and content templates. Created voice-guide.md with writing style rules. Expanded article pipeline from 4 to 30 topics in 10 clusters with two-step Perplexity research + Claude writing. Scraped all 30 US states: 241 listings total. Fixed multiple type coercion bugs. Site builds: 328 pages, zero errors. Logged everything to Obsidian vault.
- **2026-02-26:** Built entire directory factory from scratch. Astro 5 template with 13 components (ListingCard, ListingDetail, CityGrid, LeafletMap, SearchBar, SEOHead, Breadcrumbs, StateList, ReviewStars, ContactForm, ClaimBanner, SentimentBadge, ReviewHighlights), 6 page routes, Pagefind search. Factory CLI with create/scrape/generate/build/deploy. Scraping pipeline: Perplexity API scraper (scrape_perplexity.py) + Google Maps + enrichment + sentiment analysis. Scraped 174 real deposition videographer listings across 33 US cities using 30 Perplexity API calls. Built sentiment tracking: reviews table in SQLite, LLM sentiment analysis via Claude Haiku, SentimentBadge + ReviewHighlights components on listing cards and detail pages. Site builds cleanly: 258 pages in 2.5s. First vertical config: deposition-videographers.yaml. Initial git commit (52 files, 3541 lines).
