# PDF Guide Design Brief — DepoHire Lead Magnets

**Project:** 3 downloadable PDF guides for depohire.com
**Brand:** DepoHire — The most comprehensive directory of deposition videographers in the United States
**Audience:** Litigation attorneys, paralegals, and legal operations managers at mid-size to large law firms
**Tone:** Professional, authoritative, data-driven. Think McKinsey report meets legal practice guide. No fluff, no marketing speak. These readers bill $300-800/hr and value density.

---

## Brand Guidelines

### Colors
| Token | Hex | Usage |
|-------|-----|-------|
| Primary 600 | `#2563eb` | Headings, links, CTA buttons, accent bars |
| Primary 50 | `#eff6ff` | Light backgrounds, callout boxes |
| Primary 100 | `#dbeafe` | Table header backgrounds |
| Navy 800 | `#1e3a5f` | Cover page background, footer bars, hero sections |
| Navy 950 | `#1a1a2e` | Body text (dark) |
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
- Text-only: "DepoHire" in Inter ExtraBold, Navy 800
- No logo file exists — just set the brand name in Inter 800 weight

### Recurring Design Elements
- **Callout boxes:** Rounded corners (8-12px), left border accent (3-4px solid Primary 600), light background (Primary 50)
- **Pro Tip boxes:** Same as callout but with emerald left border and emerald-50 background
- **Warning/Red Flag boxes:** Red left border, red-50 background
- **Tables:** Header row in Primary 100 with Primary 700 text. Alternating gray-100 stripes. No heavy borders — use subtle 1px gray-200 lines.
- **Checkmark lists:** Emerald 600 checkmarks, body text
- **Page footer:** Gray bar with "depohire.com" left-aligned, page number right-aligned
- **Cover footer:** "depohire.com | contact@depohire.com"

---

## File Delivery Specs

| Spec | Value |
|------|-------|
| Format | PDF (print-quality, with bookmarks/TOC) |
| Page size | US Letter (8.5" x 11") |
| Margins | 0.75" all sides (1" top on first page of each section) |
| Bleed | Not needed (digital-only distribution) |
| File names | `deposition-videographer-rate-guide-2026.pdf`, `remote-deposition-setup-checklist.pdf`, `clvs-verification-guide.pdf` |
| Delivery location | `public/guides/pdf/` in the project repo |
| Max file size | Under 5MB each (these are served from Cloudflare CDN) |

---

## PDF 1: Deposition Videographer Rate Guide 2026

**File:** `deposition-videographer-rate-guide-2026.pdf`
**Target length:** 6-8 pages
**Category badge:** "Pricing" (emerald-50 bg, emerald-700 text)

### Page 1 — Cover

- Full-bleed Navy 800 background
- "DepoHire" top-left in white
- Title: **"Deposition Videographer Rate Guide 2026"**
- Subtitle: *"Real pricing data from providers across all 50 states"*
- 4 bullet points (white checkmarks):
  - Average rates for 33 major metro areas
  - Half-day vs full-day pricing breakdown
  - Hidden fees to watch for (streaming, copies, travel)
  - How to negotiate better rates with providers
- Footer: "depohire.com | Free download — Updated 2026"

### Page 2 — 2026 Pricing at a Glance

**Full-width pricing table:**

| Service Level | First Hour | Additional Hours | Full Day (8 hrs) | What's Included |
|---|---|---|---|---|
| Budget HD | $75 | $70/hr | ~$565 | HD camera, 1 lav mic, Dropbox delivery |
| Standard HD/4K | $95–$150 | $90–$110/hr | $750–$999 | 4K camera, 2 lav mics, backup recorder |
| Premium Studio | $215–$500 | $110–$350/hr | $900–$2,299 | Full crew, multi-camera, editing included |
| Remote/Zoom | $379 min | Per 6-min increments | ~$769 | Secure platform, paperless delivery |

