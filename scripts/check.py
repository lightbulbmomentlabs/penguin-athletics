#!/usr/bin/env python3
"""Checks for the Penguin website. Standard library only, nothing to install.

  python3 scripts/check.py                    check every page
  python3 scripts/check.py --only index.html  check one page (path inside public/)
  python3 scripts/check.py --launch           also fail on unfilled {{PLACEHOLDERS}}
"""
import argparse
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent / "public"
PAGES = ["index.html", "404.html", "privacy/index.html", "terms/index.html", "support/index.html"]
HOME_FIRST_LOAD_BUDGET = 600 * 1024  # bytes, from the spec
HOME_FULL_SCROLL_WARN = 1200 * 1024
EXTERNAL = re.compile(r"^\s*(https?:)?//", re.I)
PLACEHOLDER = re.compile(r"\{\{[A-Z_]+\}\}")
CSS_URL = re.compile(r"url\(\s*['\"]?([^'\")]+)")
BANNED_TAGS = {"script", "iframe", "embed", "object", "video", "audio"}


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


def candidates(img):
    urls = [c.strip().split()[0] for c in img.get("srcset", "").split(",") if c.strip()]
    return urls or ([img["src"]] if img.get("src") else [])


def size(url, base):
    f = resolve(url, base)
    return f.stat().st_size if f and f.exists() else 0


def report_weight(path, raw, page, errors, warnings):
    first = len(raw.encode("utf-8"))
    for link in page.links:
        if "stylesheet" in link.get("rel", ""):
            first += size(link["href"], path)
    lazy, seen = 0, set()
    for img in page.imgs:
        urls = candidates(img)
        key = tuple(urls)
        if key in seen:
            continue
        seen.add(key)
        biggest = max((size(u, path) for u in urls), default=0)
        if img.get("loading") == "lazy":
            lazy += biggest
        else:
            first += biggest
    full = first + lazy
    print(f"Home page: first load {first / 1024:.0f} KB, full scroll {full / 1024:.0f} KB "
          "(worst case: largest image of every srcset)")
    if first > HOME_FIRST_LOAD_BUDGET:
        errors.append(f"index.html: first load {first // 1024} KB is over the 600 KB budget")
    if full > HOME_FULL_SCROLL_WARN:
        warnings.append(f"index.html: full scroll {full // 1024} KB is over 1200 KB")


def check_page(rel, errors, warnings, launch):
    path = SITE / rel
    if not path.exists():
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
    for u in CSS_URL.findall(raw):
        if EXTERNAL.match(u):
            errors.append(f"{rel}: external url() {u}")

    for img in page.imgs:
        name = img.get("src", "?")
        if "alt" not in img:
            errors.append(f"{rel}: <img {name}> missing alt")
        if not img.get("width") or not img.get("height"):
            errors.append(f"{rel}: <img {name}> missing width/height")
        for u in candidates(img):
            if EXTERNAL.match(u):
                errors.append(f"{rel}: external image {u}")
            elif not resolve(u, path).exists():
                errors.append(f"{rel}: missing image {u}")

    for link in page.links:
        href = link.get("href", "")
        if EXTERNAL.match(href):
            errors.append(f"{rel}: external <link> {href}")
        elif href and not resolve(href, path).exists():
            errors.append(f"{rel}: missing <link> target {href}")

    for href in page.anchors:
        if href.startswith(("mailto:", "tel:", "#")) or EXTERNAL.match(href):
            continue
        target = resolve(href, path)
        if target and not target.exists():
            errors.append(f"{rel}: broken link {href}")

    for ph in sorted(set(PLACEHOLDER.findall(raw))):
        (errors if launch else warnings).append(f"{rel}: unfilled {ph}")

    if rel == "index.html":
        report_weight(path, raw, page, errors, warnings)


def check_assets(errors):
    for css in sorted(SITE.glob("assets/css/*.css")):
        text = css.read_text(encoding="utf-8")
        if "@import" in text:
            errors.append(f"{css.name}: @import adds a request; put everything in one file")
        for u in CSS_URL.findall(text):
            if u.startswith("data:"):
                continue
            if EXTERNAL.match(u):
                errors.append(f"{css.name}: external url() {u}")
            elif not resolve(u, css).exists():
                errors.append(f"{css.name}: missing file {u}")
    for js in SITE.rglob("*.js"):
        errors.append(f"{js.relative_to(SITE)}: no JavaScript files allowed")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", action="append", help="page path inside public/")
    parser.add_argument("--launch", action="store_true", help="fail on unfilled placeholders")
    args = parser.parse_args()

    errors, warnings = [], []
    for rel in args.only or PAGES:
        check_page(rel, errors, warnings, args.launch)
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
