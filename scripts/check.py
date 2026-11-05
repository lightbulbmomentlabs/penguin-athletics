#!/usr/bin/env python3
"""Checks for the Penguin website. Standard library only, nothing to install.

  python3 scripts/check.py                    check every page
  python3 scripts/check.py --only index.html  check one page (path inside public/)
  python3 scripts/check.py --launch           also fail on unfilled {{PLACEHOLDERS}}
"""
import argparse
import os
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent / "public"
PAGES = ["index.html", "404.html", "privacy/index.html", "terms/index.html", "support/index.html"]
HOME_FIRST_LOAD_BUDGET = 600 * 1024  # bytes, from the spec
HOME_FULL_SCROLL_WARN = 1200 * 1024
EXTERNAL = re.compile(r"^\s*(https?:)?//", re.I)
PLACEHOLDER = re.compile(r"\{\{[A-Z0-9_]+\}\}")
CSS_URL = re.compile(r"url\(\s*['\"]?([^'\")]+)")
BANNED_TAGS = {"script", "iframe", "embed", "object", "audio", "form", "base"}


class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.lang = None
        self.title = ""
        self._in_title = False
        self.description = None
        self.h1 = 0
        self.banned = []
        self.handlers = []
        self.imgs = []
        self.anchors = []
        self.links = []
        self.ids = set()
        self.label_fors = []
        self.videos = []  # (video attrs, [source attrs])

    def handle_starttag(self, tag, attrs):
        a = {k: (v or "") for k, v in attrs}
        if "id" in a:
            self.ids.add(a["id"])
        self.handlers += [f"<{tag} {k}>" for k in a if k.startswith("on")]
        if tag in BANNED_TAGS:
            self.banned.append(tag)
        if tag == "html":
            self.lang = a.get("lang")
        elif tag == "title":
            self._in_title = True
        elif tag == "meta" and a.get("name") == "description":
            self.description = a.get("content")
        elif tag == "h1":
            self.h1 += 1
        elif tag == "img":
            self.imgs.append(a)
        elif tag == "a" and "href" in a:
            self.anchors.append(a["href"])
        elif tag == "link":
            self.links.append(a)
        elif tag == "label" and "for" in a:
            self.label_fors.append(a["for"])
        elif tag == "video":
            self.videos.append((a, []))
        elif tag == "source" and self.videos:
            self.videos[-1][1].append(a)

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False

    def handle_data(self, data):
        if self._in_title:
            self.title += data


def resolve(url, base):
    """Map a site URL to a file inside public/. None for in-page anchors."""
    url = url.split("#")[0].split("?")[0]
    if not url:
        return None
    target = SITE / url.lstrip("/") if url.startswith("/") else base.parent / url
    if url.endswith("/") or target.is_dir():
        target = target / "index.html"
    return target


def exists_exact(path):
    """True if path is a file inside public/ and every component matches case exactly.

    macOS is case-insensitive but the deploy host is Linux, so Img/A.png must not
    pass for img/a.png. Anything that resolves outside public/ counts as missing.
    """
    path = Path(os.path.abspath(path))
    if not path.exists():
        return False
    try:
        path.resolve().relative_to(SITE.resolve())
        parts = path.relative_to(SITE).parts
    except ValueError:
        return False
    here = SITE
    for part in parts:
        if part not in os.listdir(here):
            return False
        here = here / part
    return True


def urls_of(img):
    """Every URL an <img> may load: all srcset entries plus the fallback src."""
    urls = [c.strip().split()[0] for c in img.get("srcset", "").split(",") if c.strip()]
    if img.get("src"):
        urls.append(img["src"])
    return urls


def video_urls(video, sources):
    """Every URL a <video> may load: its poster and each <source>."""
    return [u for u in [video.get("poster", ""), video.get("src", "")] + [s.get("src", "") for s in sources] if u]


def file_key(url, base):
    """Resolved path of an existing, exact-case site file, or None."""
    f = resolve(url, base)
    return Path(os.path.abspath(f)) if f and exists_exact(f) else None


def css_urls(text):
    """url() targets in CSS that point at files (no #fragments, no data:)."""
    out = (u.strip() for u in CSS_URL.findall(text))
    return [u for u in out if u and not u.startswith(("#", "data:"))]


def report_weight(path, raw, page, errors, warnings):
    first = len(raw.encode("utf-8"))
    sheets, assets = set(), set()
    for link in page.links:
        if "stylesheet" in link.get("rel", ""):
            f = file_key(link.get("href", ""), path)
            if f and f not in sheets:
                sheets.add(f)
                first += f.stat().st_size
                for u in css_urls(f.read_text(encoding="utf-8")):
                    a = file_key(u, f)
                    if a and a not in assets:
                        assets.add(a)
                        first += a.stat().st_size
    eager = {}  # file -> True if any occurrence is not lazy
    for img in page.imgs:
        files = [f for f in (file_key(u, path) for u in urls_of(img)) if f]
        if not files:
            continue
        biggest = max(files, key=lambda f: f.stat().st_size)
        eager[biggest] = eager.get(biggest, False) or img.get("loading") != "lazy"
    for video, sources in page.videos:  # autoplay loads now; count the biggest source plus the poster
        poster = file_key(video.get("poster", ""), path) if video.get("poster") else None
        if poster:
            eager[poster] = True
        files = [f for f in (file_key(s.get("src", ""), path) for s in sources) if f]
        if files:
            eager[max(files, key=lambda f: f.stat().st_size)] = True
    lazy = 0
    for f, is_eager in eager.items():
        if is_eager:
            first += f.stat().st_size
        else:
            lazy += f.stat().st_size
    full = first + lazy
    print(f"Home page: first load {first / 1024:.0f} KB, full scroll {full / 1024:.0f} KB "
          "(worst case: largest image of every srcset, the larger hero video, and the woff2 "
          "font, which Safari skips in favor of the system rounded font)")
    if first > HOME_FIRST_LOAD_BUDGET:
        errors.append(f"index.html: first load {first // 1024} KB is over the 600 KB budget")
    if full > HOME_FULL_SCROLL_WARN:
        warnings.append(f"index.html: full scroll {full // 1024} KB is over 1200 KB")