**Callout box below table:**
> **Quick Budget Reference**
> - Standard half-day deposition: $300–$600
> - Full-day deposition: $750–$999
> - Full deposition with transcript, video, and synchronization: $1,000–$5,000

**Package-Based Pricing sidebar or secondary table:**
- Half-day packages (2–3 hours): ~$625
- Full-day packages (3–5 hours): ~$750
- All-day session (8 hours): $900–$999

### Page 3 — Hidden Fees & Add-Ons

**Warning callout at top:**
> Always get an all-in quote. The base hourly rate is rarely the final number.

**Full-width table:**

| Add-On | Typical Cost | When You Need It |
|---|---|---|
| Video-to-transcript sync | $150–$300 | Trial prep, clip creation for TrialDirector |
| Editing/post-production | $350/hr | Impeachment clips, trial presentation |
| Overtime | $95 per half-hour | Deposition runs past scheduled end |
| Expedited delivery | 50–100% premium | Need files within 24–48 hours |
| 4K upgrade (over HD) | $20–$25/hr more | When visual detail matters for evidence |
| Media/disc copies | $10–$25/disc | Physical backup or opposing counsel copies |
| Cancellation fee | $99+ | Late cancellations on remote bookings |
| Travel | Varies by distance | Outside videographer's metro area |

**Pro Tip box:**
> Budget 15–20% above the quoted rate for inevitable add-ons (sync, delivery format, travel).

### Page 4-5 — Rates by State & Metro Area

**Large reference table (can span 2 pages):**

| State / Metro | Hourly Range | Typical Session | Key Notes |
|---|---|---|---|
| New York (NYC) | $150–$400+ | $500–$1,000+ | Highest demand; Manhattan appearance fees alone $250–$400 |
| Washington, DC | $150–$350 | $500–$900 | Federal litigation hub; full-day rates north of $900 |
| California (LA/SF) | $100–$420 | $400–$800 | LA freelancers $100–$420/hr; day rates $800–$3,360 for 8–10 hr sessions |
| Colorado (Denver) | $104–$404 | $400–$750 | Steady mid-range; rates flat heading into 2026 |
| Florida (Jacksonville) | $215 first hr, $110 after | $300–$600 | National providers based here; mid-range |
| New Jersey / Delaware | $75–$150 | $300–$500 | NYC proximity without Manhattan premium |
| Central Pennsylvania | $70–$95 | $250–$400 | Lowest major-market rates; full day under $600 |
| Small markets (ME, etc.) | Varies widely | $250–$600 | Fewer providers; remote often cheaper than travel |
| National Remote | $67–$135/hr technician | $250–$600 flat | Geography-neutral; stabilized at mid-range in-person rates |

**Callout box:**
> **NYC vs. NJ Tip:** If deposition location is flexible in the NY metro area, booking in northern New Jersey instead of Manhattan can save 20–30%.

**Sidebar stat:** National average deposition videographer salary: $30.74/hr ($63,930/yr), ranging from mid-$50Ks in smaller markets to $86K+ in high-cost metros.

### Page 6 — How to Negotiate Better Rates

**Numbered list with icons/checkmarks:**

1. **Get three quotes** — Pricing variation within the same city can be 50–100%. Never accept the first quote.
2. **Ask for an all-in number** — Specifically ask about sync, delivery format, overtime policy, and cancellation fees. Don't accept "starts at $X/hour."
3. **Skip editing unless going to trial** — Raw unedited files are admissible and save $350+/hr in post-production costs.
4. **Bundle with court reporting** — Many firms offering both transcription and videography discount the combined package by 10–15%.
5. **Consider remote for routine depositions** — At $250–$600 per session nationally, often cheaper than in-person in expensive markets.
6. **Book outside Manhattan** — Northern NJ saves 20–30% for NY metro depositions.
7. **Negotiate volume discounts** — For cases with 5+ depositions, ask about per-session volume pricing.

### Page 7 — Budget Planning Worksheet

**Simple fill-in table the attorney can print and use:**

