#!/usr/bin/env python3
"""Makes the served wordmark (public/assets/logo/penguin-wordmark.svg) from the traced original.

The original (penguin-script-white.svg, from VTracer) is ~22 KB, which pushed the home page past its
600 KB first-load budget. This keeps the same shapes and 1608x712 coordinate box, but rounds points to
whole units, bakes in each path's translate, and writes curves as relative offsets: ~6.5 KB.
Also writes a navy copy for light backgrounds (the join page and share images). Rerun after replacing the original. Expects VTracer-style paths (M/C/Z with a translate on each).
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "public/assets/logo/penguin-script-white.svg"
OUT = ROOT / "public/assets/logo/penguin-wordmark.svg"
NAVY = ROOT / "public/assets/logo/penguin-wordmark-navy.svg"  # for light backgrounds: join page, share images

src = SRC.read_text(encoding="utf-8")
box = re.search(r'viewBox="([^"]+)"', src).group(1)
paths = re.findall(r'<path d="([^"]*)"[^>]*transform="translate\(([-\d.]+),([-\d.]+)\)"', src)
assert paths and len(paths) == src.count("<path"), "every path needs a translate"

shapes = []
for d, tx, ty in paths:
    tx, ty = float(tx), float(ty)
    out, cur, start = [], (0, 0), (0, 0)
    for cmd, args in re.findall(r"([A-Za-z])([^A-Za-z]*)", d):
        nums = [float(n) for n in re.findall(r"-?\d+(?:\.\d+)?", args)]
        pts = [(round(nums[i] + tx), round(nums[i + 1] + ty)) for i in range(0, len(nums), 2)]
        if cmd == "M":
            out.append(f"M{pts[0][0]} {pts[0][1]}")
            cur = start = pts[0]
        elif cmd == "Z":
            out.append("z")
            cur = start
        elif cmd == "C":
            seg = []
            for i in range(0, len(pts), 3):
                group = pts[i:i + 3]
                seg += [f"{x - cur[0]} {y - cur[1]}" for x, y in group]
                cur = group[-1]
            out.append("c" + " ".join(seg))
        else:
            raise SystemExit(f"unsupported path command {cmd!r}")
    shapes.append("".join(out).replace(" -", "-"))

svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{box}" fill="#fff">'
       + "".join(f'<path d="{s}"/>' for s in shapes) + "</svg>\n")
OUT.write_text(svg, encoding="utf-8")
NAVY.write_text(svg.replace('fill="#fff"', 'fill="#1c2440"', 1), encoding="utf-8")
print(f"wrote {OUT.relative_to(ROOT)}: {len(src)} -> {len(svg)} bytes, and {NAVY.relative_to(ROOT)}")
