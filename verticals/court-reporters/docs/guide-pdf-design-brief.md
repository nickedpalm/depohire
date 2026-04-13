# PDF Guide Design Brief — StenoScout Lead Magnets

**Project:** 3 downloadable PDF guides for stenoscout.com
**Brand:** StenoScout — The most comprehensive directory of court reporters and stenographers in the United States
**Audience:** Litigation attorneys, paralegals, and legal operations managers at mid-size to large law firms
**Tone:** Professional, authoritative, data-driven. Think McKinsey report meets legal practice guide. No fluff, no marketing speak. These readers bill $300-800/hr and value density.

---

## Brand Guidelines

### Colors
| Token | Hex | Usage |
|-------|-----|-------|
| Primary 600 | `#4f46e5` | Headings, links, CTA buttons, accent bars |
| Primary 50 | `#f5f5fa` | Light backgrounds, callout boxes |
| Primary 100 | `#e7e6f4` | Table header backgrounds |
| Navy 800 | `#25234d` | Cover page background, footer bars, hero sections |
| Navy 950 | `#141320` | Body text (dark) |
| Emerald 600 | `#059669` | Checkmarks, "verified" badges, positive callouts |
| Amber 500 | `#f59e0b` | Star ratings, warning callouts |
| Red 600 | `#dc2626` | Red flag callouts, critical warnings |
| Gray 100 | `#f3f4f6` | Alternating table row stripes |
| Gray 400 | `#9ca3af` | Secondary text, captions |
| White | `#ffffff` | Page background, card backgrounds |

### Typography
| Element | Font | Weight | Size (approx) |
|---------|------|--------|---------------|
| Cover title | Inter | 800 (ExtraBold) | 36-42pt |
| Section heading (H2) | Inter | 700 (Bold) | 20-24pt |
| Sub-heading (H3) | Inter | 600 (SemiBold) | 16-18pt |
| Body text | Inter | 400 (Regular) | 10-11pt |
| Table text | Inter | 400 | 9-10pt |
| Captions/footnotes | Inter | 400 | 8pt |
| Callout text | Inter | 500 (Medium) | 10pt |