| Line Item | Estimated Cost | Actual Cost |
|---|---|---|
| Base videography (half/full day) | $_______ | $_______ |
| Transcript synchronization | $_______ | $_______ |
| Expedited delivery (if needed) | $_______ | $_______ |
| Travel / mileage | $_______ | $_______ |
| 4K upgrade | $_______ | $_______ |
| Media copies (×___ copies) | $_______ | $_______ |
| Editing (if trial-bound) | $_______ | $_______ |
| **15% contingency buffer** | $_______ | $_______ |
| **Total estimated** | $_______ | $_______ |

### Page 8 — Back Cover / CTA

- Navy 800 background
- "Find verified deposition videographers in your area"
- CTA: "Browse providers at depohire.com"
- Secondary: "Questions? contact@depohire.com"
- "Data sourced from DepoHire's directory of deposition videographers across 33+ cities and all 50 states."

---

## PDF 2: Remote Deposition Setup Checklist

**File:** `remote-deposition-setup-checklist.pdf`
**Target length:** 5-6 pages
**Category badge:** "How-To" (blue-50 bg, blue-700 text)

### Page 1 — Cover

- Full-bleed Navy 800 background
- Title: **"Remote Deposition Setup Checklist"**
- Subtitle: *"Everything you need for a legally defensible remote deposition"*
- 4 bullet points:
  - Pre-deposition technology checklist (12 items)
  - Platform comparison: Zoom vs Teams vs dedicated legal platforms
  - State-by-state remote deposition rule summary
  - Troubleshooting guide for common technical issues
- Footer: "depohire.com | Free download — Updated 2026"

### Page 2 — Pre-Deposition Technology Checklist

**Design as an actual checkable checklist (checkbox squares) that can be printed:**

**Equipment Requirements:**
- [ ] HD USB camera (NOT built-in laptop webcam)
- [ ] Noise-canceling microphone (NOT built-in camera audio)
- [ ] Hard-wired ethernet connection (NOT Wi-Fi)
- [ ] Neutral, static background (no virtual backgrounds)
- [ ] Professional lighting (even, front-facing, no harsh shadows)
- [ ] Backup recording device (external recorder separate from main camera)
- [ ] Backup batteries and spare cables
- [ ] Headphones for real-time audio monitoring

**Software & Platform:**
- [ ] Dedicated legal deposition platform (NOT Zoom/Teams for trial-bound depositions)
- [ ] Platform supports exhibit upload and screen sharing
- [ ] Breakout room capability for off-the-record conferences
- [ ] Recording outputs compatible with trial presentation software (TrialDirector, OnCue, Summation, Sanction)

**Warning callout:**
> **Post-Alcorn Warning:** *Alcorn v. City of Chicago* established that Zoom/Teams recordings without a certified videographer are frequently challenged and rejected for trial admissibility. If there is any chance the deposition will be played at trial, use a certified videographer on a purpose-built legal platform.

### Page 3 — Platform Comparison

**Full-width comparison table:**

| Factor | Zoom/Teams | Dedicated Legal Platform | In-Person |
|---|---|---|---|
| Cost | $0–$50 | $67–$135/hr technician | Technician + travel + lodging |
| Trial admissibility | Frequently challenged | Strong with certified videographer | Strong with certified videographer |
| Witness body language | Limited (gallery view issues) | Proper witness close-up | Full observation |
| Coaching prevention | Texts/notes possible off-screen | Better monitoring tools | All parties visible |
| Exhibit handling | Basic screen share | Purpose-built exhibit upload/annotation | Physical documents |
| Opening/closing protocol | Manual, often missed | Built-in compliance prompts | Standard procedure |
| Transcript sync | Not supported | Integrated with court reporter | Standard |
| **Verdict** | **Internal prep only** | **Trial-ready depositions** | **Gold standard** |

**Pro Tip box:**
> Remote depositions save 30–50% on costs vs. in-person when you factor in eliminated travel, lodging, and scheduling delays. At $250–$600 per session nationally, remote pricing has stabilized at roughly the same cost as mid-range in-person (minus travel).

