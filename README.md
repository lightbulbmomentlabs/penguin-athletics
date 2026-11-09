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

## Learn (walking-health articles)

Articles live in `content/learn/<slug>.md` (Markdown with a short header). The builder turns
them into pages under `public/learn/`, plus the Learn hub, five topic pages, the RSS feed
(`/learn/feed.xml`), the sitemap, the Learn section of `llms.txt`, and the "Walking,
explained" band on the home page. The generated HTML is committed, so hosting stays a
plain static site.

    python3 scripts/build_learn.py              # rebuild after editing anything in content/
    python3 -m unittest scripts/test_learnlib.py
    python3 scripts/check.py                    # fails if the build is stale or a citation is broken

- **Rules:** `content/STYLE.md` (evidence, safety, voice, format). Public version:
  `/learn/editorial-policy/`.
- **Topics:** `content/backlog.md`, worked top to bottom. Topics: `content/pillars.json`.
- **Daily drafts:** a scheduled Claude job follows `content/DAILY.md`: it drafts the next
  backlog topic and opens a pull request with a claim-by-claim source table. Review it,
  merge it, and DigitalOcean publishes it. Nothing publishes without a merge.
- **Reviewing a draft:** read the short answer and Gary's line, spot-check two or three
  claims against the sources table, and skim for anything that sounds like medical advice
  or body talk.
- **Share images:** `scripts/make_learn_og.py` renders `public/assets/og/learn*.jpg`
  (needs Google Chrome). Rerun after changing `content/pillars.json`.
- **Medical reviewer:** add `reviewed_by: Name, credentials` to an article once a qualified
  person has actually reviewed it. The page then shows "Reviewed by" and the structured
  data includes it.

## Rename the app

The site calls the app "Penguin" (site name "Penguin Athletics"). If that changes, update
titles, the `.logo` text, the `.wordmark`, the JSON-LD `name` fields, `llms.txt`, and the
Health/Motion settings paths in the privacy and support pages (they must match the app's
display name). Find them with: `grep -rn "Penguin" public`

## Images

Art comes from the app repo. Regenerate after art changes (the script can be run from any directory):

    scripts/optimize-images.sh "../Pedometer Penguin"

Needs `brew install webp ffmpeg`. It also builds the hero's moving penguin: the app's `idle-couch-smug-green.mp4` (the pudgy stage-1 couch bird) with the green screen removed, as `public/assets/video/hero-idle.webm` (Chrome, Firefox) and `hero-idle.mov` (Safari, HEVC with transparency). Keep the home page's first load under 600 KB (`scripts/check.py` enforces it).

## Device images

The homepage's device group (`public/assets/img/device-*.webp`) uses Apple's official
Product Bezels (Apple Design Resources) with real app screens captured from the iPhone 18 Pro,
iPhone Duo, and Apple Watch simulators (`-previewUser -todaySteps 7400`, status bar at 9:41).
Apple's license for those bezels is in each bezel download.

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
