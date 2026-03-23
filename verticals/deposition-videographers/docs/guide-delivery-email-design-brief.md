# Guide Delivery Email — Design Brief

**Purpose:** Transactional email sent immediately after someone submits the guide download form on depohire.com. Delivers the PDF download link.
**Trigger:** User enters name + email on any `/guides/[slug]/` page
**Template system:** Listmonk (Go templates — `{{ .Tx.Data.fieldname }}` syntax)
**Current HTML:** `email-templates/guide-delivery.html`

---

## Context & Goals

This is the first email a potential lead receives from DepoHire. It needs to:
1. Deliver the download link immediately and prominently (this is what they signed up for)
2. Look professional and trustworthy (audience is attorneys at law firms)
3. Cross-promote the directory and other guides without being pushy
4. Comply with CAN-SPAM (physical address, unsubscribe link)

The email is **transactional** (triggered by user action), not a marketing campaign. Keep it clean and functional — no hard sells.

---

## Brand Guidelines

### Colors
| Name | Hex | Usage in this email |
|------|-----|---------------------|
| Navy gradient | `#0f1b2d` → `#1a3352` → `#1e3a5f` → `#2a4a6b` | Header background (135deg gradient) |
| White | `#ffffff` | Email body background, button text |
| Primary 600 | `#2563eb` | CTA button, links |
| Primary 700 | `#1d4ed8` | CTA button hover |
| Primary 50 | `#eff6ff` | Guide download box background |
| Primary 200 | `#bfdbfe` | Guide download box border |
| Primary 300 | `#93c5fd` | Header subtitle text |
| Gray 50 | `#f9fafb` | Tips section background, footer background |
| Gray 100 | `#f3f4f6` | Outer body background (behind email) |
| Gray 200 | `#e5e7eb` | Tips section border, footer top border |
| Gray 400 | `#9ca3af` | Footer text, disclaimer text |
| Gray 500 | `#6b7280` | Guide box subtitle, footer links |
| Gray 600 | `#4b5563` | Body text, tips list text |
| Gray 900 | `#1f2937` | Guide title, tips heading |

### Typography
- **Font stack:** `-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif` (system fonts — no web fonts in email)
- **Header brand:** 20px, bold (700), white
- **Header subtitle:** 13px, regular, Primary 300
- **Body text:** 14px, regular, line-height 1.6, Gray 600
- **Guide title:** 18px, bold (700), Gray 900
- **CTA button text:** 15px, semibold (600), white
- **Tips heading:** 14px, semibold (600), Gray 900
- **Tips list items:** 13px, regular, Gray 600
- **Footer text:** 12px, regular, Gray 400
- **Disclaimer text:** 13px, regular, Gray 400

---

## Layout (top to bottom)

### 1. Header Bar
- Full-width navy gradient background (same as site hero)
- "DepoHire" centered, 20px bold white
- "Your free guide is ready" centered below, 13px Primary 300
- Padding: 32px top/bottom, 24px left/right

### 2. Body Section
- White background, 32px padding all sides
- Max width: 560px centered

**Greeting paragraph:**
> Hi {{ .Tx.Data.name }},

**Intro paragraph:**
> Thanks for downloading a guide from DepoHire. Your copy is ready — click the button below to download it now.

### 3. Guide Download Box (the hero element)
- **This is the most important element in the email. Make it unmissable.**
- Rounded card (10px radius), Primary 50 background, Primary 200 border
- Centered layout, 24px padding
- Guide title: `{{ .Tx.Data.guide_title }}` — 18px bold, Gray 900
- Subtitle: "PDF · Free download · Updated 2026" — 13px, Gray 500
- **CTA Button:** "Download Your Guide"
  - Primary 600 background, white text, 15px semibold
  - 14px vertical padding, 36px horizontal padding
  - 8px border radius
  - Links to: `https://depohire.com{{ .Tx.Data.pdf_url }}`
- 24px vertical margin above and below the box

### 4. Reassurance line
> This link will work anytime — feel free to bookmark it or forward it to a colleague.

### 5. Tips / Cross-promotion Box
- Gray 50 background, Gray 200 border, 8px radius, 20px padding
- Heading: "While you're here, you might also find these useful:" — 14px semibold
- Bulleted list (3 items):
  - [Browse all free guides](https://depohire.com/guides/)
  - [Find deposition videographers near you](https://depohire.com/locations/)
  - [Read our latest hiring guides and market analysis](https://depohire.com/blog/)
- Links in Primary 600

### 6. Disclaimer
- Gray 400, 13px
> You're receiving this because you requested a guide download from DepoHire. We'll send occasional updates about deposition videography (no more than once per month).

### 7. Footer
- Gray 50 background, Gray 200 top border
- 20px vertical padding, 24px horizontal padding, centered text
- Line 1: "&copy; 2026 DepoHire. All rights reserved." — 12px Gray 400
- Line 2: "DepoHire · PO Box 1547, Austin, TX 78767" — 12px Gray 400
- Line 3: [Unsubscribe]({{ .UnsubscribeURL }}) · [Privacy](https://depohire.com/privacy/) — 12px Gray 500 links

---

## Dynamic Fields (Listmonk template variables)

These are populated by the backend at send time. Use them as placeholders in the design:

| Variable | Example value | Where it appears |
|----------|---------------|-------------------|
| `{{ .Tx.Data.name }}` | "Jane Smith" | Greeting ("Hi Jane Smith,") |
| `{{ .Tx.Data.guide_title }}` | "Deposition Videographer Rate Guide 2026" | Guide box heading |
| `{{ .Tx.Data.pdf_url }}` | "/guides/pdf/deposition-videographer-rate-guide-2026.pdf" | CTA button href (appended to `https://depohire.com`) |
| `{{ .UnsubscribeURL }}` | (auto-generated by Listmonk) | Footer unsubscribe link |

### The 3 possible guide titles:
1. "Deposition Videographer Rate Guide 2026"
2. "Remote Deposition Setup Checklist"
3. "CLVS Verification & Vetting Guide"

Design should accommodate the longest title (option 1, 46 chars) without wrapping awkwardly in the guide box.

---

## Email Client Compatibility Notes

- **Outlook (Windows):** Does not support CSS gradients. The header will fall back to a solid color. Use a `background-color: #1e3a5f` fallback on the header `<div>` so it degrades to solid navy.
- **Gmail:** Strips `<style>` blocks in some contexts. All critical styles should also be inlined on the elements. The current HTML already uses inline styles as primary, `<style>` block as enhancement.
- **Dark mode:** Body text (Gray 600) has enough contrast on both white and dark backgrounds. The Primary 50 guide box may invert — consider adding `color-scheme: light` meta tag or testing in Gmail/Apple Mail dark mode.
- **Mobile:** The 560px max-width wrapper should be fluid on mobile. Ensure the CTA button is minimum 44px tap target (current: 14px padding + 15px text ≈ 43px — bump to `padding: 16px 36px` if needed).
- **Image-free:** This email uses zero images. No alt-text concerns. Renders fully without image loading.

---

## Testing Checklist

Before going live, send test emails to verify:
- [ ] CTA button links to correct PDF URL
- [ ] Name personalization renders correctly
- [ ] Guide title renders without wrapping issues
- [ ] Unsubscribe link works
- [ ] Renders properly in Gmail (web + mobile)
- [ ] Renders properly in Outlook (Windows)
- [ ] Renders properly in Apple Mail
- [ ] Dark mode appearance is acceptable
- [ ] Physical address is visible in footer
- [ ] PDF actually downloads when clicking the button