### Page 4 — FRCP 30(b)(4) Compliance Checklist

**Title:** "Three Non-Negotiable Requirements for Federal Rule 30 Compliance"

**Requirement 1: No Manipulation of Appearance or Demeanor**
- No filters, creative angles, or post-production color correction
- No gallery view (four tiny rectangles) — proper witness close-up only
- Videographers from corporate/event backgrounds often color-grade footage — this violates Rule 30

**Requirement 2: Required On-Camera Opening Statement**
Must include ALL of these (checklist format):
- [ ] Court reporter's name and business address
- [ ] Deposition location, date, and time
- [ ] Deponent's name
- [ ] Administration of oath or affirmation
- [ ] Identification of every person present with their role

**Red Flag callout:**
> Missing any single element = procedural objection and potential inadmissibility.

**Requirement 3: Provenance and Metadata Integrity**
- [ ] Original files protected with intact metadata
- [ ] Authorship, creation timestamps, modification timestamps, digital signatures preserved
- [ ] Chain of custody documented from recording start to delivery

**State-Specific Variations section (compact reference):**
- **California (CCP 2025):** Videographers recording treating physicians or expert witnesses must be authorized to administer an oath. California 3.1010 addresses remote videography standards.
- **Illinois (BIPA):** Video depositions capturing biometric data may require specific consent and data handling procedures.
- **Medical depositions (all states):** HIPAA compliance required for storage, transmission, and retention of footage with PHI.

### Page 5 — Troubleshooting Quick Reference

**Two-column layout: Problem → Solution**

| Problem | Solution |
|---|---|
| Internet drops mid-deposition | Use hard-wired connection. Have cellular hotspot as backup. Certified videographer can pause and resume without losing continuity. |
| Audio echo or feedback | Use noise-canceling mic (not built-in). Ensure only one audio input active. Mute when not speaking. |
| Video quality degradation | Close bandwidth-heavy applications. Lower resolution if needed (HD acceptable; 4K ideal but not required). |
| Witness coaching suspected | Request camera show full witness workspace. Note any unusual pauses or eye movements for the record. |
| Exhibit sharing fails | Pre-upload all exhibits to platform before deposition start. Have backup method (email to videographer for manual display). |
| Platform crashes | Certified videographer maintains local backup recording. Reconvene on backup platform within minutes. |
| Breakout room audio leak | Test breakout rooms before going on record. Confirm audio isolation with all parties. |

### Page 6 — Back Cover / CTA

- "Need a certified remote deposition videographer?"
- CTA: "Find providers at depohire.com"
- "DepoHire lists certified videographers in 33+ cities who specialize in remote and hybrid depositions."
- contact@depohire.com

---

## PDF 3: CLVS Verification & Vetting Guide

**File:** `clvs-verification-guide.pdf`
**Target length:** 6-8 pages
**Category badge:** "Hiring" (rose-50 bg, rose-700 text)

### Page 1 — Cover

- Full-bleed Navy 800 background
- Title: **"CLVS Verification & Vetting Guide"**
- Subtitle: *"How to verify credentials and avoid unqualified videographers"*
- 4 bullet points:
  - Step-by-step CLVS verification process
  - Insurance and bonding requirements by state
  - 10 red flags that indicate an unqualified videographer
  - Sample vetting questionnaire you can send to providers
- Footer: "depohire.com | Free download — Updated 2026"

### Page 2 — Understanding CLVS Certification

**What is CLVS?**
Brief paragraph: CLVS (Certified Legal Video Specialist) is the industry's gold-standard credential, administered by the National Court Reporters Association (NCRA). It's the most widely recognized certification by courts nationwide.

**CLVS vs. CDVS Comparison Table:**

