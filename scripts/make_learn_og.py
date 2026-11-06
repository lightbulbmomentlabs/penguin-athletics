#!/usr/bin/env python3
"""Renders the Learn share images (hub + one per pillar) into public/assets/og/.

Fills scripts/og/og-learn.html for each, then calls make-og-image.sh (needs Google Chrome).
Rerun after changing content/pillars.json or the template.
"""
import json
import subprocess
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = (ROOT / "scripts/og/og-learn.html").read_text(encoding="utf-8")
SPEECH = {
    "heart": "Cardio, but make it a stroll.",
    "longevity": "Immortality, one lap at a time.",
    "weight": "Steps over crash diets. Always.",
    "mind": "Walk it off. Literally.",
    "basics": "Step one: stand up. Proud of you.",
}


def render(name, kicker, title, sub, speech, pose):
    html = (TEMPLATE.replace("{{KICKER}}", escape(kicker)).replace("{{TITLE}}", escape(title))
            .replace("{{SUB}}", escape(sub)).replace("{{SPEECH}}", escape(speech)).replace("{{POSE}}", pose))
    tmp = ROOT / "scripts/og" / f".tmp-{name}.html"  # beside the template so relative asset paths work
    tmp.write_text(html, encoding="utf-8")
    try:
        out = ROOT / "public/assets/og" / f"{name}.jpg"
        out.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run([str(ROOT / "scripts/make-og-image.sh"), str(tmp.relative_to(ROOT)), str(out.relative_to(ROOT))],
                       check=True)
    finally:
        tmp.unlink()


render("learn", "Learn", "Walking, explained.", "Heart, longevity, weight, and your head. Every claim cited.",
       "Reading counts as zero steps.", "waddler-celebrating")
for p in json.loads((ROOT / "content/pillars.json").read_text(encoding="utf-8")):
    render(f"learn-{p['key']}", "Learn", p["title"], p["blurb"], SPEECH[p["key"]], p["pose"])
