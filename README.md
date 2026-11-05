# Penguin website

The landing page, privacy policy, terms, and support pages for the Penguin iOS app.
Plain HTML and CSS. No JavaScript, no build step, no third-party requests.

## Edit

Pages live in `public/`. Every page uses `public/assets/css/site.css`.
Preview locally:

    python3 -m http.server 8000 -d public

Then open http://localhost:8000. Before committing, run the checks:

    python3 scripts/check.py

## Search, sharing, and AI crawlers

Every page has a canonical URL, keywords, Open Graph and Twitter card tags, and JSON-LD
structured data (Organization, WebSite, MobileApplication, FAQPage on the home page,
WebPage plus breadcrumbs on the others). `public/robots.txt`, `public/sitemap.xml`, and
`public/llms.txt` help search engines and AI crawlers. The site URL is
`https://penguinathletics.com`; it's also `SITE_URL` in `scripts/check.py`.

- **Share image:** `public/assets/og-image.jpg` (1200x630), rendered from `scripts/og/og.html`.
  Edit that file, then run `scripts/make-og-image.sh` (needs Google Chrome).
- **FAQ:** if you change a FAQ question on the home page, update the matching `FAQPage`
  entry in its JSON-LD. `scripts/check.py` fails if they drift apart.
- **Sitemap:** add new pages to `public/sitemap.xml` and bump `lastmod` when pages change.

## Rename the app

The site calls the app "Penguin" (site name "Penguin Athletics"). If that changes, update
titles, the `.logo` text, the `.wordmark`, the JSON-LD `name` fields, `llms.txt`, and the
Health/Motion settings paths in the privacy and support pages (they must match the app's
display name). Find them with: `grep -rn "Penguin" public`

## Images

Art comes from the app repo. Regenerate after art changes (the script can be run from any directory):

    scripts/optimize-images.sh "../Pedometer Penguin"

Needs `brew install webp ffmpeg`. It also builds the hero's moving penguin: the app's `idle-waddler-smug-green.mp4` with the green screen removed, as `public/assets/video/hero-idle.webm` (Chrome, Firefox) and `hero-idle.mov` (Safari, HEVC with transparency). Keep the home page's first load under 600 KB (`scripts/check.py` enforces it).

## Hosting

DigitalOcean App Platform, static site, free tier (up to 3 static-only apps, each with 1 GiB of outbound transfer per month; then $0.02 per GiB; checked 2026-11-05).
The spec is in `.do/app.yaml`. Only `public/` is served. Pushing to `main` redeploys.

## Launch checklist

Done: publisher, contact email, governing law, domain, and GitHub repo are filled in, and
`python3 scripts/check.py --launch` passes.

1. Create the app in DigitalOcean App Platform from `.do/app.yaml`, then add the custom domain `penguinathletics.com` (and `www`) and point DNS at it.
2. Set up the `hello@penguinathletics.com` mailbox or forwarding.
3. Have someone qualified review the privacy policy and terms.
4. In App Store Connect, set the Privacy Policy URL to `https://penguinathletics.com/privacy/` and the Support URL to `https://penguinathletics.com/support/`. Keep Apple's standard EULA (our terms add to it). Link the terms from the app description or the app's Settings.
5. Submit `https://penguinathletics.com/sitemap.xml` in Google Search Console and Bing Webmaster Tools.
6. Once the listing is live, turn both "Coming soon" badges in `public/index.html` into real App Store links using Apple's official badge artwork, and add `offers` and the App Store URL to the `MobileApplication` JSON-LD.
7. Check the home page's roast wall and the privacy policy's Notifications section against the shipped app (walking reminders, caps, quiet hours).
8. Update the “Last updated” dates in the privacy policy and terms whenever they change, and re-check the privacy policy whenever Waddles, notifications, purchases, or Health access change.