| Criterion | CLVS (NCRA) | CDVS (AGCV) |
|---|---|---|
| Cost | $1,500–$2,000 | $800–$1,200 |
| Timeline | 2–3 months | 1–2 months |
| Hands-on exam | In-person mock deposition at NCRA HQ (Reston, VA) | Mock deposition submitted remotely |
| Written exam | 100 questions, 70% to pass, 200+ test sites | Online course + evaluation |
| Renewal | 10 CEU hours every 3 years | Varies |
| Court recognition | Widely recognized | Growing, but newer |
| Best for | Top-tier credibility | Budget-conscious or newer videographers |

**What CLVS Tests (6 domains):**
1. Professional development and ethics
2. Operating practices
3. Office procedures
4. Post-production
5. Legal/judicial procedures
6. Video recording production

### Page 3 — How to Verify CLVS Credentials

**Step-by-step verification process (numbered, with icons):**

**Step 1:** Ask the provider for their CLVS credential number and date of certification.

**Step 2:** Verify through NCRA's registry. Contact NCRA directly if online verification is unavailable.

**Step 3:** Check renewal status. CLVS requires 10 hours of continuing education every 3 years.

**Warning callout:**
> A lapsed CLVS means the person earned the credential but hasn't kept current with evolving standards. This matters — standards have changed significantly with the rise of remote depositions.

**Step 4:** Ask for proof of the production exam completion (the hands-on mock deposition at NCRA headquarters).

**Step 5:** If the provider claims a credential from an organization other than NCRA or AGCV, investigate thoroughly. Many online "certification mills" exist.

### Page 4 — 10 Red Flags of an Unqualified Videographer

**Design as a visual checklist with red flag icons and red-50 background cards:**

1. **Can't recite Rule 30 opening requirements from memory.** Every certified videographer knows these cold.

2. **No backup plan for equipment failure.** If their answer involves "restart" or "reschedule" — walk away. They should describe dual recording (camera + external recorder).

3. **No real-time audio monitoring.** If they don't wear headphones during recording, they can't catch audio issues before they become problems.

4. **Shows you a wedding reel or corporate video instead of deposition footage.** Completely different skill set.

5. **Treats every state's rules identically.** State deposition rules vary significantly (California oath requirements, Illinois BIPA, etc.).

6. **Claims "certified" from an unknown organization.** Only NCRA (CLVS) and AGCV (CDVS) are recognized by courts.

7. **Unfamiliar with transcript synchronization.** If they don't know how to coordinate with a court reporter for time-coded sync, they lack deposition-specific experience.

8. **No chain of custody procedures.** Can't explain how they protect metadata integrity, store original files, or maintain evidence provenance.

9. **Video uses Zoom gallery view.** Four tiny rectangles instead of a proper witness close-up is a trial admissibility problem (per Alcorn).

10. **No attorney references.** Any experienced deposition videographer can provide references from attorneys they've worked with.

### Page 5 — When Certification Matters (Decision Matrix)

**Two-column layout:**

**HIRE CERTIFIED WHEN:**
- Deposition may be played at trial
- Jurisdiction has strict admissibility standards
- High-stakes testimony (expert witnesses, key fact witnesses)
- Remote deposition requiring protocol expertise
- Any chance the video reaches a jury

**CERTIFICATION LESS CRITICAL WHEN:**
- Video is purely for internal case prep (will never see a courtroom)
- Uncertified videographer has 15+ years deposition-specific experience with strong attorney references
- Strictly internal case prep with zero trial exposure risk

**Cost comparison table:**

| Factor | Certified (CLVS/CDVS) | Uncertified / DIY |
|---|---|---|
| Cost | $200–$400/session | $0–$150 (Zoom/internal) |
| Trial admissibility | Strong | Frequently challenged |
| Equipment | Broadcast-quality, redundant | Varies wildly |
| Chain of custody | Neutral third-party, encrypted | Party-controlled |
| Legal protocol | Full Rule 30 compliance | Often ad-hoc or missing |
| Court reporter integration | Coordinated, synced transcripts | Typically disconnected |

