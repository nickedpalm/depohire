#!/usr/bin/env bash
# Deploy a vertical to Cloudflare Pages
# Usage: ./scripts/deploy.sh <vertical-slug> [--project-name <name>]
set -euo pipefail

VERTICAL="${1:?Usage: deploy.sh <vertical-slug>}"
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VERTICAL_DIR="$PROJECT_ROOT/verticals/$VERTICAL"
DIST_DIR="$VERTICAL_DIR/dist"

if [ ! -d "$VERTICAL_DIR" ]; then
    echo "Error: Vertical directory not found: $VERTICAL_DIR"
    exit 1
fi

if [ ! -d "$DIST_DIR" ]; then
    echo "Error: Build output not found. Run 'factory.py build --vertical $VERTICAL' first."
    exit 1
fi

# Default project name is the vertical slug
PROJECT_NAME="${2:-$VERTICAL}"

echo "Deploying $VERTICAL to Cloudflare Pages..."
echo "  Project: $PROJECT_NAME"
echo "  Source: $DIST_DIR"
echo ""

npx wrangler pages deploy "$DIST_DIR" --project-name "$PROJECT_NAME"

echo ""
echo "Deploy complete!"
