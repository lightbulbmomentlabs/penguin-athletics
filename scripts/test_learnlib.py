#!/usr/bin/env python3
"""Tests for learnlib. Run: python3 -m unittest scripts/test_learnlib.py"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import learnlib as L  # noqa: E402

PILLARS = {"heart": {"slug": "walking-heart-health"}, "basics": {"slug": "walking-basics"}}
POSES = {"waddler-hyped"}

META = """---
title: Does walking lower blood pressure?
pillar: heart
description: Yes, by a few points.
answer: Yes. Brisk walking lowers it.
published: 2026-11-07
keywords: walking blood pressure, bp
pose: waddler-hyped
gary: Your arteries called.
signoff: Go walk.
status: published
---
"""


def article(body, slug="does-walking-lower-blood-pressure", meta=META):
    return L.load_article(slug, meta + body)


class FrontMatter(unittest.TestCase):
    def test_parses_flat_keys_and_body(self):
        meta, body = L.parse_front_matter("---\ntitle: A: B\nempty:\n---\nHello\n")
        self.assertEqual(meta, {"title": "A: B", "empty": ""})
        self.assertEqual(body, "Hello\n")

    def test_requires_fences(self):
        with self.assertRaises(ValueError):
            L.parse_front_matter("title: x\n")
        with self.assertRaises(ValueError):
            L.parse_front_matter("---\ntitle: x\n")

    def test_rejects_line_without_colon(self):
        with self.assertRaises(ValueError):
            L.parse_front_matter("---\nnope\n---\n")


class Sections(unittest.TestCase):
    BODY = "Intro.\n\n## Why\nText [1].\n\n## FAQ\n### Is it safe?\nUsually [2].\n\n### How long?\n30 minutes.\nMore.\n\n## Sources\n1. Smith et al. Walk. *J*. 2020. https://example.org/a\n2. CDC. Activity. 2022. https://cdc.gov/x\n"

    def test_split(self):
        a = article(self.BODY)
        self.assertIn("## Why", a["main"])
        self.assertNotIn("FAQ", a["main"])
        self.assertEqual([q for q, _ in a["faq"]], ["Is it safe?", "How long?"])
        self.assertEqual(a["faq"][1][1], "30 minutes.\nMore.")
        self.assertEqual([s["n"] for s in a["sources"]], [1, 2])
        self.assertEqual(a["sources"][0]["url"], "https://example.org/a")
        self.assertEqual(a["sources"][0]["text"], "Smith et al. Walk. *J*. 2020.")

    def test_no_faq_or_sources(self):
        a = article("Just text.\n")
        self.assertEqual(a["faq"], [])
        self.assertEqual(a["sources"], [])


class Markdown(unittest.TestCase):
    def test_blocks(self):
        html = L.render_markdown("## Why walk?\nPara one\ncontinues.\n\n- a\n- b\n\n1. x\n2. y\n\n> quote\n\n### Small")
        self.assertIn('<h2 id="why-walk">Why walk?</h2>', html)
        self.assertIn("<p>Para one continues.</p>", html)
        self.assertIn("<ul>\n<li>a</li>\n<li>b</li>\n</ul>", html)
        self.assertIn("<ol>\n<li>x</li>\n<li>y</li>\n</ol>", html)
        self.assertIn("<blockquote><p>quote</p></blockquote>", html)
        self.assertIn('<h3 id="small">Small</h3>', html)

    def test_inline(self):
        html = L.inline("**bold** and *it* [CDC](https://cdc.gov/a_b*c) [home](/learn/) x [1][2]")
        self.assertIn("<strong>bold</strong>", html)
        self.assertIn("<em>it</em>", html)
        self.assertIn('<a href="https://cdc.gov/a_b*c" rel="noopener">CDC</a>', html)
        self.assertIn('<a href="/learn/">home</a>', html)
        self.assertIn('<sup class="cite"><a href="#source-1">[1]</a></sup><sup class="cite"><a href="#source-2">[2]</a></sup>', html)

    def test_escapes_html(self):
        html = L.render_markdown('<script>alert("x")</script> & 5 < 6')
        self.assertNotIn("<script>", html)
        self.assertIn("&lt;script&gt;", html)
        self.assertIn("&amp;", html)

    def test_plain_text(self):
        self.assertEqual(L.plain_text("**Yes** [1], see [CDC](https://cdc.gov) and *this*."), "Yes, see CDC and this.")

    def test_slugify(self):
        self.assertEqual(L.slugify("How much walking? (A lot!)"), "how-much-walking-a-lot")

    def test_word_count(self):
        self.assertEqual(L.word_count("## Hi there\nOne two [1] **three**."), 5)


class Validate(unittest.TestCase):
    GOOD = "Text [1].\n\n## FAQ\n### Q?\nA [2].\n\n## Sources\n1. A. T. 2020. https://a.org/1\n2. B. T. 2021. https://b.org/2\n"

    def errors(self, body=GOOD, slug="does-walking-lower-blood-pressure", meta=META):
        return L.validate(article(body, slug, meta), PILLARS, POSES, min_words=0)

    def test_good(self):
        self.assertEqual(self.errors(), [])

    def test_meta_problems(self):
        bad = META.replace("pillar: heart", "pillar: feet").replace("pose: waddler-hyped", "pose: nope")
        bad = bad.replace("description: Yes, by a few points.", "description: " + "x" * 161)
        bad = bad.replace("published: 2026-11-07", "published: Nov 7").replace("gary: Your arteries called.\n", "")
        errs = " | ".join(self.errors(meta=bad))
        for word in ("pillar", "pose", "description", "published", "gary"):
            self.assertIn(word, errs)

    def test_bad_slug(self):
        self.assertTrue(any("slug" in e for e in self.errors(slug="Bad_Slug")))

    def test_citations(self):
        errs = " | ".join(self.errors("Text [3].\n\n## Sources\n1. A. 2020. http://a.org\n2. B. 2021.\n"))
        self.assertIn("[3]", errs)
        self.assertIn("source 1 is never cited", errs)
        self.assertIn("https", errs)
        self.assertIn("source 2", errs)

    def test_sources_numbered_in_order(self):
        errs = self.errors("A [1] [3].\n\n## Sources\n1. A. https://a.org\n3. C. https://c.org\n")
        self.assertTrue(any("numbered" in e for e in errs))

    def test_word_range(self):
        a = article(self.GOOD)
        self.assertTrue(any("words" in e for e in L.validate(a, PILLARS, POSES)))

    def test_long_faq_question(self):
        errs = self.errors("x\n\n## FAQ\n### " + "w" * 90 + "?\nA.\n")
        self.assertTrue(any("FAQ" in e for e in errs))


if __name__ == "__main__":
    unittest.main()
