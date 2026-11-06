"""Parsing and validation for Learn articles (content/learn/*.md). Standard library only.

An article is flat front matter between --- fences, then a Markdown-subset body with two
optional special sections at the end: "## FAQ" (### questions) and "## Sources" (a
numbered list, each line ending in an https URL). See content/STYLE.md for the rules.
"""
import html
import re

REQUIRED = ("title", "pillar", "description", "answer", "published", "keywords", "pose", "gary", "signoff")
STATUSES = ("published", "draft")
SLUG = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
CITE = re.compile(r"\[(\d+)\](?!\()")
LINK = re.compile(r"\[([^\]]+)\]\((https://[^)\s]+|/[^)\s]*)\)")
WORDS = {"cluster": (900, 1800), "pillar": (2000, 3500)}
MAX_DESCRIPTION = 160
MAX_FAQ_QUESTION = 80


def parse_front_matter(text):
    """Return (meta dict, body). Raises ValueError on a malformed header."""
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        raise ValueError("file must start with a --- front matter fence")
    try:
        end = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    except StopIteration:
        raise ValueError("front matter has no closing --- fence") from None
    meta = {}
    for line in lines[1:end]:
        if not line.strip():
            continue
        if ":" not in line:
            raise ValueError(f"front matter line needs 'key: value': {line!r}")
        key, value = line.split(":", 1)
        meta[key.strip()] = value.strip()
    return meta, "\n".join(lines[end + 1:])


def _split_h2(body, name):
    m = re.search(rf"^## {name}\s*$", body, re.M)
    if not m:
        return body, ""
    return body[:m.start()], body[m.end():]


def parse_faq(text):
    """[(question, answer markdown)] from '### Question' blocks."""
    out = []
    for block in re.split(r"^### ", text, flags=re.M)[1:]:
        q, _, a = block.partition("\n")
        out.append((q.strip(), a.strip()))
    return out


def parse_sources(text):
    """[{n, text, url}] from a '1. Citation https://url' list. url is '' when missing."""
    out = []
    for line in text.splitlines():
        m = re.match(r"^\s*(\d+)\.\s+(.*)$", line)
        if not m:
            continue
        rest = m.group(2).strip()
        url = ""
        parts = rest.rsplit(None, 1)
        if len(parts) == 2 and re.match(r"^https?://", parts[1]):
            rest, url = parts[0].strip(), parts[1]
        elif re.match(r"^https?://", rest):
            rest, url = "", rest
        out.append({"n": int(m.group(1)), "text": rest, "url": url})
    return out


def load_article(slug, text):
    meta, body = parse_front_matter(text)
    body, sources = _split_h2(body, "Sources")
    main, faq = _split_h2(body, "FAQ")
    return {"slug": slug, "meta": meta, "main": main.strip(), "faq": parse_faq(faq), "sources": parse_sources(sources)}


