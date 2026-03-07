#!/usr/bin/env bash
# depohire deploy script
# Usage: ./scripts/depohire-deploy.sh
# Syncs src + functions, builds, copies functions into dist, deploys to Cloudflare Pages

set -euo pipefail

SRC="/Users/nick/Desktop/depohire-src"
BUILD="/tmp/depohire-build"

echo "=== DepoHire Deploy ==="

# 1. Sync source files into build dir
echo "→ Syncing source..."
rsync -a "$SRC/src/" "$BUILD/src/"
rsync -a "$SRC/functions/" "$BUILD/functions/"

# 2. Build
echo "→ Building..."
cd "$BUILD" && npm run build 2>&1 | tail -3

# 3. Copy functions into dist (required for wrangler pages deploy)
echo "→ Copying functions into dist..."
cp -r "$BUILD/functions" "$BUILD/dist/functions"

# 4. Deploy
echo "→ Deploying..."
cd "$BUILD/dist" && npx wrangler pages deploy . \
  --project-name depohire \
  --branch main \
  --commit-dirty=true 2>&1 | tail -3

echo "=== Done ==="
