#!/usr/bin/env bash
# Turns chosen app art into small WebP files for the site.
# Usage: scripts/optimize-images.sh [path-to-Pedometer-Penguin-repo]
# Needs cwebp (brew install webp) and macOS sips. Works from any directory.
set -euo pipefail

APP_REPO="$(cd "${1:-$(dirname "$0")/../../Pedometer Penguin}" && pwd)"
cd "$(dirname "$0")/.."
ART="$APP_REPO/Art"
XC="$APP_REPO/App/Assets.xcassets"
OUT="public/assets/img"
mkdir -p "$OUT"
command -v cwebp >/dev/null || { echo "Install cwebp first: brew install webp"; exit 1; }

# webp <source.png> <output-name> <width>...   -> $OUT/<output-name>-<width>.webp
webp() {
  local src="$1" name="$2"; shift 2
  [[ -f "$src" ]] || { echo "Missing source: $src"; exit 1; }
  local srcw
  srcw=$(sips -g pixelWidth "$src" | awk '/pixelWidth/ {print $2}')
  [[ -n "$srcw" ]] || { echo "Can't read width of $src"; exit 1; }
  for w in "$@"; do
    (( w <= srcw )) || { echo "Refusing to upscale $src ($srcw px) to $w px"; exit 1; }
    cwebp -quiet -q 78 -alpha_q 80 -m 6 -resize "$w" 0 "$src" -o "$OUT/$name-$w.webp"
  done
}

# Hero (also the locker's default pose and the "classified" athlete silhouette)
webp "$ART/penguin/penguin-waddler-smug.png" waddler-smug 480 800

# Glow-up, how-it-works, 404
for pose in couch-slumped couch-shocked couch-resting waddler-hyped waddler-neutral waddler-celebrating; do
  webp "$ART/penguin/penguin-$pose.png" "$pose" 320 640
done

# Locker: outfit poses + item icons
for item in crown gold-chain cowboy-hat party-hat heart-shades cape bucket-hat halo; do
  webp "$XC/penguin-waddler-smug-$item.imageset/penguin-waddler-smug-$item.png" "fit-$item" 360 720
  webp "$ART/items/item-$item.png" "item-$item" 96 192
done

# Expedition landmarks
for spot in couch-border fridge krill-shack runway afterparty podium; do
  webp "$ART/landmarks/landmark-$spot-source.png" "landmark-$spot" 320 640
done

# Small app icon for the header logo and notification cards
webp "$ART/app-icon-source.png" icon 80

# PNG icons for browsers and link previews
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
sips -z 32 32 "$ART/app-icon-source.png" --out public/assets/favicon-32.png >/dev/null
sips -z 180 180 "$ART/app-icon-source.png" --out public/assets/apple-touch-icon.png >/dev/null
sips -z 630 630 "$ART/app-icon-source.png" --out "$tmp/og-square.png" >/dev/null
sips -p 630 1200 --padColor 8CE0ED "$tmp/og-square.png" --out "$tmp/og-image.png" >/dev/null
sips -s format jpeg -s formatOptions 82 "$tmp/og-image.png" --out public/assets/og-image.jpg >/dev/null

# Hero idle loop (the couch bird, stage 1): key out the green screen (same recipe as the app's scripts/key-idle-clip.sh)
command -v ffmpeg >/dev/null || { echo "Install ffmpeg first: brew install ffmpeg"; exit 1; }
CLIP="$APP_REPO/Art/clips/idle-couch-smug-green.mp4"
VID="public/assets/video"
mkdir -p "$VID"
KEY="chromakey=0x00FF00:0.30:0.08,despill=type=green:mix=0.6:expand=0.2,format=rgba,lutrgb=a='if(lt(val\\,24)\\,0\\,val)'"
# WebM (VP9 with alpha) for Chrome, Firefox and Edge
ffmpeg -v error -y -i "$CLIP" -vf "$KEY" -c:v libvpx-vp9 -pix_fmt yuva420p -b:v 0 -crf 40 -row-mt 1 -an "$VID/hero-idle.webm"
# HEVC with alpha for Safari, which can't show WebM transparency
ffmpeg -v error -y -i "$CLIP" -vf "$KEY,premultiply=inplace=1,format=bgra" \
  -c:v hevc_videotoolbox -alpha_quality 0.4 -q:v 45 -tag:v hvc1 -an "$VID/hero-idle.mov"
# First frame: the video poster and the still shown when motion is reduced
ffmpeg -v error -y -i "$CLIP" -vf "$KEY" -frames:v 1 "$tmp/hero-poster.png"
cwebp -quiet -q 78 -alpha_q 80 -m 6 "$tmp/hero-poster.png" -o "$OUT/hero-poster-640.webp"
echo "Hero video: $(du -h "$VID/hero-idle.webm" | cut -f1) webm, $(du -h "$VID/hero-idle.mov" | cut -f1) mov"

# The hero's four friends, each doing something different. Same key; cropped to one shared box
# (so they stay the same size as each other) and kept small so the home page's first load stays under budget.
FRIEND_CROP="crop=628:628:6:5,scale=360:360:flags=lanczos"
for pair in "priya:idle-waddler-neutral-matching-set-green" "mads:idle-waddler-neutral-pa-tote-green" \
            "sam:idle-waddler-neutral-varsity-green" "jo:idle-waddler-sleepy-green"; do
  name=${pair%%:*}; src="$APP_REPO/Art/clips/${pair##*:}.mp4"
  ffmpeg -v error -y -i "$src" -vf "$KEY,$FRIEND_CROP" -c:v libvpx-vp9 -pix_fmt yuva420p -b:v 0 -crf 42 -row-mt 1 -an "$VID/friend-$name.webm"
  ffmpeg -v error -y -i "$src" -vf "$KEY,$FRIEND_CROP,premultiply=inplace=1,format=bgra" \
    -c:v hevc_videotoolbox -alpha_quality 0.3 -q:v 30 -tag:v hvc1 -an "$VID/friend-$name.mov"
  ffmpeg -v error -y -i "$src" -vf "$KEY,$FRIEND_CROP" -frames:v 1 "$tmp/friend-$name.png"
  cwebp -quiet -q 72 -alpha_q 75 -m 6 "$tmp/friend-$name.png" -o "$OUT/friend-$name-360.webp"
done
echo "Friend videos: $(du -ch "$VID"/friend-*.mov | tail -1 | cut -f1) mov total"

echo "Generated $(ls "$OUT" | wc -l | tr -d ' ') WebP files:"
du -ch "$OUT"/*.webp | tail -1
echo "Largest:"
ls -lS "$OUT" | sed -n 2,6p
