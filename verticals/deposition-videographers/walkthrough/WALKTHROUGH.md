# DepoHire — Product Walkthrough & Business Overview

**URL:** [depohire.com](https://depohire.com)
**Version:** March 2026
**Status:** Live, revenue-ready

---

## Table of Contents

1. [What DepoHire Is](#what-depohire-is)
2. [Market Opportunity](#market-opportunity)
3. [User Journey — Attorney (Buyer)](#user-journey--attorney-buyer)
4. [User Journey — Provider (Seller)](#user-journey--provider-seller)
5. [Revenue Model](#revenue-model)
6. [Page-by-Page Walkthrough](#page-by-page-walkthrough)
7. [Lead Capture System](#lead-capture-system)
8. [Data Pipeline & Coverage](#data-pipeline--coverage)
9. [Technical Architecture](#technical-architecture)
10. [SEO & Content Strategy](#seo--content-strategy)
11. [Scalability — Directory Factory](#scalability--directory-factory)
12. [Metrics & KPIs to Track](#metrics--kpis-to-track)
13. [Roadmap](#roadmap)

---

## What DepoHire Is

DepoHire is a vertical directory connecting **litigation attorneys** with **deposition videographers** across the United States. It solves a real problem: attorneys have no reliable, centralized way to find qualified, local deposition videographers — a professional they need regularly for trial preparation.

Think of it as "Thumbtack for deposition videographers" — but built specifically for the legal industry, with CLVS certification verification, structured quote requests, and content designed for attorneys who need to make a hiring decision quickly.

**Key stats:**
- 1,089 verified provider listings
- 67 cities across 48 states
- 96% of listings have a contactable email or phone number
- 30 SEO-optimized blog articles
- Fully static site (zero hosting cost, instant page loads)

---

## Market Opportunity

Deposition videography is a $2–4B annual market in the US. Every civil litigation case that goes to trial needs deposition video — and most law firms book 10–50 depositions per year.

**Why there's no good directory today:**
- Google Maps returns generic "video production" companies
- Legal directories (Martindale, Avvo) don't cover videographers
- Most firms rely on word-of-mouth or court reporter referrals
- No directory verifies CLVS certification (the NCRA gold standard)

**Our moat:**
- First mover in this specific niche
- Real, verified provider data (not scraped listings with no contact info)
- CLVS certification surfaced on every listing
- Domain authority from 30+ expert articles targeting long-tail legal keywords
- Template system that lets us replicate to adjacent legal service niches in days

---

## User Journey — Attorney (Buyer)

The attorney journey is designed for speed and trust. An attorney with an upcoming deposition should be able to find and contact a qualified local videographer in under 2 minutes.

### Flow Diagram

```
Google Search / Direct Visit
         │
         ▼
    ┌─────────┐     ZIP Code     ┌──────────────┐
    │ Homepage │───────or────────▶│ Nearest Cities│
    │          │   City Name      │   Results     │
    └────┬─────┘                  └──────┬────────┘
         │                               │
         ▼                               ▼
    ┌──────────┐                  ┌──────────────┐
    │City Page │◀─────────────────│ State Page   │
    │(listings)│                  │ (all cities) │
    └────┬─────┘                  └──────────────┘
         │
    ┌────┴──────────────────┐
    │                       │
    ▼                       ▼
┌──────────┐        ┌──────────────┐
│ Single   │        │ Multi-Quote  │
│ Listing  │        │ (select 2-5) │
│ Detail   │        │              │
└────┬─────┘        └──────┬───────┘
     │                     │
     ▼                     ▼
┌──────────┐        ┌──────────────┐
│ Quote    │        │ Batch Quote  │
│ Request  │        │ Modal        │
│ Form     │        │              │
└────┬─────┘        └──────┬───────┘
     │                     │
     └──────────┬──────────┘
                ▼
         ┌─────────────┐
         │ Lead Capture │
         │ API          │
         │ (saves lead, │
         │  emails      │
         │  provider +  │
         │  attorney)   │
         └─────────────┘
```

### Key Decision Points

1. **Search** — Attorney types a city name or zip code. Zip codes are geocoded and matched to the nearest cities with providers, showing distance in miles.

2. **Compare** — City page shows all providers with filters (Has Reviews, CLVS Certified, 4+ Stars) and sort options (Rating, Most Reviews, Name). Listings show certifications, services, sentiment badges, and review highlights.

3. **Select** — Attorney can click into a single listing for detail, OR check 2–5 providers and click "Request Quotes" to contact multiple at once.

4. **Convert** — Quote request form captures name, email, phone, case details. The request is sent to the provider(s) via email, and the attorney receives a confirmation. Every lead is saved to our database.

---

## User Journey — Provider (Seller)

Providers are the paying customers. Their journey is about discovering they're listed, seeing the value, and upgrading.

### Flow Diagram

```
   Receives quote request email
   from DepoHire
         │
         ▼
   Visits their listing page
   (link in email footer)
         │
         ▼
   Sees "Claim Listing" banner
         │
         ▼
   Clicks "List Your Business"
   (nav CTA) or "Get Featured"
   (ad slot on listing page)
         │
         ▼
   ┌──────────────┐
   │ Advertise    │──▶ Application form
   │ Page         │    (name, business,
   └──────┬───────┘     email, city, plan)
          │
          ▼
   ┌──────────────┐
   │ Pricing Page │──▶ 3 tiers:
   │              │    Free / $79 / $149
   └──────────────┘
```

### Provider Value Proposition

- **Free listing:** Basic presence, appears in search results
- **Featured ($79/mo):** Gold badge, priority placement, appears above free listings
- **City Pro ($149/mo):** Featured + exclusive city guide mention + newsletter sponsorship

---

## Revenue Model

### Primary Revenue: Featured Listings

| Tier | Price | What Provider Gets |
|------|-------|--------------------|
| Basic | Free | Standard listing with contact info |
| Featured | $79/mo | Gold badge, priority sort, top of city page |
| City Pro | $149/mo | Featured + city guide mention + newsletter ad |

**Revenue math (conservative):**
- 67 cities × 2 Featured listings/city = 134 Featured slots
- At 20% fill rate = 27 paying providers
- 27 × $79/mo = **$2,133/mo ($25,596/yr)**

**Revenue math (moderate):**
- 134 Featured + 67 City Pro slots = 201 total slots
- At 40% fill rate = 80 paying providers
- Mix of $79 and $149 = avg $100/mo
- 80 × $100/mo = **$8,000/mo ($96,000/yr)**

### Secondary Revenue: Add-Ons

| Add-On | Price | Description |
|--------|-------|-------------|
| Extra City | $49/mo | Appear as Featured in an additional city |
| Newsletter Sponsorship | $99/mo | Banner in city newsletter |
| Guide Mention | $149/mo | Named in city-specific blog articles |

### Tertiary Revenue: Lead Data

Every quote request generates a lead with attorney name, email, case details, and which providers they contacted. This data has value for:
- Aggregate market intelligence (which cities have most demand)
- Provider analytics (conversion rates per listing)
- Future premium features (analytics dashboard for providers)

### Cost Structure

| Item | Monthly Cost |
|------|-------------|
| Cloudflare Pages hosting | $0 |
| Domain (depohire.com) | ~$1/mo amortized |
| VPS (shared with other services) | ~$5/mo allocated |
| Amazon SES email | < $1/mo |
| Google Maps API | $0 (within free tier) |
| Perplexity API (data enrichment) | < $1/mo |
| **Total operating cost** | **~$7/mo** |

**Margin: 99%+ at any revenue level.**

---

## Page-by-Page Walkthrough

### 1. Homepage (`/`)

![Homepage](screenshots/01-homepage.png)

The homepage is designed around a single action: **find a provider near you.**

**Elements (top to bottom):**
- **Nav bar:** Find Providers | Browse by State | Blog | About | [List Your Business]
- **Trust signal:** "FREE TO SEARCH · NO ACCOUNT NEEDED"
- **Headline:** "A bad deposition videographer can sink your case." — fear-based hook that speaks directly to the attorney's risk
- **Subheadline:** Positions DepoHire as the only directory for litigation attorneys, emphasizes CLVS certification
- **Smart Search:** Accepts city names OR zip codes. Zip codes are geocoded and show nearest cities with distance
- **Stats banner:** 48+ states, 67+ cities, 1089+ providers, 100% free
- **3 Benefit cards:** CLVS certification, 2-minute quotes, no travel surcharges
- **US State Map:** Interactive SVG choropleth showing provider density by state
- **City Grid:** Top 25 cities by provider count, with state and count
- **State List:** All 48 states with city and listing counts

**SEO:** Title includes current year, Organization schema, SearchAction schema.

---

### 2. Smart Search — Zip Code

![Zip Code Search](screenshots/02-homepage-search-zip.png)

When a user types a 5-digit zip code (e.g., "90210"), the search bar:
1. Calls the free zippopotam.us API to geocode the zip
2. Calculates haversine distance to all 67 cities with providers
3. Shows the nearest cities sorted by distance with provider counts and miles

This is critical for attorneys who know their courthouse zip code but may not know which metro area has providers.

---

### 3. City Page (`/{city}/`)

![City Page](screenshots/03-city-page-new-york.png)

The city page is the highest-value page in the funnel. Most organic traffic will land here via searches like "deposition videographer New York."

**Elements:**
- **Breadcrumbs:** Home > State > City (structured data)
- **Hero image:** City skyline with credit attribution
- **Headline:** "Hiring a deposition videographer in New York?"
- **Subtitle:** Provider count, verified badge, value proposition
- **Metrics bar:** Provider count, "Verified listings" badge, last updated date
- **3 Stat cards:**
  - $100–300 travel cost warning (red) — creates urgency to hire local
  - 2–3x faster turnaround (green) — benefits of local provider
  - CLVS certification (amber) — what to look for
- **Leaflet map:** Interactive map with pins for each provider
- **Ad slot:** "Get Featured" CTA for providers
- **Filter bar:** Has Reviews, CLVS Certified, 4+ Stars filters + Sort dropdown
- **Listing grid:** 2-column card layout with all providers
- **FAQ accordion:** City-specific FAQs with FAQ schema markup
- **Related blog content:** Links to relevant articles
- **Nearby cities:** 5 nearest cities with provider counts

---

### 4. City Page — Filtering

![Filters Active](screenshots/04-city-page-filters.png)

Filter pills toggle instantly (client-side JavaScript, no page reload). Active filters show highlighted in blue. The counter updates to show "Showing X of Y providers."

**Available filters:**
- **Has Reviews** — Shows only providers with at least 1 review
- **CLVS Certified** — Shows only providers with CLVS certification
- **4+ Stars** — Shows only providers rated 4.0 or higher

**Sort options:**
- Default (featured first, then by rating)
- Rating (high to low)
- Most Reviews
- Name (A–Z)

---

### 5. City Page — Multi-Quote Selection

![Multi-Select](screenshots/05-city-page-multi-select.png)

Each listing card has a "Compare" checkbox. When 1–5 providers are selected, a floating bottom bar appears:

**"3 providers selected — [Clear] [Request Quotes]"**

Clicking "Request Quotes" opens a modal with:
- List of selected providers
- Quote request form (name, email, phone, case details)
- Single submit sends to ALL selected providers
- Attorney receives one confirmation email listing all providers contacted

This is the **Thumbtack/HomeAdvisor model** — the most valuable interaction because it generates multiple leads from a single form submission.

---

### 6. Listing Detail Page (`/listing/{slug}/`)

![Listing Detail](screenshots/06-listing-detail.png)

Individual provider page with all available data:

- **Header:** Provider name, address, star rating, review count
- **Map:** Leaflet map centered on the provider's location
- **Certifications & services:** Tagged badges (CLVS, deposition videography, etc.)
- **Sentiment badge:** AI-generated sentiment analysis from reviews
- **Review highlights:** AI-extracted positive keywords and quotes
- **"Claim Listing" banner:** CTA for unclaimed providers to take ownership
- **Contact form:** Direct quote request form (see Lead Capture section)
- **Ad slot:** "Get Featured" CTA

**Schema markup:** Full LocalBusiness structured data with AggregateRating, credentials, services, and geo coordinates.

---

### 7. Quote Request Form (Lead Capture)

![Contact Form](screenshots/07-listing-contact-form.png)

The contact form is the primary conversion point. Every submission:
1. Saves the lead to our database (attorney name, email, phone, case details, provider, city)
2. Sends a branded email to the provider with the attorney's details
3. Sends a confirmation email to the attorney
4. Notifies the site owner

**Fields:**
- Your Name (required)
- Email (required)
- Phone (optional)
- Case Details (free text — date, location, proceeding type)

**Anti-spam:** Honeypot field, rate limiting (5 requests per 10 minutes per IP).

---

### 8. Search Page (`/search/`)

![Search Page](screenshots/08-search-page.png)

Full-text search powered by Pagefind (client-side search index). Indexes all listing pages and blog content. Search results show page titles with highlighted matching text.

Works with View Transitions (client-side navigation) — the search index loads dynamically when navigating to this page.

---

### 9. Blog Index (`/blog/`)

![Blog Index](screenshots/09-blog-index.png)

30 SEO-optimized articles organized in a hub-and-spoke content architecture. Featured "pillar" article at top, 2-column card grid below.

**Content clusters:**
- Complete guide to deposition videographers (pillar)
- CLVS certification guide
- Cost guides by city
- Equipment and technology
- Legal compliance and ethics
- Remote deposition video
- State-specific regulations

Each article targets long-tail keywords that attorneys search for.

---

### 10. Blog Post (`/blog/{slug}/`)

![Blog Post](screenshots/10-blog-post.png)

Individual articles with:
- Author attribution (builds E-E-A-T for Google)
- Reading time estimate
- Hub/spoke breadcrumb linking
- Prose typography with callout boxes
- BlogPosting schema markup

---

### 11. Blog — City Search CTA

![Blog City CTA](screenshots/11-blog-city-cta.png)

Every blog post ends with a "Find a deposition videographer near you" section. Features:
- **Search input:** Accepts city names or zip codes (same smart search as homepage)
- **Popular city pills:** Top 6 cities by provider count as quick-access links
- **"All Cities" button:** Links to the states/all browsing page

This converts blog readers (informational intent) into directory users (transactional intent).

---

### 12. All States Page (`/states/all/`)

![All States](screenshots/12-states-all.png)

Browsing page showing all 48 states with provider coverage. Each state card shows:
- State name
- Number of cities covered
- Total listing count
- Link to state detail page

---

### 13. State Page (`/states/{state}/`)

![State Page](screenshots/13-state-page.png)

State-level aggregation showing all cities within that state. Each city card links to the city page with listing count. Helps attorneys who need a videographer "somewhere in California" narrow down to specific metro areas.

---

### 14. Pricing Page (`/pricing/`)

![Pricing Page](screenshots/14-pricing.png)

Three-tier pricing designed to convert providers:

| | Basic | Featured | City Pro |
|---|---|---|---|
| **Price** | Free | $79/mo | $149/mo |
| Listed in directory | Yes | Yes | Yes |
| Contact info shown | Yes | Yes | Yes |
| Featured badge | — | Yes | Yes |
| Priority placement | — | Yes | Yes |
| City guide mention | — | — | Yes |
| Newsletter sponsorship | — | — | Yes |

Includes:
- ROI section ("What Featured looks like" comparison)
- FAQ accordion
- "Get Started" CTA linking to the Advertise application form

---

### 15. Advertise Page (`/advertise/`)

![Advertise Page](screenshots/15-advertise.png)

Application form for providers wanting to upgrade. Captures:
- Provider name and business name
- Email and phone
- City they serve
- Which plan interests them

Also shows add-on pricing ($49/extra city, $99/newsletter, $149/guide mention).

Form action sends to the site's contact email for manual processing initially. Can be upgraded to automated Stripe checkout later.

---

### 16. About Page (`/about/`)

![About Page](screenshots/16-about.png)

Trust and authority page. Explains:
- Why the directory exists
- Editorial standards
- How listings are verified
- Team/author information

Required for Google's E-E-A-T (Experience, Expertise, Authoritativeness, Trustworthiness) signals.

---

### 17. Statistics Page (`/statistics/`)

![Statistics Page](screenshots/17-statistics.png)

Data dashboard showing directory-wide metrics:
- Total providers, cities, states
- Coverage by state
- Average ratings
- Certification breakdown

Serves dual purpose: trust signal for attorneys ("this is a serious directory") and SEO content (targets "deposition videographer statistics" queries).

---

### 18. Privacy Policy (`/privacy/`)

![Privacy Page](screenshots/18-privacy.png)

Standard privacy policy. Required for legal compliance and Google's quality guidelines.

---

## Lead Capture System

### Architecture

```
┌─────────────────┐     POST /api/leads      ┌──────────────────┐
│ Static Site      │────────────────────────▶  │ Lead Capture API │
│ (Cloudflare      │                           │ (FastAPI on VPS) │
│  Pages)          │◀────────────────────────  │                  │
│                  │     JSON response         │ Port 8770        │
└─────────────────┘                            │ api.depohire.com │
                                               └────────┬─────────┘
                                                        │
                              ┌──────────────────────────┼──────────────────┐
                              │                          │                  │
                              ▼                          ▼                  ▼
                     ┌──────────────┐          ┌──────────────┐   ┌──────────────┐
                     │ SQLite       │          │ Amazon SES   │   │ Notification │
                     │ leads.db     │          │ (SMTP)       │   │ Email        │
                     │              │          │              │   │ (to owner)   │
                     │ - leads      │          │ Sends to:    │   │              │
                     │ - providers  │          │ 1. Provider  │   └──────────────┘
                     └──────────────┘          │ 2. Attorney  │
                                               └──────────────┘
```

### Database Schema

```sql
leads (
  id, attorney_name, attorney_email, attorney_phone,
  case_details, city, source_ip, created_at
)

lead_providers (
  id, lead_id, provider_name, provider_email,
  provider_slug, email_sent, created_at
)
```

### Email Templates

**To Provider:** Branded DepoHire email with attorney's name, email, phone, city, and case details. Reply-To is set to the attorney's email so the provider can respond directly.

**To Attorney:** Confirmation listing which providers were contacted. Sets expectation of 1 business day response time.

**To Owner:** Notification with lead number, attorney name, city, and provider count for real-time monitoring.

### Security

- **Rate limiting:** 5 requests per IP per 10-minute window
- **Honeypot field:** Hidden form field that bots fill — submissions with it filled are silently accepted but discarded
- **CORS:** Only allows requests from depohire.com
- **Input validation:** Pydantic models with email validation

---

## Data Pipeline & Coverage

### How Listings Are Sourced

```
Perplexity API (sonar model)     Google Maps Places API
  queries by state                 Place Details
         │                                │
         ▼                                ▼
    ┌──────────┐                   ┌──────────────┐
    │ Raw      │                   │ Phone        │
    │ listings │                   │ Website      │
    │ (name,   │                   │ Rating       │
    │  city,   │                   │ Hours        │
    │  address)│                   │ Maps URL     │
    └────┬─────┘                   │ Status       │
         │                         └──────┬───────┘
         │            ┌───────────────────┘
         ▼            ▼
    ┌──────────────────────┐
    │ pipeline.db (SQLite) │
    └──────────┬───────────┘
               │
    ┌──────────┼──────────────────┐
    │          │                  │
    ▼          ▼                  ▼
Website     Perplexity          Playwright
Scraper     Contact Search      JS Rendering
(httpx +    (sonar API,         (headless
 BS4)        batched)            Chromium)
    │          │                  │
    └──────────┼──────────────────┘
               ▼
    ┌──────────────────────┐
    │ Enriched Data        │
    │ - Email (66%)        │
    │ - Phone (93%)        │
    │ - Contact form (44%) │
    │ - LinkedIn (12%)     │
    │ - Facebook (17%)     │
    └──────────┬───────────┘
               │
               ▼
    ┌──────────────────────┐
    │ export.py            │
    │ SQLite → JSON files  │
    │ per city             │
    └──────────┬───────────┘
               │
               ▼
    ┌──────────────────────┐
    │ Astro Static Build   │
    │ 1,243 HTML pages     │
    │ Pagefind search      │
    └──────────┬───────────┘
               │
               ▼
    ┌──────────────────────┐
    │ Cloudflare Pages     │
    │ Global CDN           │
    │ depohire.com         │
    └──────────────────────┘
```

### Current Coverage

| Metric | Count | Coverage |
|--------|-------|----------|
| Total listings | 1,089 | — |
| With phone | 1,014 | 93% |
| With email | 725 | 66% |
| With website | 1,018 | 93% |
| With contact form URL | 490 | 44% |
| With LinkedIn | 138 | 12% |
| With Facebook | 188 | 17% |
| With Google Maps URL | 829 | 76% |
| Contactable (email or phone) | 1,054 | 96% |
| Cities covered | 67 | — |
| States covered | 48 | — |

### Enrichment Cost

| Method | Cost |
|--------|------|
| Google Maps Place Details | $6.63 (covered by $200/mo free credit) |
| Perplexity API (contact search) | $0.21 |
| Website scraping (httpx) | $0 |
| Playwright JS rendering | $0 |
| **Total data enrichment cost** | **$0.21** |

---

## Technical Architecture

### Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Frontend | Astro 5 | Static site generator |
| Styling | Tailwind CSS | Utility-first CSS |
| Search | Pagefind | Client-side search index |
| Maps | Leaflet + OpenStreetMap | Interactive maps |
| API | FastAPI (Python) | Lead capture |
| Database | SQLite | Pipeline data + leads |
| Email | Amazon SES | Transactional email |
| Hosting | Cloudflare Pages | Static site CDN |
| DNS/SSL | Cloudflare | DNS, SSL, caching |
| VPS | Hetzner (Ubuntu 24.04) | API + pipeline scripts |

### Performance

- **Build time:** ~15 seconds for 1,243 pages
- **Page load:** < 1 second (static HTML from CDN edge)
- **Lighthouse score:** 95+ performance
- **Monthly hosting cost:** $0 (Cloudflare Pages free tier)

### Key Files

```
verticals/deposition-videographers/
├── src/
│   ├── pages/
│   │   ├── index.astro              # Homepage
│   │   ├── [city].astro             # City pages (67)
│   │   ├── listing/[slug].astro     # Listing detail (1,089)
│   │   ├── states/[state].astro     # State pages (48+1)
│   │   ├── blog/[...slug].astro     # Blog posts (30)
│   │   ├── search.astro             # Pagefind search
│   │   ├── pricing.astro            # Pricing tiers
│   │   ├── advertise.astro          # Provider application
│   │   ├── about.astro              # Trust page
│   │   ├── statistics.astro         # Data dashboard
│   │   └── privacy.astro            # Privacy policy
│   ├── components/directory/
│   │   ├── SearchBar.astro          # Smart search (city + zip)
│   │   ├── ListingCard.astro        # Provider card with checkbox
│   │   ├── ListingFilters.astro     # Filter/sort controls
│   │   ├── ContactForm.astro        # API-backed quote form
│   │   ├── MultiQuoteBar.astro      # Multi-select + modal
│   │   ├── StickyCTA.astro          # Scroll-triggered CTA
│   │   ├── LeafletMap.astro         # Interactive map
│   │   ├── UsStateMap.astro         # SVG choropleth
│   │   └── ...                      # 15+ more components
│   ├── data/
│   │   ├── cities.json              # 67 cities with lat/lng
│   │   ├── listings/*.json          # Per-city listing data
│   │   └── us-states-paths.json     # SVG map paths
│   └── content/
│       ├── blog/                    # 30 MDX articles
│       └── cities/                  # City-specific content
├── pipeline.db                      # SQLite data pipeline
└── vertical.json                    # Site configuration

scripts/
├── scrape_perplexity.py             # Initial data sourcing
├── enrich_places.py                 # Google Maps enrichment
├── enrich_websites.py               # Website scraping (httpx)
├── enrich_playwright.py             # JS-rendered scraping
├── enrich_perplexity.py             # AI contact search
├── enrich_emails_smtp.py            # SMTP verification
├── export.py                        # SQLite → JSON export
└── generate_articles.py             # AI content generation

~/tools/depohire-api/
├── main.py                          # FastAPI lead capture
├── leads.db                         # Lead database
└── .env                             # SES SMTP credentials
```

---

## SEO & Content Strategy

### On-Page SEO

- **Title tags:** Include current year, city name, and primary keyword
- **Meta descriptions:** City-specific with provider count
- **Structured data:**
  - Organization schema (site-wide)
  - LocalBusiness schema (listing pages)
  - ItemList schema (city pages)
  - BlogPosting schema (articles)
  - FAQPage schema (city page FAQs)
  - SearchAction schema (homepage)
- **Internal linking:**
  - Hub/spoke blog architecture
  - City → nearby cities cross-links
  - Blog → city CTAs
  - State → city → listing breadcrumbs
- **E-E-A-T signals:**
  - About page with editorial team
  - Author attribution on articles
  - Editorial guidelines page
  - Privacy policy

### Content Strategy

30 articles in 10 topic clusters:

1. **Pillar:** Complete Guide to Deposition Videographers
2. **Cost & Pricing:** How much does it cost, city-specific cost guides
3. **Certification:** CLVS guide, what certifications matter
4. **Technology:** Equipment, remote depositions, AI in legal video
5. **Legal Compliance:** Federal rules, state regulations, evidence admissibility
6. **Hiring Guide:** What to look for, red flags, interview questions
7. **Industry Trends:** Market statistics, emerging tech
8. **Case Types:** Medical malpractice, corporate litigation, family law
9. **Comparison:** In-house vs outsourced, videographer vs court reporter
10. **Local Guides:** City-specific deposition videography guides

Each article targets 1–3 long-tail keywords with monthly search volume of 100–1,000.

---

## Scalability — Directory Factory

DepoHire is not a one-off product. It was built using **Directory Factory** — a template-once, deploy-many system for niche directory sites.

### How It Works

```bash
# Create a new vertical from config
python3 factory.py create --config configs/new-vertical.yaml

# Scrape listings
python3 factory.py scrape --vertical new-vertical

# Generate content
python3 factory.py generate --vertical new-vertical

# Build and deploy
python3 factory.py build --vertical new-vertical
python3 factory.py deploy --vertical new-vertical
```

### Ready-to-Launch Verticals (24 domains registered)

| Domain | Niche | Market |
|--------|-------|--------|
| depohire.com | Deposition videographers | **LIVE** |
| stenoscout.com | Court stenographers | Legal |
| legalterp.com | Legal interpreters | Legal |
| servecircuit.com | Process servers | Legal |
| expertslate.com | Expert witnesses | Legal |
| forensicledger.com | Forensic accountants | Legal |
| lncscout.com | Legal nurse consultants | Legal/Medical |
| bedsideimaging.com | Mobile X-ray/imaging | Medical |
| routestat.com | Route optimization | Logistics |
| aeriscout.com | Drone inspection | Industrial |
| envivault.com | Environmental testing | Environmental |
| ndtintel.com | Non-destructive testing | Industrial |
| calledger.com | Calibration services | Industrial |
| chairsideit.com | Dental IT services | Medical |
| dockettech.com | Legal tech services | Legal |
| scadaintel.com | SCADA/ICS security | Industrial |
| ehrintel.com | EHR consulting | Medical |
| moldregistry.com | Mold inspectors | Home services |
| radontrust.com | Radon testing | Home services |
| septictrust.com | Septic inspectors | Home services |
| surveyslate.com | Land surveyors | Professional |
| chimneyadvisor.com | Chimney inspection | Home services |
| rcmintel.com | RCM billing services | Medical |
| locumtrust.com | Locum tenens staffing | Medical |

Each vertical shares the same template, pipeline scripts, and deployment infrastructure. Time to launch a new vertical: **~2 days** (scraping + content generation + review).

---

## Metrics & KPIs to Track

### Traffic KPIs
- Organic search impressions and clicks (Google Search Console)
- Page views per city page
- Search-to-city-page conversion rate
- Blog traffic → directory conversion rate

### Lead KPIs
- Quote requests per day/week/month
- Single vs multi-quote ratio
- Leads by city (demand mapping)
- Provider email delivery rate
- Attorney-to-provider response rate

### Revenue KPIs
- Featured listing conversion rate (from inbound provider interest)
- Revenue per city
- Provider churn rate
- Average revenue per provider
- LTV:CAC ratio

### Data Quality KPIs
- Email coverage percentage
- Phone coverage percentage
- Listings with reviews
- CLVS certification coverage
- Stale/closed business rate

---

## Roadmap

### Near-Term (Q2 2026)

- [ ] **Stripe integration** — automated Featured listing checkout
- [ ] **Provider dashboard** — login, edit listing, view lead analytics
- [ ] **Review collection** — email past leads asking for reviews
- [ ] **City newsletters** — monthly email to local attorneys (Listmonk integration)
- [ ] **Google Ads** — test paid acquisition for high-value cities

### Medium-Term (Q3–Q4 2026)

- [ ] **Launch 5 more verticals** — stenoscout, legalterp, servecircuit, expertslate, forensicledger
- [ ] **Provider analytics dashboard** — how many views, quote requests, competitor comparison
- [ ] **Instant booking** — calendar integration for providers who want it
- [ ] **Mobile app** (PWA) — save providers, get notified of quotes
- [ ] **Affiliate partnerships** — equipment suppliers, insurance, continuing education

### Long-Term (2027+)

- [ ] **AI-powered matching** — "Tell us about your case, we'll recommend providers"
- [ ] **Verified reviews** — require proof of engagement to leave a review
- [ ] **Multi-language support** — Spanish market for legal interpreters vertical
- [ ] **Marketplace model** — handle payments between attorneys and providers (take %)
- [ ] **Exit opportunity** — directory portfolio acquisition by legal tech company

---

*Document generated March 2026. Screenshots reflect the live production site at depohire.com.*