### Logo
- Text-only wordmark: "Steno" in Inter ExtraBold white + "Scout" in Inter ExtraBold Primary 600 (#4f46e5)
- On dark backgrounds: both words in white with "Scout" in Primary 400 (#6760dc)
- Wordmark assets available at `brand_assets/stenoscout/`

### Recurring Design Elements
- **Callout boxes:** Rounded corners (8-12px), left border accent (3-4px solid Primary 600), light background (Primary 50)
- **Pro Tip boxes:** Same as callout but with emerald left border and emerald-50 background
- **Warning/Red Flag boxes:** Red left border, red-50 background
- **Tables:** Header row in Primary 100 with Primary 700 text. Alternating gray-100 stripes. No heavy borders — use subtle 1px gray-200 lines.
- **Checkmark lists:** Emerald 600 checkmarks, body text
- **Page footer:** Gray bar with "stenoscout.com" left-aligned, page number right-aligned
- **Cover footer:** "stenoscout.com | contact@stenoscout.com"

---

## File Delivery Specs

| Spec | Value |
|------|-------|
| Format | PDF (print-quality, with bookmarks/TOC) |
| Page size | US Letter (8.5" x 11") |
| Margins | 0.75" all sides (1" top on first page of each section) |
| Bleed | Not needed (digital-only distribution) |
| File names | `court-reporter-rate-guide-2026.pdf`, `remote-court-reporting-setup-checklist.pdf`, `court-reporter-certification-vetting-guide.pdf` |
| Delivery location | `public/guides/pdf/` in the project repo |
| Max file size | Under 5MB each (these are served from Cloudflare CDN) |

---

## PDF 1: Court Reporter Rate Guide 2026

**File:** `court-reporter-rate-guide-2026.pdf`
**Target length:** 7-9 pages
**Category badge:** "Pricing" (emerald-50 bg, emerald-700 text)

### Page 1 — Cover

- Full-bleed Navy 800 background
- "StenoScout" top-left in white (with "Scout" in lighter indigo)
- Title: **"Court Reporter Rate Guide 2026"**
- Subtitle: *"Real pricing data — per-page rates, appearance fees, and hidden costs across all 50 states"*
- 4 bullet points (white checkmarks):
  - Federal and private per-page transcript rates
  - Rates by metro area and service level
  - Hidden fees to watch for (expedited, realtime, copies, exhibits)
  - How to negotiate better rates with agencies and freelancers
- Footer: "stenoscout.com | Free download — Updated 2026"

### Page 2 — How Court Reporter Billing Works

**Intro paragraph:**
Court reporter billing is multi-layered. Unlike a flat hourly rate, invoices typically combine an appearance fee, per-page transcript charges, and various add-ons. Understanding the structure is the first step to controlling costs.

**Billing Structure Overview (visual breakdown):**

| Component | Description | Typical Range |
|---|---|---|
| Appearance fee (per diem) | Charged for showing up — half-day or full-day | $100–$500 |
| Per-page transcript fee | The core charge, billed on the final certified transcript | $3.00–$7.50/page |
| Copy charges | Additional parties requesting copies | $0.75–$1.45/page |
| Add-ons | Expedited delivery, realtime feed, rough drafts, exhibits | Varies widely |

**Callout box:**
> **Quick Budget Reference**
> - Short deposition (1-2 hours, ~75 pages): $300–$700
> - Half-day deposition (3-4 hours, ~150 pages): $500–$1,200
> - Full-day deposition (5-7 hours, ~300 pages): $900–$2,500
> - Full video deposition with transcript, sync, and room: $1,000–$3,000+

### Page 3 — Federal Maximum Transcript Rates (JCUS)

**Title:** "Federal Court Transcript Rate Caps — Your Benchmark"

**Intro text:** The Judicial Conference of the United States (JCUS) sets maximum per-page rates for federal proceedings. These serve as the national pricing benchmark. Private/freelance rates often exceed these caps.

**Full-width table:**

| Delivery Speed | Original (per page) | First Copy | Additional Copies |
|---|---|---|---|
| 30-Day (Ordinary) | $4.40 | $1.10 | $0.75 |
| 14-Day | $5.10 | $1.10 | $0.75 |
| 7-Day (Expedited) | $5.85 | $1.10 | $0.75 |
| 3-Day | $6.55 | $1.30 | $0.90 |
| Next-Day (Daily) | $7.30 | $1.45 | $1.10 |
| 2-Hour (Hourly/Same-Day) | $8.70 | $1.45 | $1.10 |

**Realtime Feed Rates (Federal):**

| Number of Feeds | Per Page |
|---|---|
| 1 feed | $3.70 |
| 2–4 feeds | $2.55 |
| 5+ feeds | $1.80 |

*Source: JCUS rate schedule, effective October 1, 2024.*

**Callout box:**
> **Key Rule of Thumb:** Expedited delivery adds 50–100% over ordinary rates. Only expedite when you genuinely need it — this is the single biggest cost lever attorneys control.

### Page 4 — Private/Freelance Rate Ranges

**Per-Page Rates by Service Level:**

| Service Level | Per-Page Rate | Notes |
|---|---|---|
| Standard transcript (10–14 day delivery) | $4.50–$6.25 | Ordinary turnaround |
| Expedited (3–7 day) | $5.85–$7.50 | 50–100% surcharge over standard |
| Daily/overnight delivery | $7.30–$8.50 | Next-morning delivery |
| Same-day / 2-hour (hourly) | $8.70–$10.00+ | Highest priority |
| Rough draft (unedited, uncertified) | $1.75–$3.50 | Useful for trial prep; not a certified record |
| Realtime feed (per connection) | $3.00–$3.70/page | Per device/viewer |
| CART (Communication Access Realtime) | $50–$75/hour | ADA accommodation |

**Appearance Fees:**

| Duration | Fee Range |
|---|---|
| Half-day (up to 4 hours) | $100–$400 |
| Full-day (up to 8 hours) | $200–$700 |
| Hourly (alternative billing) | $75–$300/hour |

### Page 5 — Rates by State & Metro Area

**Full-width reference table:**

| State / Metro | Per-Page Range | Appearance Fees | Key Notes |
|---|---|---|---|
| New York (NYC) | $6.50–$7.50 | $250–$400 | Highest rates in the country; strong demand |
| Washington, DC | $6.00–$7.50 | Up to $350 | Premium government/regulatory market |
| California (LA/SF) | $5.50–$7.00 | $150–$350 | Severe shortage driving prices up; 458 reporters short |
| Chicago / Illinois | $4.40–$5.85 | $110–$220 | Federal rates; private rates higher |
| Southern Florida (Miami) | $4.84–$8.03 | $65–$100/hr | Federal rates above JCUS baseline |
| Texas (Houston, Dallas) | $4.00–$6.00 | $65–$150 | Moderate market; growing |
| New Jersey / Delaware | $4.75–$6.25 | Moderate | Mid-Atlantic standard; NYC proximity |
| Midwest / Rural | $3.00–$5.00 | $75–$125 | Lowest cost markets |

**Callout box ($ icon):**
> **NYC vs. NJ Savings Tip:** If deposition location is flexible in the NY metro area, booking in northern New Jersey instead of Manhattan can save 20–30% on per-page and appearance costs.

**Callout box ($ icon):**
> **Industry Salary Benchmark:** National median court reporter salary: $67,310/yr ($32.36/hr). Top freelancers with realtime specialization in major markets earn $150,000–$300,000+. This context helps you evaluate whether a provider's quoted rate is reasonable.

### Page 6 — Hidden Fees & Add-Ons

**Warning callout at top:**
> Always get an itemized quote. The per-page rate is rarely the final number. Budget 20–30% above the base transcript cost for add-ons.

**Full-width table:**

| Add-On | Typical Cost | When You Need It |
|---|---|---|
| Appearance/attendance fee | $100–$500 | Every session (half-day or full-day) |
| Transcript copy charges | $0.75–$1.45/page | Per additional party/copy |
| Rough draft surcharge | $1.75–$3.50/page | Unedited preliminary version for trial prep |
| Realtime feed | $3.00–$3.70/page per device | Live text stream to counsel during proceedings |
| Expedited delivery surcharge | +50–100% over ordinary | Need files within 3–7 days vs. 30-day standard |
| Weekend/after-hours surcharge | +25–50% | Outside normal business hours |
| Exhibit handling | $25–$75 per exhibit | Marking, copying, managing physical/digital exhibits |
| Video-to-transcript sync | $150–$300 | Syncing video recording to transcript |
| Expert/medical testimony surcharge | +$0.75/page | Specialized subject matter premium |
| Cancellation fee (< 24 hrs) | $100–$300 | Some firms charge full appearance fee |
| Travel / mileage | $100–$300 | Distant locations; parking and tolls extra |
| Conference room rental | $100–$500 | Half-day or full-day in major metros |
| Interpreter services | $75–$150/hour | Certified language interpreter |
| E-transcript / electronic delivery | $25–$50 | ASCII, PDF, or e-transcript format |
| Word index / condensed format | $25–$75 | Optional transcript formatting add-ons |
| Agency markup on per diem | 100–200% | Agencies may double the reporter's appearance rate |

**Pro Tip box:**
> Request an itemized quote that breaks out appearance fee, per-page rate, delivery speed, copy charges, and all anticipated add-ons. Don't accept "starts at $X/page."

### Page 7 — How to Negotiate Better Rates

**Numbered list:**

1. **Compare agency vs. freelance.** Agency rates include a 100–200% markup on the reporter's per diem. Freelance reporters charge directly, typically 20–40% less for equivalent service.
2. **Choose standard delivery unless you need speed.** Ordinary (30-day) transcripts cost roughly half of daily delivery. Only expedite when genuinely necessary.
3. **Share transcripts in multi-party cases.** One party orders the original; others order copies at $0.75–$1.45/page — far cheaper than separate originals.
4. **Bundle services.** Ordering transcript + video + realtime as a package often yields 10–15% savings vs. a la carte.
5. **Negotiate volume contracts.** Firms committing to regular volume can negotiate 10–25% discounts on per-page rates.
6. **Consider remote for routine depositions.** Eliminate travel fees, room rental, and parking entirely. Remote saves 40–50% when travel is involved.
7. **Skip the rough draft unless trial-bound.** Rough drafts add $1.75–$3.50/page. Only order if you need same-day preliminary text for trial prep.
8. **Get three quotes.** Pricing variation within the same market can be 30–50%. Compare at least 2–3 providers.
9. **Negotiate copy rates.** Copy charges are often the most negotiable line item, especially for high-volume multi-party litigation.
10. **Avoid last-minute cancellations.** Cancel more than 24 hours in advance to avoid $100–$300 cancellation fees.

### Page 8 — Budget Planning Worksheet

**Title:** Use this worksheet to estimate total court reporting costs. Print and fill in for each case.

**Fill-in table:**

| Line Item | Estimated Cost | Actual Cost |
|---|---|---|
| Appearance fee (half/full day) | $_____________ | $_____________ |
| Transcript — original (est. pages x rate) | $_____________ | $_____________ |
| Transcript copies (x parties) | $_____________ | $_____________ |
| Realtime feed (if needed) | $_____________ | $_____________ |
| Rough draft (if needed) | $_____________ | $_____________ |
| Expedited delivery surcharge | $_____________ | $_____________ |
| Video recording | $_____________ | $_____________ |
| Video-transcript sync | $_____________ | $_____________ |
| Exhibit handling | $_____________ | $_____________ |
| Conference room rental | $_____________ | $_____________ |
| Travel / mileage | $_____________ | $_____________ |
| **20% contingency buffer** | $_____________ | $_____________ |
| **TOTAL ESTIMATED** | $_____________ | $_____________ |

**Pro Tip box:**
> Complete this worksheet before requesting quotes. Knowing your full scope helps you get accurate all-in pricing and avoid surprise charges.

**CTA box:**
> Want a quick sanity check on your numbers?
> Email this worksheet to contact@stenoscout.com or browse verified court reporters at stenoscout.com

### Page 9 — Back Cover / CTA

- Navy 800 background
- "StenoScout" wordmark top-left
- "Find certified court reporters in your area"
- CTA button: "Browse reporters at stenoscout.com"
- "Pricing data verified against federal rate schedules and industry sources, 2026."
- contact@stenoscout.com
- "Data sourced from StenoScout's directory of court reporters across 47 states."

---

## PDF 2: Remote Court Reporting Setup Checklist

**File:** `remote-court-reporting-setup-checklist.pdf`
**Target length:** 6-8 pages
**Category badge:** "How-To" (indigo-50 bg, indigo-700 text)

### Page 1 — Cover

- Full-bleed Navy 800 background
- Title: **"Remote Court Reporting Setup Checklist"**
- Subtitle: *"Everything you need for a legally defensible remote deposition with a court reporter"*
- 4 bullet points:
  - Pre-deposition technology checklist (14 items)
  - Platform comparison: Zoom vs dedicated legal platforms
  - Realtime feed technology explained
  - State-by-state remote deposition rule summary
- Footer: "stenoscout.com | Free download — Updated 2026"

### Page 2 — Pre-Deposition Technology Checklist

**Design as an actual checkable checklist (checkbox squares) that can be printed:**

**Attorney / Participant Equipment:**
- [ ] External HD webcam (NOT built-in laptop camera)
- [ ] Noise-canceling headset with microphone (NOT laptop speakers/mic)
- [ ] Hard-wired Ethernet connection (NOT Wi-Fi)
- [ ] Minimum 10 Mbps download / 5 Mbps upload
- [ ] Professional lighting — even, front-facing, no harsh shadows
- [ ] Private, quiet room with neutral background
- [ ] All exhibits pre-loaded to platform repository (PDF format)
- [ ] Backup copies of all exhibits on local drive
- [ ] Phone dial-in number for audio backup
- [ ] Secondary device charged and ready as backup

**Court Reporter Equipment:**
- [ ] Steno writer (Luminex II, NexGen, or Diamante) connected to laptop via USB-C
- [ ] CAT software installed and tested (Case CATalyst, Eclipse, or StenoCAT)
- [ ] Realtime streaming software configured (CaseViewNet Cloud, Bridge Mobile, or LiveNote)
- [ ] Audio backup — wireless microphone kit for AudioSync recording
- [ ] Hardwired Ethernet with minimum 10 Mbps up/down
- [ ] Secondary internet connection ready (mobile hotspot)
- [ ] Backup steno machine available

**Pre-Deposition Protocol:**
- [ ] Full system test with reporter and all key participants 24–48 hours before
- [ ] All participants log in 20 minutes early for final testing
- [ ] Backup phone dial-in number distributed to all parties
- [ ] Exhibit sharing tested with sample documents
- [ ] Stipulations drafted for remote format, recording method, and technical-difficulty protocol

**Warning callout:**
> **Critical:** All participants should conduct a full dry run 24–48 hours before the deposition — not the morning of. Equipment failures discovered day-of cause delays, extra charges, and scheduling headaches.

### Page 3 — Platform Comparison

**Full-width comparison table:**

| Factor | Zoom / Teams (Generic) | Dedicated Legal Platform | In-Person |
|---|---|---|---|
| Cost | $0–$20/month | Typically included in court reporting fees | Reporter + travel + room |
| Exhibit management | Basic screen share only | Digital stamping, repository, annotation | Physical documents |
| Realtime transcript display | Requires separate software | Integrated into platform | Separate viewer |
| Digital exhibit stamping | No | Yes, with timestamps | Manual Bates stamps |
| Breakout rooms (attorney-client) | Yes | Yes, with enhanced privacy | Step outside |
| End-to-end encryption | Zoom for Government only | Standard | N/A |
| Audit trail / timestamps | No | Yes | Manual record |
| Court reporter integration | Manual | Built-in | Standard |
| Video recording quality | Varies | Professional, trial-ready | Videographer controls |
| **Verdict** | **Internal prep only** | **Trial-ready depositions** | **Gold standard** |

**Major Legal Platforms (brief descriptions):**
- **Veritext Virtual** — Built on Zoom with legal overlay; exhibit share with digital stamping; most widely used
- **RemoteDepo Pro** (US Legal Support) — Centralized exhibit repository across entire case; annotation tools
- **LegalView** (Lexitas) — Military-grade encryption; picture-in-picture realtime + video
- **vTestify** — ScriptSync for post-depo keyword search; up to 50 HD participants
- **Planet Depos Remote** — Remote tech provided free; charge only for technician oversight

**Pro Tip box:**
> Most dedicated legal platforms are included in the court reporting firm's service fee — you're not paying extra for the platform. Ask your reporter or agency what platform they use and whether it's included.

### Page 4 — Realtime Feed Technology Explained

**Title:** "How Realtime Transcript Streaming Works"

**Step-by-step visual (numbered flow):**

1. **Reporter writes** on steno machine (Luminex II, NexGen, Diamante)
2. **Machine connects** via USB-C to laptop running CAT software
3. **CAT software translates** steno strokes to English using reporter's personal dictionary
4. **Streaming software broadcasts** translated text to connected viewers via cloud or local network
5. **Attorneys view** live transcript on any device — annotate, highlight, and search in real time

**Realtime Streaming Systems:**

| System | Developer | How It Works | Client Access |
|---|---|---|---|
| CaseViewNet Cloud | Stenograph | Reporter generates session code; viewers enter at caseviewnet.com | Any browser, any device |
| Bridge Mobile | Advantage Software | Cloud streaming via Connection Magic Server | iOS/Android app + desktop |
| LiveNote Stream | Thomson Reuters | Local network + internet streaming | LiveNote client (paid) |
| TrialBook | StenoCAT | Browser-based streaming | Any browser, any device |
| LiveLitigation | LiveLitigation | Cloud streaming | Browser-based viewer |

**Callout box:**
> **Why Request Realtime?** Live transcript streaming lets you review testimony immediately, annotate key passages, and adjust your questioning strategy in real time. CaseViewNet is browser-based — no software to install. Cost: $3.00–$3.70 per page per connection.

### Page 5 — FRCP Rule 30 Compliance Checklist

**Title:** "Federal Rule 30 Requirements for Remote Depositions"

**Authorization (Rule 30(b)(4)):**
Remote depositions are permitted by party stipulation or court order. The noticing party must state the recording method in the deposition notice.

**Required On-the-Record Opening Statement (Rule 30(b)(5)):**
The officer MUST begin with ALL of the following:
- [ ] Officer's name and business address
- [ ] Date, time, and place of deposition
- [ ] Deponent's name
- [ ] Administration of oath or affirmation
- [ ] Identification of every person present with their role
- [ ] Any stipulations by the parties

**Red Flag callout:**
> Missing any single element = procedural objection and potential inadmissibility.

**Recording Requirements:**
- [ ] Deponent's appearance or demeanor must NOT be distorted through recording techniques
- [ ] Any party may designate an additional recording method beyond what the noticing party specified

**Required Closing Statement:**
- [ ] Officer states deposition is complete
- [ ] Stipulations about custody of transcript, recording, and exhibits

**State-Specific Variations:**

**Critical: Check rules in BOTH the forum state AND the state where the witness is physically located.**

- **California (CCP 2025.310):** Deponent or deposing party may elect remote attendance. Reporter does NOT need to be physically present with witness for oath.
- **Washington (CR 30):** Presumes remote depositions proceed unless opposing party files protective order within 3 business days.
- **Massachusetts:** Noticing party may elect remote format, subject to motion challenging the choice.
- **New York:** Commercial Division Rule 37, Appendix G — detailed remote deposition protocol.

**Pro Tip box:**
> **State-by-state tracker:** Perkins Coie maintains the definitive "U.S. Remote Deposition and Oath Status" chart with links to every state's specific law. Essential reference for cross-jurisdictional work.

### Page 6 — Troubleshooting Quick Reference

**Two-column layout: Problem -> Solution**

| Problem | Solution |
|---|---|
| Internet drops mid-deposition | Use hard-wired Ethernet. Have cellular hotspot as backup. Reporter goes on record noting interruption. |
| Audio echo or feedback | Use headset with mic (not laptop speakers). Ensure only one audio input active. Mute when not speaking. |
| Realtime feed disconnects | Reporter regenerates CaseViewNet/Bridge session code. Viewers reconnect. Transcript is preserved locally regardless. |
| Video quality degrades | Close other applications. Reduce video quality settings. Turn off other participants' video if needed. |
| Exhibit sharing fails | Pre-upload all exhibits to platform before going on record. Have backup method (email to reporter for manual display). |
| Platform crashes | Reporter maintains local backup recording. Reconvene on backup platform. Go on record noting interruption. |
| Witness coaching suspected | Request camera show full witness workspace. Note unusual pauses or eye movements for the record. Confirm witness is alone. |
| Software update interrupts | Update all software 24+ hours before. Disable auto-updates during session window. |

### Page 7 — Cost Comparison: Remote vs. In-Person

**Side-by-side comparison (typical 4-hour deposition, ~150 pages):**

| Component | In-Person | Remote |
|---|---|---|
| Appearance fee | $350 | $250 |
| Transcript (150 pp @ $5.50/pg) | $825 | $825 |
| Conference room rental | $250 | $0 |
| Reporter travel | $75 | $0 |
| Tech/platform fee | $0 | $200 |
| Video recording | $400 | $350 |
| Attorney travel (out-of-town) | $1,200 | $0 |
| **Total** | **$3,100** | **$1,625** |

**Callout box:**
> Remote depositions save approximately **40–50%** vs. in-person when travel is involved. For local depositions without travel, savings are more modest (10–20%) but scheduling flexibility remains a significant advantage.

### Page 8 — Back Cover / CTA

- Navy 800 background
- "StenoScout" wordmark
- "Need a court reporter for your next remote deposition?"
- CTA: "Find reporters at stenoscout.com"
- "StenoScout lists certified court reporters in 47 states who specialize in remote and hybrid proceedings."
- contact@stenoscout.com

---

## PDF 3: Court Reporter Certification & Vetting Guide

**File:** `court-reporter-certification-vetting-guide.pdf`
**Target length:** 7-9 pages
**Category badge:** "Hiring" (rose-50 bg, rose-700 text)

### Page 1 — Cover

- Full-bleed Navy 800 background
- Title: **"Court Reporter Certification & Vetting Guide"**
- Subtitle: *"How to verify credentials and avoid unqualified reporters"*
- 4 bullet points:
  - RPR, RMR, RDR, CRR certifications explained
  - Step-by-step credential verification process
  - 10 red flags that indicate an unqualified reporter
  - Sample vetting questionnaire you can send to providers
- Footer: "stenoscout.com | Free download — Updated 2026"

### Page 2 — Understanding Court Reporter Certifications

**Intro paragraph:**
The National Court Reporters Association (NCRA) administers the industry's most recognized certifications. Understanding the certification hierarchy helps you match the right reporter to your case.

**Certification Hierarchy (visual — stacked levels):**

| Level | Certification | Speed Tested | What It Proves |
|---|---|---|---|
| **Entry** | RPR (Registered Professional Reporter) | 180/200/225 WPM | Baseline competency — Literary, Jury Charge, Testimony at 95% accuracy |
| **Advanced** | RMR (Registered Merit Reporter) | 200/240/260 WPM | Advanced speed and knowledge; requires RPR + 3 years NCRA membership |
| **Expert** | RDR (Registered Diplomate Reporter) | Written exam only | Highest NCRA tier; requires RMR + 5 years NCRA membership |
| **Specialty** | CRR (Certified Realtime Reporter) | 200 WPM realtime | Proves realtime ability — 96% accuracy with NO editing allowed before submission |

**Additional Certifications:**

| Certification | Issuing Body | Purpose |
|---|---|---|
| CSR (Certified Shorthand Reporter) | Individual states | State-level licensing; requirements vary by state |
| CVR (Certified Verbatim Reporter) | NVRA | Parallel to RPR; 180/200/225 WPM at 95% accuracy |
| RVR (Realtime Verbatim Reporter) | NVRA | Parallel to CRR; requires CVR |
| CRC (Certified Realtime Captioner) | NCRA | Broadcast/CART captioners; 180 WPM |

### Page 3 — Full Certification Comparison

**Detailed comparison table:**

| Attribute | RPR | RMR | RDR | CRR |
|---|---|---|---|---|
| Full Name | Registered Professional Reporter | Registered Merit Reporter | Registered Diplomate Reporter | Certified Realtime Reporter |
| Issuing Body | NCRA | NCRA | NCRA | NCRA |
| Speed Tested | 180/200/225 WPM | 200/240/260 WPM | Written exam only | 200 WPM realtime |
| Accuracy Required | 95% each leg | 95% each leg | N/A | 96% (no editing) |
| Written Test | 120 questions, 110 min | 105 questions | 120 questions | None |
| Prerequisite | None | RPR + 3 yrs NCRA | RMR + 5 yrs NCRA | RPR or higher |
| Exam Cost | ~$220 WKT + $135–$216 skills | Similar structure | Similar structure | $160 |
| CEU Renewal | 3.0 per 3 years | 3.0 per 3 years (shared) | 3.0 per 3 years (shared) | 3.0 per 3 years (shared) |
| Court Recognition | Accepted in ~22 states | Higher prestige; preferred for complex litigation | Highest NCRA credential | Required/preferred for realtime |

**Pro Tip box:**
> **RPR is the baseline.** If a reporter doesn't hold at least an RPR (or state CSR equivalent), they haven't demonstrated minimum competency through a standardized exam. For high-stakes litigation, look for RMR or higher.

### Page 4 — State Licensing Requirements

**Two-column layout:**

**States That Require Their Own Exam (do NOT accept national certifications alone):**
Arkansas, California, Connecticut, Idaho, Illinois, Michigan, Mississippi, Missouri, Nevada, Oklahoma, Tennessee, Texas

**States That Accept NCRA RPR (~22 states):**
Most other licensing states accept RPR as a qualifying credential. Check with the specific state board.

**Notable State Requirements:**
- **California CSR:** 200 WPM four-voice dictation at 95% accuracy + 2,300 hours machine shorthand training + 660 hours academic coursework. Verify at search.dca.ca.gov
- **Texas CSR:** State-specific exam; does not accept national certifications
- **Illinois CSR:** State certification at 225 WPM
- **Iowa:** RPR holders only need the written portion of the Iowa exam

**Warning callout:**
> Even in non-licensing states (like New York, Florida, Pennsylvania), individual courts and employers often require NCRA certification. "No state requirement" does NOT mean "no certification needed for quality work."

### Page 5 — How to Verify Credentials

**Step-by-step verification process (numbered, with icons):**

**Step 1:** Ask the reporter for their NCRA certification number and current membership status.

**Step 2:** Verify through NCRA's PROLink directory (ncra.org). Search by name, locale, or certification level.

**Step 3:** Check state licensing. In licensing states, verify through the state's court reporting board (e.g., California: search.dca.ca.gov; Texas: Court Reporters Certification Board).

**Warning callout:**
> NCRA PROLink only shows members who opt in to the public directory. Members who opt out won't appear. If a reporter claims NCRA certification but isn't on PROLink, contact NCRA directly to verify.

**Step 4:** Check renewal and CE status. All NCRA certifications require 3.0 CEUs every 3 years. A lapsed certification means the reporter hasn't kept current with evolving standards.

**Step 5:** Ask to see the certification page of a recent transcript. The reporter's credentials appear next to their signature on the certification page.

**Step 6:** If the reporter claims credentials from an unfamiliar organization, investigate. Only NCRA and NVRA certifications are widely recognized by courts.

### Page 6 — 10 Red Flags of an Unqualified Reporter

**Design as visual cards with red flag icons and red-50 background:**

1. **No certifications or vague credentials.** Can't produce an NCRA number or state license number; deflects when asked about specific credentials.

2. **Outdated technology.** Not using computer-aided transcription (CAT) software or AudioSync backup. Relying on tape recorders or outdated equipment.

3. **Non-itemized billing.** Lump-sum invoices that obscure line-item charges — a common cover for overbilling.

4. **Cannot provide realtime.** For complex litigation, inability to provide a realtime feed to counsel is a competency concern.

5. **Financial relationships with opposing counsel.** Ethical violation if undisclosed. Watch for differential pricing (discount for hiring attorney, surcharge for opposing counsel).

6. **Delayed or differential transcript delivery.** Delivering transcripts to the contracting attorney days before opposing counsel receives their copies.

7. **Won't ask for clarification on the record.** A competent reporter interrupts to request spellings, ask speakers to repeat, and clarify on/off-record status.

8. **No E&O insurance.** Freelance reporters without professional liability coverage expose attorneys to risk if errors occur.

9. **No professional association membership.** No NCRA, NVRA, or state association membership means no ongoing ethical oversight or CE requirements.

10. **Shows you corporate transcription samples instead of legal proceedings.** Court reporting and general transcription are completely different skill sets.

### Page 7 — When Certification Matters (Decision Matrix)

**Two-column layout:**

**HIRE CERTIFIED (RPR minimum, RMR/CRR preferred) WHEN:**
- Deposition may be played at trial
- High-stakes litigation (med mal, patent, securities, class action)
- Realtime feed required (deaf/HOH accommodation, attorney preference)
- Multi-party deposition with rapid speaker changes
- Cross-jurisdictional work requiring credential portability
- Appeals-sensitive proceedings
- Federal court (many federal courts require/prefer NCRA certification)

**CERTIFICATION LESS CRITICAL WHEN:**
- Routine EUOs (examinations under oath) for insurance matters
- Internal corporate proceedings not intended for court submission
- Uncertified reporter has 10+ years of active deposition experience with strong attorney references
- Even here: verify E&O insurance and request sample transcripts

**Cost comparison:**

| Factor | Certified (RPR/RMR/CRR) | Uncertified / Digital |
|---|---|---|
| Per-page rate | $4.50–$7.50/page | $3.00–$5.00/page |
| Realtime capability | Yes (CRR) | No |
| Rough draft / daily copy | Yes | Limited |
| Trial admissibility | Strong | May be challenged |
| Professional oversight | NCRA ethics code, CE requirements | None unless state-licensed |
| E&O insurance | Standard | Varies |

### Page 8 — Sample Vetting Questionnaire

**Design as a printable page attorneys can email to providers:**

**Title:** "Court Reporter Vetting Questionnaire — Send This Before Hiring"

**Instructions:** *Copy and send these questions to any court reporter or agency you're considering. Their answers will tell you everything you need to know.*

---

**1. Credentials & Licensing**
- What NCRA certifications do you currently hold (RPR, RMR, RDR, CRR)?
- What is your NCRA member number?
- Are you licensed/certified in [state where the proceeding will occur]?
- When did you last complete your continuing education requirements?

**2. Experience & Capabilities**
- How many years have you been reporting depositions? Approximately how many per year?
- Do you have experience with [specific subject matter — medical, patent, financial, technical]?
- Can you provide realtime feed to counsel during the deposition?
- What CAT software do you use? Do you provide CaseViewNet/LiveNote/Bridge compatibility?

**3. Technology & Backup**
- What is your primary steno equipment?
- Do you use AudioSync backup during proceedings?
- What is your procedure if equipment fails mid-proceeding?
- Can you accommodate remote/hybrid depositions?

**4. Ethics & Independence**
- Do you have any contracting relationships with any party or firm involved in this matter?
- Will all parties receive their transcripts at the same time and at the same rates?

**5. Insurance & Business**
- Do you carry errors & omissions (professional liability) insurance? What are your policy limits?
- What is your transcript delivery timeline for standard, expedited, and daily copy?
- Do you provide itemized invoices with per-page rates clearly stated?
- What is your cancellation policy?

**6. References**
- Can you provide 2–3 attorney references?
- Can you share a sample of a recent deposition transcript?

### Page 9 — Back Cover / CTA

- Navy 800 background
- "StenoScout" wordmark
- "Find certified court reporters in your area"
- CTA: "Search reporters at stenoscout.com"
- "Every listing includes certification status, reviews from attorneys, and direct contact information."
- contact@stenoscout.com

---

## Design Notes for All Three PDFs

1. **Printability matters.** Attorneys print these. Avoid large solid color areas on interior pages (waste ink). Reserve full-bleed backgrounds for cover and back cover only.

2. **Tables are the star.** These guides live or die on their reference tables. Make tables scannable, well-spaced, and easy to read at 100% zoom on screen AND when printed on letter paper.

3. **Checklist pages should be functional.** The remote setup checklist (PDF 2, page 2) and vetting questionnaire (PDF 3, page 8) should have actual checkbox squares that look good printed.

4. **Keep it dense but not cramped.** Attorneys expect information density. Don't add decorative filler. Every element should convey information. White space should aid readability, not pad page count.

5. **No stock photos.** These are data documents, not marketing brochures. Use tables, callout boxes, and icons instead of photography.

6. **Consistent footer on every interior page:** Left-aligned "stenoscout.com", right-aligned page number, thin gray rule above.

7. **PDF bookmarks/TOC.** Each PDF should have clickable bookmarks in the PDF sidebar matching the section headings.

8. **Hyperlinks.** "stenoscout.com" and "contact@stenoscout.com" should be clickable links in the PDF.

9. **Brand color consistency.** StenoScout uses indigo (#4f46e5) where DepoHire uses blue (#2563eb). Apply the indigo consistently across all accent elements, headers, and CTA buttons.

10. **Match the DepoHire PDF quality.** Reference the existing DepoHire PDFs for exact layout patterns, spacing, cover design (navy background with subtle circle accent), table formatting, callout box styling, and back cover CTA layout. The StenoScout PDFs should feel like they're from the same family — same design system, different brand colors and content.
