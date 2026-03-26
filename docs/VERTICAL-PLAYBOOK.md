# Vertical Creation Playbook

The complete guide to spinning up a new directory vertical from the template. Follow every section in order — no skipping.

---

## Table of Contents

1. [Pre-Launch Checklist](#1-pre-launch-checklist)
2. [YAML Config](#2-yaml-config)
3. [Copy Deck](#3-copy-deck)
4. [Color Scheme](#4-color-scheme)
5. [Static Assets](#5-static-assets)
6. [Email Setup](#6-email-setup)
7. [Infrastructure Setup](#7-infrastructure-setup)
8. [Create & Build](#8-create--build)
9. [Apply Copy Deck](#9-apply-copy-deck)
10. [Apply Color Scheme](#10-apply-color-scheme)
11. [Scrape & Generate Content](#11-scrape--generate-content)
12. [Deploy](#12-deploy)
13. [Post-Launch](#13-post-launch)
14. [Vertical Reference: Color Schemes](#appendix-a-color-schemes)
15. [Vertical Reference: All 24 Domains](#appendix-b-all-24-domains)

---

## 1. Pre-Launch Checklist

Before creating a vertical, gather ALL of the following:

### Required
- [ ] **Domain name** (registered, DNS on Cloudflare)
- [ ] **Brand name** (short, memorable — e.g., "DepoHire", "StenoScout")
- [ ] **Primary keyword** (what people search — e.g., "deposition videographer")
- [ ] **Target audience** (who hires them — e.g., "litigation attorneys")
- [ ] **Job value range** (what a single engagement pays — e.g., "$500–2,000+")
- [ ] **Industry** (legal, environmental, healthcare, construction, etc.)
- [ ] **Certifications** (professional certs in this field, if any)
- [ ] **City page context** (2-4 sentence description of what the professional does)
- [ ] **Scrape queries** (Google Maps search terms that find these businesses)

### Optional (Can Add Later)
- [ ] Stripe payment links (sponsored + city pro tiers)
- [ ] Turnstile sitekey (bot protection)
- [ ] Google Analytics ID
- [ ] Guide PDFs
- [ ] Custom logo / favicons / OG image

---

## 2. YAML Config

Create `configs/{slug}.yaml`. The slug must be the URL-safe version of the profession name (e.g., `court-reporters`, `mold-inspectors`).

```yaml
# ── Identity ─────────────────────────────────────────────
name: Court Reporters                          # Full directory name (plural)
brand_name: StenoScout                         # Short brand for UI/emails
slug: court-reporters                          # URL-safe, matches filename
domain: stenoscout.com                         # Primary domain
tagline: "Find certified court reporters near you"
description: "The most comprehensive directory of court reporters in the United States"

# ── Business Context ─────────────────────────────────────
job_value: "$250–1,500+ per session"           # Per-engagement value (used in ROI copy)
industry: legal                                # legal | environmental | healthcare | construction | etc.
certifications:                                # Professional certs (first one gets highlighted)
  - "RPR (Registered Professional Reporter)"
  - "RMR (Registered Merit Reporter)"
  - "CRR (Certified Realtime Reporter)"

# ── Scraping ─────────────────────────────────────────────
scrape_sources:
  - type: google_maps
    query: "court reporter"
  - type: google_maps
    query: "court reporting service"

# ── Content Generation ───────────────────────────────────
city_page_prompt_context: |
  Court reporters create verbatim transcripts of legal proceedings
  including depositions, trials, hearings, and arbitrations. They use
  stenotype machines or voice writing. Many offer realtime reporting
  and expedited delivery. Attorneys and courts hire them for civil
  and criminal proceedings.

# ── Editorial ────────────────────────────────────────────
contact_email: "contact@stenoscout.com"
founded_year: 2026
editorial_author:
  name: "Nick Palmer"
  title: "Founder & Lead Researcher"
  bio: "Nick built this directory to help legal professionals find qualified court reporters without the guesswork."
  linkedin: "https://linkedin.com/in/nickedpalmer"

# ── SEO ──────────────────────────────────────────────────
primary_keyword: "court reporter"              # Singular — used everywhere
secondary_keywords:
  - "stenographer"
  - "court reporting service"
  - "certified court reporter"
  - "realtime reporter"

# ── Listing Schema ───────────────────────────────────────
extra_fields:
  - certifications
  - years_experience
  - services
  - coverage_area
  - equipment

# ── Payments & Integrations ──────────────────────────────
stripe_sponsored_link: ""                      # Set up in Stripe dashboard
stripe_city_pro_link: ""                       # Set up in Stripe dashboard
turnstile_sitekey: ""                          # Set up in CF dashboard
google_analytics_id: ""                        # Set up in GA4
```

---

## 3. Copy Deck

Every vertical needs customized copy on ~10 pages. The template ships with deposition videographer copy as the default. **You MUST update these strings for each vertical.**

### 3.1 Core Strings (Used Everywhere)

These strings appear across 30+ files. Define them once here, then find-and-replace after `factory.py create`:

| Key | Description | DepoHire Example | StenoScout Example |
|-----|-------------|-------------------|---------------------|
| `primaryKeyword` | Singular profession | deposition videographer | court reporter |
| `primaryKeywordPlural` | Plural | deposition videographers | court reporters |
| `primaryKeywordTitleCase` | Title case singular | Deposition Videographer | Court Reporter |
| `primaryKeywordPluralTitleCase` | Title case plural | Deposition Videographers | Court Reporters |
| `targetAudience` | Who hires them | litigation attorneys | attorneys and law firms |
| `targetAudienceSingular` | Singular | attorney | attorney |
| `primaryCert` | Main certification abbreviation | CLVS | RPR |
| `primaryCertFull` | Full cert name | CLVS (Certified Legal Video Specialist) | RPR (Registered Professional Reporter) |
| `certBody` | Certifying organization | NCRA | NCRA |
| `serviceNoun` | What one job is called | deposition | proceeding |
| `serviceNounPlural` | Plural | depositions | proceedings |

### 3.2 Homepage (`src/pages/index.astro`)

| Line | Current Text | Replace With |
|------|-------------|--------------|
| 94 | `Find Deposition Videographers Near You` | `Find {primaryKeywordPluralTitleCase} Near You` |
| 114-115 | `Find the Right Deposition Videographer — Fast` | `Find the Right {primaryKeywordTitleCase} — Fast` |
| 118 | `The only directory built for litigation attorneys. CLVS-certified professionals...` | `The only directory built for {targetAudience}. {primaryCert}-certified professionals, researched credentials, real reviews, and direct quote requests.` |
| 186 | `...deposition videographers near your courthouse` | `...{primaryKeywordPlural} in your area` |
| 194 | `CLVS certifications` | `{primaryCert} certifications` (or remove if no cert) |
| 202 | `deposition details` | `{serviceNoun} details` |
| 213 | `Built for Litigation Attorneys` | `Built for {targetAudience}` |
| 222 | `CLVS Certification, Front and Center` | `{primaryCert} Certification, Front and Center` (or generic: `Verified Credentials`) |
| 223 | `CLVS is the NCRA gold standard...` | Rewrite for your cert/industry |
| 255 | `Real Reviews from Real Attorneys` | `Real Reviews from Real {targetAudience}` |
| 256 | `...what other litigators actually think` | `...what other {targetAudience} actually think` |
| 269 | `Need a Videographer Fast?` | `Need a {primaryKeywordTitleCase} Fast?` |
| 309 | `Trusted by Attorneys Nationwide` | `Trusted by {targetAudience} Nationwide` |
| 356 | `Trusted by Legal Professionals Nationwide` | `Trusted Nationwide` or `Trusted by {targetAudience}` |
| 397 | `Top Cities for Deposition Videographers` | `Top Cities for {primaryKeywordPluralTitleCase}` |
| 425 | `deposition videographers` | `{primaryKeywordPlural}` |
| 451 | `Are You a Deposition Videographer?` | `Are You a {primaryKeywordTitleCase}?` |
| 453 | `...quote requests from attorneys` | `...quote requests from {targetAudience}` |
| 499 | `needs a deposition videographer in` | `needs a {primaryKeyword} in` |

### 3.3 Value Props (Homepage Lines 222-258)

The four value prop cards need industry-appropriate copy. Templates:

**Card 1 — Credentials**
- **Legal:** "CLVS Certification, Front and Center" / "CLVS is the NCRA gold standard..."
- **Environmental:** "Licensed & Certified Inspectors" / "We verify state licenses and professional certifications..."
- **Healthcare:** "Board Certifications Verified" / "We surface board certifications and state licenses..."
- **Generic (no cert):** "Verified Credentials" / "We research qualifications so you don't have to..."

**Card 2 — Speed** (usually works as-is)
- "Get a Quote in Under 2 Minutes" — works for all verticals

**Card 3 — Local** (adjust the fee context)
- **Legal:** "Out-of-market providers add $100–300 in travel fees."
- **Construction/Environmental:** "Out-of-area providers add travel surcharges."
- **Generic:** "We surface local options first to minimize costs."

**Card 4 — Reviews** (adjust audience)
- Replace "attorneys" / "litigators" with `{targetAudience}`

### 3.4 About Page (`src/pages/about.astro`)

The about page has the most industry-specific narrative. **Rewrite these blocks entirely:**

**Hero Problem Statement (lines 44-49):**
```
Current: "Hiring a deposition videographer shouldn't feel like a gamble.
You've got a deposition in two weeks. You need a videographer who shows up
on time, knows FRCP 30(b)(5), and won't fumble the chain of custody..."

Template: "Hiring a {primaryKeyword} shouldn't feel like a gamble.
You've got a {serviceNoun} coming up. You need a {primaryKeyword} who
[industry-specific quality markers]. But you're stuck cold-calling
strangers from a Google search."
```

**Stakes Section (lines 57-73):**
Three risk cards showing what goes wrong with a bad hire. Industry examples:

| Vertical | Risk 1 | Risk 2 | Risk 3 |
|----------|--------|--------|--------|
| Depo videographers | Unusable footage | Bad audio/framing | Opposing counsel challenges |
| Court reporters | Inaccurate transcript | Missed deadline | Appeal overturned |
| Mold inspectors | Missed contamination | Failed clearance test | Liability exposure |
| Septic inspectors | Missed system failure | Failed sale inspection | Costly emergency repair |

**Methodology Section (lines 80+):**
- Replace "litigation professionals who need deposition videographers" → `{targetAudience} who need {primaryKeywordPlural}`
- Replace cert references with your vertical's certs
- "Free for attorneys" → "Free for {targetAudience}" (or "Free to search")

### 3.5 Search Page (`src/pages/search.astro`)

| Line | Current | Replace With |
|------|---------|--------------|
| 14 | `Find a Deposition Videographer` | `Find a {primaryKeywordTitleCase}` |
| 15 | `...curated deposition videographers across...` | `...curated {primaryKeywordPlural} across...` |
| 36 | `Find a Deposition Videographer` | `Find a {primaryKeywordTitleCase}` |
| 100 | `deposition videographers on our platform` | `{primaryKeywordPlural} on our platform` |
| 121 | `attorneys hiring deposition videographers` | `{targetAudience} hiring {primaryKeywordPlural}` |
| 193 | `Deposition videographers near {zip}` | `{primaryKeywordPluralTitleCase} near {zip}` |

### 3.6 Pricing Page (`src/pages/pricing.astro`)

- Replace all "deposition videographer" references with `{primaryKeyword}`
- Update the ROI calculation copy: "A single {serviceNoun} pays {jobValue}"
- Update example listing cards with profession-appropriate names
- Replace "attorney" references with `{targetAudienceSingular}`
- Update cert references

### 3.7 Advertise Page (`src/pages/advertise.astro`)

- Replace "Attorneys in your city are searching for a videographer" → `{targetAudience} in your city are searching for a {primaryKeyword}`
- Update FAQ answers with industry-appropriate search terms
- Replace cert references

### 3.8 Editorial Guidelines (`src/pages/editorial-guidelines.astro`)

- The terminology section references "deposition videographer" vs "court reporter" distinctions
- The licensing disclaimer references FRCP and "deposition video recording"
- **Rewrite both blocks** to match your industry's terminology and regulatory context
- For non-regulated industries, remove or simplify the licensing disclaimer

### 3.9 Blog Index (`src/pages/blog/index.astro`)

- Replace "Deposition Videographer Guides & Resources" → `{primaryKeywordTitleCase} Guides & Resources`
- Replace editorial intro paragraph with industry-appropriate description
- The "Are You a Deposition Videographer?" CTA → `Are You a {primaryKeywordTitleCase}?`

### 3.10 Guides Section (`src/pages/guides/`)

- Update meta descriptions with your vertical's keywords
- Update hero copy: "Free Guides for {targetAudience}"
- Update guide descriptions (or remove guides section if no PDFs yet)

### 3.11 Privacy Page (`src/pages/privacy.astro`)

Already mostly templatized with `config.primaryKeyword`. Check for any remaining hardcoded references to "attorney" or specific data sources.

### 3.12 Quick-Reference: Find-and-Replace Strings

After `factory.py create`, run these replacements across the entire `verticals/{slug}/src/` directory:

```bash
# Case-insensitive replacements — review each match before applying
# Use your editor's find-and-replace, not blind sed

"deposition videographer"  → "{primaryKeyword}"
"deposition videographers" → "{primaryKeywordPlural}"
"Deposition Videographer"  → "{primaryKeywordTitleCase}"
"Deposition Videographers" → "{primaryKeywordPluralTitleCase}"
"litigation attorneys"     → "{targetAudience}"
"attorneys"                → "{targetAudience}" (context-dependent!)
"CLVS"                     → "{primaryCert}" (or remove if no cert)
"NCRA"                     → "{certBody}" (or remove)
"deposition"               → "{serviceNoun}" (when referring to the job, not the brand)
"courthouse"               → appropriate venue for your industry
"FRCP 30(b)(5)"           → remove or replace with industry regulation
```

---

## 4. Color Scheme

Each vertical gets its own color palette. Colors are defined in two places:

### 4.1 Where Colors Live

1. **`tailwind.config.js`** — Primary color scale (50–950), navy scale, box-shadow colors
2. **`src/assets/styles/tailwind.css`** — Hero gradient, CSS custom properties

### 4.2 How to Change Colors

After `factory.py create`, edit `verticals/{slug}/tailwind.config.js`:

```javascript
// Replace the primary color scale with your vertical's palette
colors: {
  primary: {
    DEFAULT: 'var(--aw-color-primary)',
    50:  '#f0fdf4',   // lightest tint (backgrounds)
    100: '#dcfce7',
    200: '#bbf7d0',
    300: '#86efac',
    400: '#4ade80',
    500: '#22c55e',   // mid-tone (text accents)
    600: '#16a34a',   // PRIMARY — buttons, links, CTAs
    700: '#15803d',   // hover states
    800: '#166534',
    900: '#14532d',
    950: '#052e16',   // darkest (text on light bg)
  },
  navy: {
    800: '#1a3d2e',   // dark card backgrounds
    900: '#153226',   // darker
    950: '#0d1f17',   // darkest (hero gradient end)
  },
},
```

Then edit `verticals/{slug}/src/assets/styles/tailwind.css`:

```css
.hero-gradient {
  background: linear-gradient(135deg, #0d1f17 0%, #1a3d2e 40%, #16a34a 100%);
}

/* Also update the second .hero-gradient in @layer components */
```

And update box-shadow accent colors:

```javascript
boxShadow: {
  'card-hover': '0 8px 24px rgba(22,163,74,0.08)',    // primary-600 as rgba
  'card-elevated': '0 4px 20px rgba(22,163,74,0.1)',
},
```

### 4.3 Recommended Color Palettes by Industry

See [Appendix A](#appendix-a-color-schemes) for complete palettes for all 24 verticals.

---

## 5. Static Assets

### 5.1 Required Assets

| Asset | Location | Size/Format | Notes |
|-------|----------|-------------|-------|
| **Logo** | `public/logo.png` | ~200x50px, PNG with transparency | Used in header nav |
| **Favicon** | `public/favicon.ico` | 32x32 ICO | Browser tab icon |
| **Favicon 16** | `public/favicon-16x16.png` | 16x16 PNG | |
| **Favicon 32** | `public/favicon-32x32.png` | 32x32 PNG | |
| **Apple Touch** | `public/apple-touch-icon.png` | 180x180 PNG | iOS home screen |
| **Android 192** | `public/android-chrome-192x192.png` | 192x192 PNG | Android home screen |
| **Android 512** | `public/android-chrome-512x512.png` | 512x512 PNG | Android splash |
| **OG Image** | `public/og-image.png` | 1200x630 PNG | Social media preview |

### 5.2 Quick Asset Generation

For MVP launch, you can use the brand name + primary color to generate assets:

```bash
# Generate a simple text-based logo with ImageMagick (if available)
convert -size 400x100 xc:transparent -font Helvetica-Bold -pointsize 36 \
  -fill "#16a34a" -gravity center -annotate 0 "StenoScout" \
  public/logo.png

# For favicons, use https://favicon.io/favicon-generator/ with:
#   Text: first letter of brand name
#   Background: primary-600 color
#   Font: any bold sans-serif
```

### 5.3 Guide PDFs (Optional)

Guide PDFs go in `public/guides/pdf/` and are referenced in `src/data/guides.json`. Each guide needs:
- A PDF file
- An entry in `guides.json` with slug, title, subtitle, description, bullets, pdfUrl, category

For initial launch, you can ship with an empty `guides.json` (`[]`) and add guides later.

### 5.4 Blog Images

Blog article images go in `public/images/blog/`. The article generation script (`generate_articles.py`) names images by slug. You can:
1. Add placeholder images before generating articles
2. Use Unsplash API to fetch relevant images per article
3. Skip images initially — articles will render without them

---

## 6. Email Setup

Each vertical needs its own Listmonk list and uses shared transactional templates.

### 6.1 Listmonk Lists

1. Log into Listmonk at `mail.firestick.io`
2. Create a new list: `{BrandName} Newsletter` (single opt-in)
3. Note the **list ID** (visible in the URL or list settings)

### 6.2 Listmonk Transactional Templates

The existing templates are shared across verticals — they use dynamic variables:
- **Magic Link Template** (ID 6): Uses `{{ .Tx.Data.siteName }}`, `{{ .Tx.Data.domain }}`
- **Guide Delivery Template** (ID 7): Uses `{{ .Tx.Data.name }}`, `{{ .Tx.Data.guide_title }}`
- **Passthrough Template** (ID 8): Renders custom HTML body

**No new templates needed per vertical** — the env vars control which brand/domain appears.

### 6.3 Email Routing

Each domain should have:
- `contact@{domain}` → `system.ops.central@gmail.com`
- `newsletter@{domain}` → `system.ops.central@gmail.com`

Set up in **Cloudflare Email Routing** for the domain.

### 6.4 Amazon SES Domain Verification

1. Add domain in AWS SES console
2. Add the 3 DKIM CNAME records to Cloudflare DNS
3. Wait for verification (~5 min)

---

## 7. Infrastructure Setup

### 7.1 Cloudflare Pages Project

```bash
# Create the project (run from verticals/{slug}/)
export CLOUDFLARE_API_KEY=...
export CLOUDFLARE_EMAIL=...
export CLOUDFLARE_ACCOUNT_ID=...

npx wrangler pages project create {slug} --production-branch main
```

### 7.2 Custom Domain

In CF dashboard: **Workers & Pages** → **{project}** → **Custom domains** → Add `{domain}` and `www.{domain}`.

Ensure the domain's DNS has a CNAME pointing to `{slug}.pages.dev`.

### 7.3 D1 Database

```bash
npx wrangler d1 create {slug}-db

# Run all migrations
for f in migrations/0*.sql; do
  npx wrangler d1 execute {slug}-db --file=$f
done
```

Then bind in the Pages project settings: **Settings** → **Functions** → **D1 database bindings** → Variable name: `LEADS_DB`, Database: `{slug}-db`

### 7.4 R2 Bucket (Optional — for photo uploads)

```bash
npx wrangler r2 bucket create {slug}-photos
```

Bind: Variable name: `PHOTOS`, Bucket: `{slug}-photos`

### 7.5 Environment Variables

Set ALL of these in **CF Pages** → **Settings** → **Environment variables** → **Production**:

| Variable | Value | Notes |
|----------|-------|-------|
| `SITE_DOMAIN` | `{domain}` | e.g., `stenoscout.com` |
| `SITE_NAME` | `{brandName}` | e.g., `StenoScout` |
| `SITE_TAGLINE` | `{tagline}` | |
| `SITE_FROM_EMAIL` | `{brandName} <noreply@{domain}>` | |
| `COMPANY_ADDRESS` | `PO Box 1547, Austin, TX 78767` | Shared across verticals |
| `LISTMONK_URL` | `https://mail.firestick.io` | Shared |
| `LISTMONK_USER` | `admin` | Shared |
| `LISTMONK_PASS` | *(secret)* | Shared |
| `LISTMONK_LIST_ID` | `{listId}` | From step 6.1 |
| `LISTMONK_MAGICLINK_TEMPLATE_ID` | `6` | Shared |
| `LISTMONK_GUIDE_TEMPLATE_ID` | `7` | Shared |
| `LISTMONK_PASSTHROUGH_TEMPLATE_ID` | `8` | Shared |
| `TURNSTILE_SECRET_KEY` | *(secret)* | From CF Turnstile dashboard |
| `HASH_SALT` | `{slug}-salt-2026` | Unique per vertical |
| `STRIPE_SECRET_KEY` | *(secret)* | From Stripe dashboard |
| `STRIPE_WEBHOOK_SECRET` | *(secret)* | From Stripe webhook config |
| `ADMIN_EMAIL` | `contact@{domain}` | |

### 7.6 Stripe Setup (Optional)

1. Create two Stripe Payment Links:
   - **Sponsored Listing** — $79/mo recurring
   - **City Pro** — $149/mo recurring
2. Add the links to the YAML config
3. Create a webhook endpoint pointing to `https://{domain}/api/stripe-webhook`
4. Note the webhook signing secret

### 7.7 Turnstile Setup

1. CF dashboard → **Turnstile** → **Add widget**
2. Set domain to `{domain}` and `*.pages.dev`
3. Copy the **Site Key** to YAML config `turnstile_sitekey`
4. Copy the **Secret Key** to CF Pages env var `TURNSTILE_SECRET_KEY`

### 7.8 Google Analytics Setup

1. Create a GA4 property for the domain
2. Copy the Measurement ID (G-XXXXXXXXXX)
3. Add to YAML config `google_analytics_id`

---

## 8. Create & Build

```bash
cd ~/tools/directory-factory
source .venv/bin/activate

# Create the vertical from template
python3 factory.py create --config configs/{slug}.yaml

# Verify it builds
python3 factory.py build --vertical {slug}
```

This copies the template, writes `vertical.json`, patches `robots.txt`/`package.json`/`site.webmanifest`, and runs `npm install`.

---

## 9. Apply Copy Deck

After `factory.py create`, apply the copy deck from Section 3. The fastest approach:

### 9.1 Automated Find-and-Replace

```bash
cd verticals/{slug}/src

# Replace profession references (review each — don't blindly replace)
# Use your IDE's multi-file search and replace with case sensitivity

# Plural first (to avoid partial matches)
find . -name "*.astro" -exec grep -l "deposition videographers" {} \;
# Then singular
find . -name "*.astro" -exec grep -l "deposition videographer" {} \;
# Then audience
find . -name "*.astro" -exec grep -l "litigation attorneys" {} \;
# Then certs
find . -name "*.astro" -exec grep -l "CLVS" {} \;
```

### 9.2 Manual Narrative Blocks

These require human writing (or Claude). Open each file and rewrite:

1. **`src/pages/about.astro`** — Hero problem statement + stakes cards
2. **`src/pages/index.astro`** — Value prop descriptions (lines 222-258)
3. **`src/pages/editorial-guidelines.astro`** — Terminology + licensing sections
4. **`src/pages/pricing.astro`** — Example listing cards

### 9.3 Verify No Stale References

```bash
# Should return zero results after copy deck is applied
grep -ri "deposition\|depohire\|CLVS\|FRCP\|litigation attorney" src/pages/ src/components/ --include="*.astro" | grep -v node_modules
```

---

## 10. Apply Color Scheme

Edit these two files per Section 4:

1. `verticals/{slug}/tailwind.config.js` — Primary scale, navy scale, box-shadows
2. `verticals/{slug}/src/assets/styles/tailwind.css` — Hero gradient (both instances)

Rebuild to verify: `python3 factory.py build --vertical {slug}`

---

## 11. Scrape & Generate Content

### 11.1 Scrape Listings

```bash
# Perplexity scraper (primary — queries by state, good economy)
PERPLEXITY_API_KEY=... python3 scripts/scrape_perplexity.py \
  --config configs/{slug}.yaml --vertical {slug}

# Then run the post-scrape pipeline
python3 scripts/clean_cities.py {slug}
GOOGLE_MAPS_API_KEY=... python3 scripts/geocode.py --vertical {slug} --missing-only
ANTHROPIC_API_KEY=... python3 scripts/enrich.py --vertical {slug}
python3 scripts/export.py --vertical {slug}
```

Or use the all-in-one (runs Google Maps + auto enrichment):
```bash
python3 factory.py scrape --vertical {slug}
```

### 11.2 Generate City Pages

```bash
ANTHROPIC_API_KEY=... python3 factory.py generate --vertical {slug} --cities
```

### 11.3 Generate Blog Articles

```bash
PERPLEXITY_API_KEY=... ANTHROPIC_API_KEY=... python3 factory.py generate --vertical {slug} --articles
```

This generates ~30 articles using Perplexity for research and Claude for writing. Topics are auto-generated from the YAML config keywords.

### 11.4 Final Build

```bash
python3 factory.py build --vertical {slug}
```

---

## 12. Deploy

```bash
# Set CF credentials
export CLOUDFLARE_API_KEY=...
export CLOUDFLARE_EMAIL=...
export CLOUDFLARE_ACCOUNT_ID=...

cd verticals/{slug}
npx wrangler pages deploy dist --project-name {slug} --branch main --commit-dirty=true
```

Or if using the factory's deploy script:
```bash
python3 factory.py deploy --vertical {slug}
```

### 12.1 Verify

- [ ] Homepage loads at `https://{domain}`
- [ ] Search works (Pagefind)
- [ ] City pages have listings
- [ ] Blog articles render
- [ ] Contact form submits (check Turnstile + leads API)
- [ ] Newsletter signup works (check Listmonk)
- [ ] Provider login page loads
- [ ] No "deposition videographer" text visible (unless that IS your vertical)

---

## 13. Post-Launch

### 13.1 Monitoring
- Check GA4 for traffic
- Check Listmonk for subscriptions
- Check D1 for leads
- Run `scripts/check_stale.py {slug}` monthly to find dead listings

### 13.2 Monthly Maintenance
- Re-scrape for new listings: `python3 factory.py scrape --vertical {slug}`
- Generate new articles as needed
- Update guide PDFs seasonally

### 13.3 Rescrape States That Failed
Some states return 0 from Perplexity (parse errors). Re-run just those:
```bash
python3 scripts/scrape_perplexity.py --config configs/{slug}.yaml --vertical {slug} --states CA,OH,VA,MN,OK
```

---

## Appendix A: Color Schemes

Recommended palettes for each vertical. Primary-600 is the main brand color used for buttons, links, and CTAs.

### Legal Verticals

| Vertical | Brand | Primary-600 | Navy-950 | Hero Gradient | Vibe |
|----------|-------|-------------|----------|---------------|------|
| **DepoHire** (deposition-videographers) | Blue | `#2563eb` | `#1a1a2e` | slate-900 → primary-900 → slate-900 | Professional trust |
| **StenoScout** (court-reporters) | Indigo | `#4f46e5` | `#1e1b4b` | indigo-950 → indigo-800 → slate-900 | Precision & authority |
| **LegalTerp** (legal-interpreters) | Teal | `#0d9488` | `#0f1f1d` | slate-900 → teal-900 → slate-900 | Communication bridge |
| **ServeCircuit** (process-servers) | Slate Blue | `#3b82f6` | `#0f172a` | slate-950 → blue-900 → slate-900 | Speed & reliability |
| **ExpertSlate** (expert-witnesses) | Purple | `#7c3aed` | `#1a0f2e` | purple-950 → purple-800 → slate-900 | Expertise & authority |
| **ForensicLedger** (forensic-accountants) | Dark Green | `#059669` | `#0a1f17` | emerald-950 → emerald-800 → slate-900 | Financial precision |
| **DocketTech** (legal-technology) | Electric Blue | `#2563eb` | `#0c1222` | blue-950 → blue-800 → slate-950 | Modern tech |

### Environmental / Inspection Verticals

| Vertical | Brand | Primary-600 | Navy-950 | Hero Gradient | Vibe |
|----------|-------|-------------|----------|---------------|------|
| **MoldRegistry** (mold-inspectors) | Green | `#16a34a` | `#0d1f17` | green-950 → green-800 → slate-900 | Safety & health |
| **RadonTrust** (radon-inspectors) | Amber | `#d97706` | `#1c1208` | amber-950 → amber-800 → slate-900 | Warning & protection |
| **SepticTrust** (septic-inspectors) | Brown/Earth | `#92400e` | `#1a1008` | amber-950 → brown-800 → slate-900 | Earth & reliability |
| **EnviVault** (environmental-consultants) | Forest | `#15803d` | `#0a1a10` | green-950 → emerald-900 → slate-900 | Nature & compliance |

### Healthcare Verticals

| Vertical | Brand | Primary-600 | Navy-950 | Hero Gradient | Vibe |
|----------|-------|-------------|----------|---------------|------|
| **BedsideImaging** (mobile-imaging) | Sky Blue | `#0284c7` | `#0c1829` | sky-950 → sky-800 → slate-900 | Clinical care |
| **ChairsideIT** (dental-it) | Cyan | `#0891b2` | `#0a1a20` | cyan-950 → cyan-800 → slate-900 | Tech + health |
| **EHRIntel** (ehr-consultants) | Blue | `#2563eb` | `#0f172a` | blue-950 → blue-800 → slate-900 | Data & systems |
| **LocumTrust** (locum-tenens) | Rose | `#e11d48` | `#1a0a10` | rose-950 → rose-800 → slate-900 | Healthcare staffing |

### Industrial / Technical Verticals

| Vertical | Brand | Primary-600 | Navy-950 | Hero Gradient | Vibe |
|----------|-------|-------------|----------|---------------|------|
| **NDTIntel** (ndt-inspectors) | Orange | `#ea580c` | `#1a1008` | orange-950 → orange-800 → slate-900 | Industrial safety |
| **SCADAIntel** (scada-consultants) | Red/Charcoal | `#dc2626` | `#1a0a0a` | red-950 → red-900 → slate-950 | Critical infrastructure |
| **AeriScout** (drone-surveyors) | Sky | `#0ea5e9` | `#0c1829` | sky-950 → sky-800 → slate-900 | Aerial tech |
| **RouteStat** (traffic-engineers) | Yellow/Dark | `#ca8a04` | `#1a1608` | yellow-950 → amber-800 → slate-900 | Infrastructure |
| **CalLedger** (calibration-services) | Gray/Steel | `#4b5563` | `#111827` | gray-900 → gray-800 → slate-950 | Precision & metrology |

### Real Estate / Property Verticals

| Vertical | Brand | Primary-600 | Navy-950 | Hero Gradient | Vibe |
|----------|-------|-------------|----------|---------------|------|
| **SurveySlate** (land-surveyors) | Olive | `#65a30d` | `#1a1f0a` | lime-950 → green-800 → slate-900 | Land & territory |
| **ChimneyAdvisor** (chimney-inspectors) | Brick Red | `#b91c1c` | `#1a0a0a` | red-950 → red-800 → slate-900 | Home safety |
| **RCMIntel** (medical-billing) | Violet | `#7c3aed` | `#1a0f2e` | violet-950 → violet-800 → slate-900 | Revenue & compliance |
| **LNCScout** (legal-nurse-consultants) | Pink/Mauve | `#db2777` | `#1a0a15` | pink-950 → pink-800 → slate-900 | Care + legal crossover |

### Tailwind Color Scale Generator

To generate a full 50–950 scale from a single hex color, use:
- [Tailwind CSS Color Generator](https://uicolors.app/create) — paste your primary-600 hex
- Or [Tailwind Shades](https://www.tailwindshades.com/) — generates the full scale

---

## Appendix B: All 24 Domains

| # | Slug | Brand | Domain | Industry | Primary Keyword |
|---|------|-------|--------|----------|-----------------|
| 1 | deposition-videographers | DepoHire | depohire.com | Legal | deposition videographer |
| 2 | court-reporters | StenoScout | stenoscout.com | Legal | court reporter |
| 3 | legal-interpreters | LegalTerp | legalterp.com | Legal | legal interpreter |
| 4 | process-servers | ServeCircuit | servecircuit.com | Legal | process server |
| 5 | expert-witnesses | ExpertSlate | expertslate.com | Legal | expert witness |
| 6 | forensic-accountants | ForensicLedger | forensicledger.com | Legal | forensic accountant |
| 7 | legal-nurse-consultants | LNCScout | lncscout.com | Legal/Healthcare | legal nurse consultant |
| 8 | mobile-imaging | BedsideImaging | bedsideimaging.com | Healthcare | mobile imaging technician |
| 9 | ehr-consultants | EHRIntel | ehrintel.com | Healthcare | EHR consultant |
| 10 | locum-tenens | LocumTrust | locumtrust.com | Healthcare | locum tenens provider |
| 11 | dental-it | ChairsideIT | chairsideit.com | Healthcare | dental IT specialist |
| 12 | medical-billing | RCMIntel | rcmintel.com | Healthcare | medical billing specialist |
| 13 | ndt-inspectors | NDTIntel | ndtintel.com | Industrial | NDT inspector |
| 14 | scada-consultants | SCADAIntel | scadaintel.com | Industrial | SCADA consultant |
| 15 | drone-surveyors | AeriScout | aeriscout.com | Industrial | drone surveyor |
| 16 | traffic-engineers | RouteStat | routestat.com | Industrial | traffic engineer |
| 17 | calibration-services | CalLedger | calledger.com | Industrial | calibration service |
| 18 | mold-inspectors | MoldRegistry | moldregistry.com | Environmental | mold inspector |
| 19 | radon-inspectors | RadonTrust | radontrust.com | Environmental | radon inspector |
| 20 | septic-inspectors | SepticTrust | septictrust.com | Environmental | septic inspector |
| 21 | environmental-consultants | EnviVault | envivault.com | Environmental | environmental consultant |
| 22 | land-surveyors | SurveySlate | surveyslate.com | Property | land surveyor |
| 23 | chimney-inspectors | ChimneyAdvisor | chimneyadvisor.com | Property | chimney inspector |
| 24 | legal-technology | DocketTech | dockettech.com | Legal | legal technology provider |

---

## Quick Start (TL;DR)

```bash
# 1. Create YAML config (copy from configs/deposition-videographers.yaml and edit)
cp configs/deposition-videographers.yaml configs/{slug}.yaml
# Edit with your vertical's details

# 2. Create vertical
python3 factory.py create --config configs/{slug}.yaml

# 3. Apply copy deck (find-and-replace profession + audience references)
# See Section 3 and Section 9

# 4. Apply color scheme (edit tailwind.config.js + tailwind.css)
# See Section 4 and Appendix A

# 5. Replace static assets (logo, favicons, OG image)
# See Section 5

# 6. Set up infra (CF Pages project, D1, env vars, email, Stripe, Turnstile, GA)
# See Sections 6-7

# 7. Scrape + generate content
python3 factory.py scrape --vertical {slug}
python3 factory.py generate --vertical {slug}

# 8. Build + deploy
python3 factory.py build --vertical {slug}
python3 factory.py deploy --vertical {slug}
```

Total time for a new vertical (after first time): ~2 hours hands-on + scraping/generation wait time.