def slugify(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def inline(text):
    """Escape, then render links, **bold**, *italic*, and [n] citations."""
    text = html.escape(text, quote=True)
    saved = []

    def stash(m):
        label, url = m.group(1), m.group(2)
        rel = ' rel="noopener"' if url.startswith("https://") else ""
        saved.append(f'<a href="{url}"{rel}>{label}</a>')
        return f"\x00{len(saved) - 1}\x00"

    text = LINK.sub(stash, text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<em>\1</em>", text)
    text = CITE.sub(lambda m: f'<sup class="cite"><a href="#source-{m.group(1)}">[{m.group(1)}]</a></sup>', text)
    return re.sub(r"\x00(\d+)\x00", lambda m: saved[int(m.group(1))], text)


def render_markdown(md):
    """Markdown subset to HTML: ## / ### headings, paragraphs, lists, > quotes."""
    out, para, items, kind = [], [], [], None

    def flush():
        nonlocal para, items, kind
        if para:
            out.append(f"<p>{inline(' '.join(para))}</p>")
        if items:
            out.append(f"<{kind}>\n" + "\n".join(f"<li>{inline(i)}</li>" for i in items) + f"\n</{kind}>")
        para, items, kind = [], [], None

    for raw in md.splitlines():
        line = raw.strip()
        if not line:
            flush()
            continue
        h = re.match(r"^(#{2,3}) (.+)$", line)
        ul = re.match(r"^[-*] (.+)$", line)
        ol = re.match(r"^\d+\. (.+)$", line)
        if h:
            flush()
            level, title = len(h.group(1)), h.group(2).strip()
            out.append(f'<h{level} id="{slugify(plain_text(title))}">{inline(title)}</h{level}>')
        elif line.startswith("> "):
            flush()
            out.append(f"<blockquote><p>{inline(line[2:])}</p></blockquote>")
        elif ul or ol:
            if para:
                flush()
            want = "ul" if ul else "ol"
            if kind and kind != want:
                flush()
            kind = want
            items.append((ul or ol).group(1))
        elif items:
            items[-1] += " " + line  # wrapped list item
        else:
            para.append(line)
    flush()
    return "\n".join(out)


def plain_text(md):
    """Markdown to plain text (for meta tags, JSON-LD, and word counts)."""
    text = re.sub(r"^#{1,6}\s+", "", md, flags=re.M)
    text = re.sub(r"^\s*(?:[-*]|\d+\.|>)\s+", "", text, flags=re.M)
    text = LINK.sub(r"\1", text)
    text = re.sub(r"\s*\[\d+\](?!\()", "", text)
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"\*(.+?)\*", r"\1", text)
    return " ".join(text.split())


def word_count(md):
    return len(plain_text(md).split())


def validate(art, pillars, poses, min_words=None):
    """Problems with one article, as human-readable strings. [] means it's good.

    pillars: {key: {"slug": ...}}; poses: set of allowed pose names.
    min_words=0 skips the length check (tests); None uses the cluster/pillar range.
    """
    slug, meta, errs = art["slug"], art["meta"], []
    say = lambda msg: errs.append(f"{slug}: {msg}")  # noqa: E731
    if not SLUG.match(slug):
        say("slug (file name) must be lowercase-words-with-dashes")
    for key in REQUIRED:
        if not meta.get(key):
            say(f"missing front matter field '{key}'")
    if meta.get("pillar") and meta["pillar"] not in pillars:
        say(f"unknown pillar '{meta['pillar']}' (use one of {', '.join(sorted(pillars))})")
    if meta.get("pose") and meta["pose"] not in poses:
        say(f"unknown pose '{meta['pose']}' (use one of {', '.join(sorted(poses))})")
    if len(meta.get("description", "")) > MAX_DESCRIPTION:
        say(f"description is over {MAX_DESCRIPTION} characters")
    for key in ("published", "updated"):
        if meta.get(key) and not DATE.match(meta[key]):
            say(f"{key} must be YYYY-MM-DD")
    if meta.get("status", "published") not in STATUSES:
        say("status must be 'published' or 'draft'")

    for q, a in art["faq"]:
        if not q or not a:
            say("every FAQ needs a ### question and an answer")
        elif len(q) > MAX_FAQ_QUESTION:
            say(f"FAQ question over {MAX_FAQ_QUESTION} characters: {q[:40]}…")

    cited = {int(n) for n in CITE.findall(art["main"] + "\n" + "\n".join(a for _, a in art["faq"]))}
    numbers = [s["n"] for s in art["sources"]]
    if numbers != list(range(1, len(numbers) + 1)):
        say("sources must be numbered 1, 2, 3… in order")
    for n in sorted(cited - set(numbers)):
        say(f"citation [{n}] has no matching source")
    for s in art["sources"]:
        if s["n"] not in cited:
            say(f"source {s['n']} is never cited")
        if not s["url"]:
            say(f"source {s['n']} needs a URL at the end of the line")
        elif not s["url"].startswith("https://"):
            say(f"source {s['n']} URL must use https")

    if min_words != 0:
        is_pillar = any(p["slug"] == slug for p in pillars.values())
        low, high = WORDS["pillar" if is_pillar else "cluster"]
        n = word_count(art["main"])
        if not low <= n <= high:
            say(f"body is {n} words; aim for {low}–{high}")
    return errs
