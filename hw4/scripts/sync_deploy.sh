#!/bin/sh
# Push the current code + the ORIGINAL data pack + the built website to the PRIVATE deploy repo that Render builds from.
# Usage (from hw4/):  sh scripts/sync_deploy.sh "path/to/data pack.zip"
# The public repo is untouched: the data pack and the build only ever go to the private repo.
set -e
PACK="${1:?usage: sh scripts/sync_deploy.sh <data pack zip>}"
HERE="$(cd "$(dirname "$0")/.." && pwd)"          # hw4/
REPO="$(cd "$HERE/.." && pwd)"                    # repo root
WORK="$(mktemp -d)"
echo "Building the website…"; (cd "$HERE/frontend" && npm run build >/dev/null)
echo "Preparing the deploy copy in $WORK"
git -C "$REPO" archive HEAD | tar -x -C "$WORK"
unzip -q -o "$PACK" -d "$WORK/unzipped"
DB="$(find "$WORK/unzipped" -name campus_customs.db | head -1)"; PHOTOS="$(dirname "$DB")/products"
cp "$DB" "$WORK/hw4/data/campus_customs.db"
cp "$PHOTOS"/*.jpg "$WORK/hw4/data/products/"
mkdir -p "$WORK/hw4/frontend/dist" && cp -R "$HERE/frontend/dist/." "$WORK/hw4/frontend/dist/"
rm -rf "$WORK/unzipped"
cd "$WORK"
git init -q -b main
git add -A && git add -f hw4/data/campus_customs.db hw4/data/products/*.jpg hw4/frontend/dist
git -c user.name="Dr_BMo" -c user.email="$(git -C "$REPO" config user.email)" commit -q -m "Deploy: $(git -C "$REPO" rev-parse --short HEAD) + data pack + built site"
git push -q -f "git@github.com:dr-bmo2255/mgt409e-hw4-deploy.git" main
echo "Pushed to the private deploy repo. Render redeploys automatically."
rm -rf "$WORK"