**Pro Tip callout:**
> Some uncertified videographers with 10+ years of deposition-specific experience will outperform a freshly certified CLVS holder. But when hiring someone you've never worked with, a guaranteed baseline is worth paying for.

### Page 6 — Sample Vetting Questionnaire

**Design as a tear-out / printable page that attorneys can email to providers:**

**Title:** "Provider Vetting Questionnaire — Send This to Videographers Before Hiring"

**Instructions text:** *Copy and send these questions to any deposition videographer you're considering. Their answers will tell you everything you need to know.*

---

**1. Certification & Credentials**
- What certifications do you hold? (CLVS, CDVS, other)
- What is your credential number and date of certification?
- Are you current on continuing education requirements?

**2. Rule 30 Compliance**
- Walk me through the opening statement requirements you include at the start of every deposition.
- *(Expected: court reporter name/address, location/date/time, deponent name, oath, identification of all persons present — from memory)*

**3. Equipment & Redundancy**
- What is your primary recording setup?
- What is your backup plan if your primary camera fails mid-deposition?
- *(Expected: dual recording — camera + external recorder, backup batteries, spare cables)*
- Do you monitor audio in real-time during recording?

**4. Jurisdiction Knowledge**
- Are you familiar with [STATE] deposition rules?
- What specific requirements apply in this jurisdiction?

**5. Court Reporter Coordination**
- Have you worked alongside court reporters? Describe your sync workflow.
- What trial presentation software are your files compatible with? *(Expected: TrialDirector, OnCue, Summation, Sanction)*

**6. Experience & References**
- How many depositions have you recorded in the past 12 months?
- Can you provide 2-3 attorney references?
- Can you share a sample of actual deposition footage (not corporate or event video)?

**7. Insurance & Logistics**
- Do you carry professional liability insurance?
- What is your cancellation policy?
- What are your rates for [half-day / full-day], and what is included vs. add-on?

---

### Page 7 — Insurance & Bonding Reference

**State-specific requirements (compact table):**

| Requirement | Details |
|---|---|
| California (CCP 2025) | Videographers recording treating physicians or experts must be authorized to administer an oath (notary or certified court reporter status) |
| Illinois (BIPA) | Video capturing biometric data (facial geometry in HD) may require specific consent and data handling procedures |
| Medical depositions (all states) | HIPAA compliance required for storage, transmission, and retention of footage containing PHI |
| General best practice | Verify professional liability insurance, equipment insurance, and errors & omissions coverage |

**Callout:**
> Always confirm insurance coverage before the deposition date. Request a certificate of insurance if the case is high-stakes.

### Page 8 — Back Cover / CTA

- Navy 800 background
- "Find CLVS-certified videographers in your area"
- CTA: "Search providers at depohire.com"
- "Every listing includes certification status, reviews from attorneys, and direct contact information."
- contact@depohire.com

---

## Design Notes for All Three PDFs

1. **Printability matters.** Attorneys print these. Avoid large solid color areas on interior pages (waste ink). Reserve full-bleed backgrounds for cover and back cover only.

2. **Tables are the star.** These guides live or die on their reference tables. Make tables scannable, well-spaced, and easy to read at 100% zoom on screen AND when printed on letter paper.

3. **Checklist pages should be functional.** The remote setup checklist (PDF 2, page 2) and vetting questionnaire (PDF 3, page 6) should have actual checkbox squares that look good printed.

4. **Keep it dense but not cramped.** Attorneys expect information density. Don't add decorative filler. Every element should convey information. White space should aid readability, not pad page count.

5. **No stock photos.** These are data documents, not marketing brochures. Use tables, callout boxes, and icons instead of photography.

6. **Consistent footer on every interior page:** Left-aligned "depohire.com", right-aligned page number, thin gray rule above.

7. **PDF bookmarks/TOC.** Each PDF should have clickable bookmarks in the PDF sidebar matching the section headings.

8. **Hyperlinks.** "depohire.com" and "contact@depohire.com" should be clickable links in the PDF.
