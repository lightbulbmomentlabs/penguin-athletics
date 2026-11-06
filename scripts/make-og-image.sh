#!/usr/bin/env bash
# Renders the 1200x630 share image (Open Graph / Twitter card) from scripts/og/og.html
# with headless Google Chrome, then saves it as public/assets/og-image.jpg.
# Edit og.html to change the copy or layout, then rerun. Works from any directory.
# Optional args: make-og-image.sh <template.html> <output.jpg> (paths relative to the repo root).
set -euo pipefail
cd "$(dirname "$0")/.."

CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
[[ -x "$CHROME" ]] || { echo "Needs Google Chrome in /Applications"; exit 1; }

TEMPLATE="${1:-scripts/og/og.html}"
OUT="${2:-public/assets/og-image.jpg}"

tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

"$CHROME" --headless=new --disable-gpu --hide-scrollbars --force-device-scale-factor=1 \
  --window-size=1200,630 --virtual-time-budget=3000 \
  --screenshot="$tmp/og.png" "file://$PWD/$TEMPLATE" >/dev/null 2>&1

w=$(sips -g pixelWidth "$tmp/og.png" | awk '/pixelWidth/ {print $2}')
h=$(sips -g pixelHeight "$tmp/og.png" | awk '/pixelHeight/ {print $2}')
[[ "$w" == 1200 && "$h" == 630 ]] || { echo "Expected 1200x630, got ${w}x${h}"; exit 1; }

sips -s format jpeg -s formatOptions 85 "$tmp/og.png" --out "$OUT" >/dev/null
echo "$OUT ($(du -h "$OUT" | cut -f1))"
