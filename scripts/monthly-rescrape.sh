#!/usr/bin/env bash
# Monthly re-scrape pipeline for deposition-videographers
# Usage: ./scripts/monthly-rescrape.sh [--deploy]
# Cron: 0 3 1 * * /home/nick/tools/directory-factory/scripts/monthly-rescrape.sh --deploy >> /tmp/rescrape.log 2>&1
#
# Steps:
#   1. Re-scrape all states via Perplexity API
#   2. Enrich with Google Maps data
#   3. Export to JSON
#   4. Build site
#   5. (Optional) Deploy to Cloudflare Pages

set -euo pipefail

FACTORY_DIR="/home/nick/tools/directory-factory"
VERTICAL="deposition-videographers"
VERTICAL_DIR="$FACTORY_DIR/verticals/$VERTICAL"
DEPLOY=false

[[ "${1:-}" == "--deploy" ]] && DEPLOY=true

cd "$FACTORY_DIR"
source .venv/bin/activate

echo "$(date) === Monthly Re-scrape: $VERTICAL ==="

# 1. Re-scrape
echo "$(date) → Scraping via Perplexity API..."
python3 scripts/scrape_perplexity.py --config configs/deposition-videographers.yaml --vertical "$VERTICAL" 2>&1 | tail -5

# 2. Enrich (Google Maps geocoding, website checks)
echo "$(date) → Enriching listings..."
python3 scripts/enrich_places.py --vertical "$VERTICAL" 2>&1 | tail -5

# 3. Export SQLite → JSON
echo "$(date) → Exporting to JSON..."
python3 scripts/export.py --vertical "$VERTICAL" 2>&1 | tail -3

# 4. Build
echo "$(date) → Building site..."
cd "$VERTICAL_DIR"
npm run build 2>&1 | tail -5

# 5. Deploy
if $DEPLOY; then
  echo "$(date) → Deploying to Cloudflare Pages..."
  npx wrangler pages deploy dist \
    --project-name depohire \
    --branch main \
    --commit-dirty=true 2>&1 | tail -5
fi

echo "$(date) === Re-scrape complete ==="
