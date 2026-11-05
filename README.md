# Penguin website

The landing page, privacy policy, terms, and support pages for the Penguin iOS app.
Plain HTML and CSS. No JavaScript, no build step, no third-party requests.

## Edit

Pages live in `public/`. Every page uses `public/assets/css/site.css`.
Preview locally:

    python3 -m http.server 8000 -d public

Then open http://localhost:8000. Before committing, run the checks:

    python3 scripts/check.py

## Rename the app

The site calls the app "Penguin." When the final name is picked, replace it in:
- every `<title>` and the `.logo` link text in each page in `public/`
- the `.wordmark` heading in `public/index.html`
- the `og:title` tag in `public/index.html`
- "the Penguin app" in `public/privacy/index.html` and `public/terms/index.html`
- "Settings › Privacy & Security › Health › Penguin" and "turn on Penguin" in the privacy and support pages (these must match the app's display name)

Find them all with: `grep -rn "Penguin" public --include=*.html`

## Images

Art comes from the app repo. Regenerate after art changes (the script can be run from any directory):

    scripts/optimize-images.sh "../Pedometer Penguin"

Needs `brew install webp`. Keep the home page's first load under 600 KB (`scripts/check.py` enforces it).

## Hosting

DigitalOcean App Platform, static site, free tier (up to 3 static-only apps, each with 1 GiB of outbound transfer per month; then $0.02 per GiB; checked 2026-11-05).
The spec is in `.do/app.yaml`. Only `public/` is served. Pushing to `main` redeploys.

## Launch checklist

1. Replace `{{SUPPORT_EMAIL}}`, `{{PUBLISHER_NAME}}`, `{{GOVERNING_LAW}}` in `public/`, `{{SITE_URL}}` (in `public/index.html`), and `{{GITHUB_REPO}}` in `.do/app.yaml`.
2. `python3 scripts/check.py --launch` passes.
3. Have someone qualified review the privacy policy and terms.
4. Add the custom domain in App Platform. Set `{{SITE_URL}}` to that domain (e.g. https://example.com, no trailing slash).
5. In App Store Connect, set the Privacy Policy URL to `https://<domain>/privacy/` and the Support URL to `https://<domain>/support/`. Keep Apple's standard EULA (our terms add to it). Link the terms from the app description or the app's Settings.
6. Once the listing is live, turn both the hero and footer "Coming soon" badges in `public/index.html` into real App Store links, using Apple's official badge artwork per Apple's marketing guidelines.
7. Update the “Last updated” dates in `public/privacy/index.html` and `public/terms/index.html`.
8. Re-check the privacy policy against the app whenever Waddles, notifications, purchases, or Health access change.
