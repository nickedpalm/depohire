# DepoHire — Monetization Components
# Installation Guide
# Generated March 2026
#
# ─────────────────────────────────────────────
# STEP 1: Copy new components into your project
# ─────────────────────────────────────────────
# From your project root (/tmp/depohire-build/):

cp ~/Desktop/depohire-src/_new-components/QuoteForm.astro src/components/directory/QuoteForm.astro
cp ~/Desktop/depohire-src/_new-components/ExitIntent.astro src/components/directory/ExitIntent.astro
cp ~/Desktop/depohire-src/_new-components/BlogEmailCTA.astro src/components/directory/BlogEmailCTA.astro
cp ~/Desktop/depohire-src/_new-components/CityCTA.astro src/components/directory/CityCTA.astro
cp ~/Desktop/depohire-src/_new-components/subscribe.ts functions/subscribe.ts  # create functions/ dir first: mkdir -p functions
cp ~/Desktop/depohire-src/lib/listmonk.ts src/lib/listmonk.ts


# ─────────────────────────────────────────────
# STEP 2: Wire into [city].astro
# ─────────────────────────────────────────────
# In src/pages/[city].astro, add to imports (top of frontmatter):
#
#   import QuoteForm from '~/components/directory/QuoteForm.astro';
#
# Then add the component ABOVE the listing cards grid, after the map:
# Find this line:
#   {listings.length > 0 ? (
# Add BEFORE it:
#   <div class="mb-8">
#     <QuoteForm city={cityInfo.city} state={cityInfo.state} citySlug={cityInfo.slug} />
#   </div>


# ─────────────────────────────────────────────
# STEP 3: Wire into listing/[slug].astro
# ─────────────────────────────────────────────
# In src/pages/listing/[slug].astro, add to imports:
#
#   import ExitIntent from '~/components/directory/ExitIntent.astro';
#
# REPLACE the existing ContactForm block:
#   <div class="mt-8">
#     <ContactForm listingName={listing.name} listingEmail={listing.email} />
#   </div>
#
# WITH:
#   <div class="mt-8">
#     <QuoteForm
#       city={cityInfo?.city || listing.city}
#       state={listing.state}
#       citySlug={listing.city}
#       listingName={listing.name}
#       listingSlug={listing.slug}
#       mode="listing"
#     />
#   </div>
#
# And add ExitIntent just before </PageLayout>:
#   <ExitIntent city={cityInfo?.city} citySlug={listing.city} />


# ─────────────────────────────────────────────
# STEP 4: Wire into blog/[...slug].astro
# ─────────────────────────────────────────────
# Add to imports:
#   import BlogEmailCTA from '~/components/directory/BlogEmailCTA.astro';
#
# In the sidebar section, REPLACE this block:
#   <div class="card p-5 bg-accent-50 border-accent-200">
#     <p class="font-semibold text-gray-900 text-sm">Find a {config.primaryKeyword}</p>
#     <p class="text-xs text-gray-600 mt-1">Browse certified professionals near you</p>
#     <a href="/states/all/" class="btn-primary text-sm mt-3 w-full">Search Directory</a>
#   </div>
#
# WITH:
#   <BlogEmailCTA />
#
# Also add after the mobile AuthorBox:
#   <BlogEmailCTA compact />


# ─────────────────────────────────────────────
# STEP 5: Cloudflare Pages Environment Variables
# ─────────────────────────────────────────────
# Go to: Cloudflare Dashboard → Pages → depohire → Settings → Environment Variables
# Add these (Production + Preview):
#
#   LISTMONK_URL         https://YOUR_VPS_DOMAIN
#   LISTMONK_API_KEY     [run in terminal: node -e "console.log(btoa('admin:YOURPASSWORD'))"]
#   LISTMONK_LIST_ID     1   (or whatever your main list ID is in Listmonk)


# ─────────────────────────────────────────────
# STEP 6: Build and deploy
# ─────────────────────────────────────────────
cd /tmp/depohire-build
npm run build
npx wrangler pages deploy dist --project-name depohire


# ─────────────────────────────────────────────
# STEP 7: Test the subscribe endpoint
# ─────────────────────────────────────────────
# After deploy, test from terminal:
# curl -X POST https://depohire.com/subscribe \
#   -H "Content-Type: application/json" \
#   -d '{"email":"test@example.com","city":"New York","source":"test"}'
# Expected: {"ok":true}


# ─────────────────────────────────────────────
# STEP 8: Create lead magnet PDFs (low effort)
# ─────────────────────────────────────────────
# Create these two simple PDFs and place in /tmp/depohire-build/public/downloads/:
#   deposition-prep-checklist.pdf     (for exit intent)
#   deposition-hiring-checklist.pdf   (for blog sidebar)
# Claude can generate the content for both — just ask!


# ─────────────────────────────────────────────
# FUTURE: Featured listings
# ─────────────────────────────────────────────
# To mark a listing as featured, edit its JSON file:
# e.g. data/listings/new-york.json — set "featured": true for 1-3 listings per city
# Featured listings already sort first in [city].astro (see existing featured logic)
# Style them differently by updating ListingCard.astro to check listing.featured