def check_page(rel, errors, warnings, launch):
    path = SITE / rel
    if not exists_exact(path):
        errors.append(f"{rel}: page is missing")
        return
    raw = path.read_text(encoding="utf-8")
    page = Page()
    page.feed(raw)

    if page.lang != "en":
        errors.append(f'{rel}: <html> needs lang="en"')
    if not page.title.strip():
        errors.append(f"{rel}: missing <title>")
    if not page.description:
        errors.append(f"{rel}: missing meta description")
    if page.h1 != 1:
        errors.append(f"{rel}: needs exactly one <h1>, found {page.h1}")
    for tag in page.banned:
        errors.append(f"{rel}: <{tag}> is not allowed (no JS, no embeds)")
    for handler in page.handlers:
        errors.append(f"{rel}: inline JS handler {handler}")
    for target in page.label_fors:
        if target not in page.ids:
            errors.append(f'{rel}: <label for="{target}"> has no matching id')
    for u in css_urls(raw):
        if EXTERNAL.match(u):
            errors.append(f"{rel}: external url() {u}")

    for img in page.imgs:
        name = img.get("src", "?")
        if "alt" not in img:
            errors.append(f"{rel}: <img {name}> missing alt")
        if not img.get("width") or not img.get("height"):
            errors.append(f"{rel}: <img {name}> missing width/height")
        for u in urls_of(img):
            if EXTERNAL.match(u):
                errors.append(f"{rel}: external image {u}")
                continue
            target = resolve(u, path)
            if target and not exists_exact(target):
                errors.append(f"{rel}: missing image {u}")

    for video, sources in page.videos:
        for need in ("muted", "playsinline"):
            if need not in video:
                errors.append(f"{rel}: <video> needs {need} (autoplay rules)")
        if not video.get("width") or not video.get("height"):
            errors.append(f"{rel}: <video> missing width/height")
        for u in video_urls(video, sources):
            if EXTERNAL.match(u):
                errors.append(f"{rel}: external video {u}")
                continue
            target = resolve(u, path)
            if target and not exists_exact(target):
                errors.append(f"{rel}: missing video file {u}")

    for link in page.links:
        href = link.get("href", "")
        if EXTERNAL.match(href):
            errors.append(f"{rel}: external <link> {href}")
            continue
        target = resolve(href, path) if href else None
        if target and not exists_exact(target):
            errors.append(f"{rel}: missing <link> target {href}")

    for href in page.anchors:
        if href.startswith("#"):
            if len(href) > 1 and href[1:] not in page.ids:
                errors.append(f"{rel}: broken in-page anchor {href}")
            continue
        if href.startswith(("mailto:", "tel:")) or EXTERNAL.match(href):
            continue
        target = resolve(href, path)
        if target and not exists_exact(target):
            errors.append(f"{rel}: broken link {href}")

    if rel == "404.html":  # served at any depth, so internal URLs must start with /
        urls = list(page.anchors) + [l.get("href", "") for l in page.links]
        for img in page.imgs:
            urls += urls_of(img)
        for video, sources in page.videos:
            urls += video_urls(video, sources)
        for u in urls:
            if u and not u.startswith(("/", "#", "mailto:", "tel:", "data:")) and not EXTERNAL.match(u):
                errors.append(f"{rel}: internal URL must be root-absolute: {u}")

    for ph in sorted(set(PLACEHOLDER.findall(raw))):
        (errors if launch else warnings).append(f"{rel}: unfilled {ph}")

    if rel == "index.html":
        report_weight(path, raw, page, errors, warnings)


def check_app_yaml(errors, warnings, launch):
    f = SITE.parent / ".do" / "app.yaml"
    if f.exists():
        for ph in sorted(set(PLACEHOLDER.findall(f.read_text(encoding="utf-8")))):
            (errors if launch else warnings).append(f".do/app.yaml: unfilled {ph}")


def check_assets(errors):
    for css in sorted(SITE.glob("assets/css/*.css")):
        text = css.read_text(encoding="utf-8")
        if "@import" in text:
            errors.append(f"{css.name}: @import adds a request; put everything in one file")
        for u in css_urls(text):
            if EXTERNAL.match(u):
                errors.append(f"{css.name}: external url() {u}")
                continue
            target = resolve(u, css)
            if target and not exists_exact(target):
                errors.append(f"{css.name}: missing file {u}")
    for js in SITE.rglob("*.js"):
        errors.append(f"{js.relative_to(SITE)}: no JavaScript files allowed")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", action="append", help="page path inside public/")
    parser.add_argument("--launch", action="store_true", help="fail on unfilled placeholders")
    args = parser.parse_args()

    errors, warnings = [], []
    pages = args.only or PAGES + sorted(
        p.relative_to(SITE).as_posix() for p in SITE.rglob("*.html")
        if p.relative_to(SITE).as_posix() not in PAGES)
    for rel in pages:
        check_page(rel, errors, warnings, args.launch)
    check_app_yaml(errors, warnings, args.launch)
    check_assets(errors)

    for w in warnings:
        print("warn:", w)
    for e in errors:
        print("FAIL:", e)
    if errors:
        sys.exit(1)
    print("All checks passed.")


if __name__ == "__main__":
    main()
