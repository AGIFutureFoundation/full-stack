#!/usr/bin/env python3
"""Draws the repo's figures from recipe.toml and data/records.toml.

    python3 tools/render.py          # writes assets/*.svg and docs/spec.json
    python3 tools/render.py --check  # exit 1 if any output is out of date

Change a number in recipe.toml, run this, and the drawings follow.
"""

from __future__ import annotations

import base64
import functools
import html
import json
import math
import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BRAND = ROOT / "assets/brand"
sys.path.insert(0, str(ROOT))
from calc import compute, load_spec  # noqa: E402

# Pancake brand palette: Figma "Pancake Design" variables (core tokens, 2316:5111),
# plus the page cream, tinted pill and blue ramp of pancake.ai (landing-v3/foundation.css).
# One source for the page CSS ({{TOKENS_CSS}}) and the drawings (C below).
TOKENS = {
    "ink": {0: "#FFFFFF", 10: "#FFFBF6", 20: "#FFF7EC", 30: "#F7EDE5", 40: "#EFE4DC", 50: "#DDCFCD",
            60: "#BBA8AE", 70: "#9A818F", 80: "#85687C", 90: "#6C4B65", 100: "#2C002A"},
    "pink": {10: "#FFD9DA", 20: "#FFBBC7", 30: "#FF7AA0", 40: "#E33A6A"},
    "purple": {10: "#EFDDF1", 20: "#DEC3F5", 30: "#BA8BFF", 40: "#8D43FD"},
    "yellow": {10: "#FFE9D1", 20: "#FFDBB5", 30: "#FFBD7A", 40: "#F38F43"},
    "orange": {10: "#FFDDBE", 20: "#FFA45F", 30: "#D43900", 40: "#B20000"},
    "red": {10: "#FFD1C9", 20: "#FF8080", 30: "#E5002E", 40: "#AD001A"},
    "green": {10: "#CEEAD5", 20: "#68CEA7", 30: "#037D48", 40: "#00532F"},
    "blue": {10: "#D9E9FF", 20: "#B0CBFF", 30: "#6A8FFF", 40: "#4660E7"},
    "cream": "#FBF6F1",   # page background
    "tinted": "#F8E5D4",  # tinted pill
}
INK_TR = (5, 10, 20, 40, 50, 60, 70, 80)  # ink-100 at these opacities


def tokens_css() -> str:
    lines = []
    for name, val in TOKENS.items():
        if isinstance(val, dict):
            lines += [f"--{name}-{k}: {v};" for k, v in val.items()]
        else:
            lines.append(f"--{name}: {val};")
    lines += [f"--ink-tr-{p}: rgb(44 0 42 / {p}%);" for p in INK_TR]
    return ":root {\n  " + "\n  ".join(lines) + "\n}"


T = TOKENS
C = {
    "bg": T["cream"], "paper": T["ink"][10], "ink": T["ink"][100], "sub": T["ink"][80], "muted": T["ink"][70],
    "line": T["ink"][50], "faint": T["ink"][40], "pink": T["pink"][30], "pink2": T["pink"][20], "pink4": T["pink"][40],
    "purple": T["purple"][30], "purple1": T["purple"][10], "purple2": T["purple"][20], "purple4": T["purple"][40],
    "yellow": T["yellow"][30], "yellow2": T["yellow"][20], "yellow4": T["yellow"][40], "green": T["green"][20],
    "green3": T["green"][30], "blue": T["blue"][40], "tinted": T["tinted"],
}
SANS = "Geist, 'Helvetica Neue', Helvetica, Arial, sans-serif"
MONO = "'Geist Mono', ui-monospace, 'SF Mono', Menlo, Consolas, monospace"
# Headlines: Mona Sans condensed 600, like the page. GitHub shows README images through <img>, which
# can't fetch web fonts, so the standalone SVGs carry a Latin subset of it (with_font). Built once with
# fonttools, not a dependency here: the Google Fonts "Mona Sans" wdth 75 wght 600 latin file (the build
# the page loads), then
#   pyftsubset latin.woff2 --unicodes='U+0020-007E,U+00A0,U+00B0,U+00B7,U+00BC,U+00D7,U+2013,U+2014,U+2018,
#     U+2019,U+201C,U+201D,U+2026' --layout-features='kern,liga,ccmp,locl' --drop-tables+=STAT,gasp
#     --flavor=woff2 --name-IDs='*' --no-hinting
# then renamed "Tower Display" in its name table: a subset is a Modified Version under the OFL, and
# "Mona" is a Reserved Font Name. The copyright notice and licence (fonts/OFL.txt) stay with it.
DISPLAY = "'Tower Display', 'Mona Sans', 'Arial Narrow', Arial, sans-serif"
DISPLAY_FONT = BRAND / "fonts/TowerDisplay-Condensed-SemiBold-latin.woff2"
DISPLAY_TRACK = -0.03  # em
# its advance widths in 1/1000 em (hmtx), to size headlines without the font at hand
DISPLAY_ADV = dict(zip(
    " !\"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~°·¼×–—‘’“”…",
    (188, 200, 331, 501, 432, 671, 571, 158, 263, 263, 259, 480, 176, 314, 165, 291, 455, 287, 406, 425, 451, 428, 447,
     420, 437, 447, 165, 176, 480, 480, 480, 393, 667, 449, 426, 448, 459, 351, 340, 468, 465, 210, 243, 444, 317, 590,
     469, 463, 429, 483, 447, 417, 358, 464, 436, 683, 444, 438, 389, 275, 295, 275, 480, 373, 264, 416, 416, 385, 416,
     389, 244, 413, 423, 196, 196, 386, 196, 661, 423, 404, 416, 416, 266, 364, 234, 423, 367, 569, 381, 360, 305, 298,
     208, 298, 480, 357, 181, 521, 480, 422, 598, 176, 176, 374, 374, 557), strict=True))
FALLBACK_EM = 0.6, 0.72  # Arial Bold per character, roughly (lower case, capitals): a headline without its face
TIER = {"base": ("pink", "pink2"), "body": ("purple", "purple2"), "top": ("yellow", "yellow2")}


def logo_path() -> str:
    svg = (ROOT / "assets/brand/pancake-logo.svg").read_text()
    return re.search(r'<path d="([^"]+)"', svg).group(1)


def mascot_inner() -> str:
    svg = (ROOT / "assets/brand/pancake-monster.svg").read_text()
    return svg[svg.index(">") + 1: svg.rindex("</svg>")].strip()


def logo(x: float, y: float, width: float, fill: str = C["ink"]) -> str:
    s = width / 422
    return f'<path transform="translate({x} {y}) scale({s:.4f})" d="{logo_path()}" fill="{fill}"/>'


def mascot(x: float, y: float, width: float, cls: str = "") -> str:
    s = width / 348
    inner = f'<g transform="translate({x} {y}) scale({s:.4f}) translate(-340 -362)">{mascot_inner()}</g>'
    return f'<g class="{cls}">{inner}</g>' if cls else inner


def text(x, y, s, size, fill=C["ink"], weight=400, family=SANS, anchor="start", extra=""):
    s = s.replace("&", "&amp;").replace("<", "&lt;")
    return (f'<text x="{x}" y="{y}" font-family="{family}" font-size="{size}" font-weight="{weight}" '
            f'fill="{fill}" text-anchor="{anchor}"{extra}>{s}</text>')


def display_width(s: str, size: float) -> float:
    return size * (sum(DISPLAY_ADV[ch] for ch in s) / 1000 + DISPLAY_TRACK * len(s))


def display(x, y, s, size, box, fill=C["ink"], anchor="start"):
    """A headline in Mona Sans condensed 600. `box` is the width it may take: where Arial Bold would not fit
    in it, textLength pins the line to its Mona Sans width, so a missing font squeezes instead of spilling."""
    w = display_width(s, size)
    assert w <= box, f"{s!r} at {size}px is {w:.0f}px, wider than its {box:.0f}px box"
    extra = f' font-stretch="condensed" letter-spacing="{DISPLAY_TRACK}em"'
    if size * sum(FALLBACK_EM[ch.isupper()] for ch in s) > box:
        extra += f' textLength="{w:.1f}" lengthAdjust="spacingAndGlyphs"'
    return text(x, y, s, size, fill, 600, DISPLAY, anchor, extra)


def sans_width(s: str, size: float) -> float:
    """Width of a Geist line with room to spare: README images get Helvetica or Arial instead (+5 %), even Verdana fits."""
    em = sum(.3 if ch in " .,:;'·ijlI|!ftr()" else .9 if ch in "mwMW" else .74 if ch.isupper() else .57 for ch in s)
    return em * size


def eyebrow(x, y, s, size=13, fill=C["sub"]):
    return text(x, y, s.upper(), size, fill, 500, SANS, extra=' letter-spacing="0.1em"')


def chip(x, y, label, size=14, dot=None) -> tuple[str, float]:
    """The page's chip: r8, ink at 5 %, Geist 500. Returns the markup and its width."""
    pad, h = 12, size + 18
    lead = 16 if dot else 0
    w = 2 * pad + lead + sans_width(label, size)
    out = [f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h}" rx="8" fill="{C["ink"]}" fill-opacity="0.05"/>']
    if dot:
        out.append(f'<circle cx="{x + pad + 4:.1f}" cy="{y + h / 2:.1f}" r="4" fill="{dot}"/>')
    out.append(text(round(x + pad + lead + (w - 2 * pad - lead) / 2, 1), round(y + h / 2 + size * .36, 1),
                    label, size, C["ink"], 500, SANS, "middle"))
    return "".join(out), w


@functools.cache
def font_face() -> str:
    b64 = base64.b64encode(DISPLAY_FONT.read_bytes()).decode()
    return (f"@font-face {{ font-family: 'Tower Display'; font-weight: 600; font-stretch: condensed; "
            f"src: url(data:font/woff2;base64,{b64}) format('woff2'); }}")


def with_font(svg: str) -> str:
    """The standalone file: the drawing plus the display face it can't fetch. The page inlines the bare drawing."""
    head, rest = svg.split("</title>\n", 1)
    return f"{head}</title>\n<style>\n{font_face()}\n</style>\n{rest}"


def svg_open(w, h, label):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
            f'role="img" aria-label="{label}">\n<title>{label}</title>\n')


def stack(x_center, y_bottom, width, n, layer_px, color, rule, rx=3):
    """A tier of n pancakes, one hairline per pancake."""
    h = n * layer_px
    top = y_bottom - h
    out = [f'<rect x="{x_center - width / 2:.1f}" y="{top:.1f}" width="{width:.1f}" height="{h:.1f}" rx="{rx}" fill="{C[color]}"/>']
    for i in range(1, n):
        yy = y_bottom - i * layer_px
        out.append(f'<line x1="{x_center - width / 2 + 1:.1f}" x2="{x_center + width / 2 - 1:.1f}" y1="{yy:.2f}" y2="{yy:.2f}" '
                   f'stroke="{C[rule]}" stroke-width="{min(0.8, layer_px * 0.35):.2f}"/>')
    return "\n".join(out), top


# ---------------------------------------------------------------- hero
def dome(scale: float, dx: float, dy: float) -> str:
    """pancake.ai's hero rainbow (assets/brand/rainbow-hero.svg): five rings and the cream core over them."""
    rings = re.findall(r'<path d="([^"]+)" fill="(#[0-9A-Fa-f]{6})"/>', (BRAND / "rainbow-hero.svg").read_text())
    assert len(rings) == 6, "rainbow-hero.svg: expected 5 rings and the core"
    body = "\n".join(f'<path d="{d}" fill="{fill}"/>' for d, fill in rings)
    return f'<g transform="translate({dx:.1f} {dy:.1f}) scale({scale:.4f})" aria-hidden="true">\n{body}\n</g>'


def hero(spec, plan) -> str:
    W, H = 1280, 640
    t, meta, ev = spec["target"], spec["meta"], spec["event"]
    s = 10  # px per inch
    base_y, cx = 600, 910
    rx = cx - 78  # the ruler
    chips_y, h1_y, h1_lh, h1_size, facts_y = 304, 430, 72, 70, 552
    parts = [svg_open(W, H, "Pancake Tower: we promised a world record. Here is the recipe.")]
    parts.append(f"""<style>
@media (prefers-reduced-motion: no-preference) {{
  .tier {{ transform-box: fill-box; transform-origin: 50% 100%; animation: grow .8s cubic-bezier(.2,.8,.2,1) both; }}
  .t2 {{ animation-delay: .7s; animation-duration: 1.6s; }}
  .t3 {{ animation-delay: 2.2s; }}
  .later {{ animation: fade .6s ease both; animation-delay: 2.9s; }}
  .hop {{ animation: hop .7s cubic-bezier(.3,1.6,.5,1) both; animation-delay: 3.2s; transform-box: fill-box; transform-origin: 50% 100%; }}
  @keyframes grow {{ from {{ transform: scaleY(0); }} }}
  @keyframes fade {{ from {{ opacity: 0; }} }}
  @keyframes hop {{ from {{ transform: translateY(40px) scale(.6); opacity: 0; }} }}
}}
</style>
<defs><clipPath id="card"><rect width="{W}" height="{H}" rx="28"/></clipPath></defs>
<g clip-path="url(#card)">
<rect width="{W}" height="{H}" fill="{C['bg']}"/>""")
    parts.append(dome(0.89, -20, -195))
    # left column: logo, chips, the H1 (plum, like production), the numbers
    parts.append(logo(72, 52, 140))
    x = 72
    for label, dot in [(f"v{meta['version']} · {meta['status']}", C["pink4"]), (f"{ev['date']} · {ev['place']}", None)]:
        markup, w = chip(x, chips_y, label, dot=dot)
        parts.append(markup)
        x += w + 8
    box = rx - 36 - 72  # up to the ruler's numbers
    for i, line in enumerate(["We promised a world record.", "Here’s the recipe."]):
        parts.append(display(70, h1_y + i * h1_lh, line, h1_size, box))
    x = 72
    for label in [f"{t['record_height_in']} in to beat", f"{t['build_to_in']:g} in stop line",
                  f"~{plan['pancakes_to_stop_line']} pancakes", f"{spec['rules']['hold_seconds']} s hold"]:
        markup, w = chip(x, facts_y, label)
        parts.append(markup)
        x += w + 8
    assert x - 8 <= rx - 36, "hero chips run into the ruler"
    # ruler
    parts.append(f'<g class="later"><line x1="{rx}" x2="{rx}" y1="{base_y}" y2="{base_y - 48 * s}" stroke="{C["sub"]}" stroke-width="1.5"/>')
    for i in range(0, 49, 6):
        yy = base_y - i * s
        parts.append(f'<line x1="{rx - 8}" x2="{rx}" y1="{yy}" y2="{yy}" stroke="{C["sub"]}" stroke-width="1.5"/>')
        parts.append(text(rx - 14, yy + 5, f"{i} in" if i == 48 else f"{i}", 13, C["sub"], 500, MONO, "end"))
    parts.append("</g>")
    # tower to scale
    layer = plan["thickness_in"] * (1 - t["settle_ratio"]) * s
    y = base_y
    for i, z in enumerate(plan["sizes"]):
        n = z["in_tower"]
        if z["name"] == "top":  # stack up to the stop line, not past it
            n = min(n, int((t["build_to_in"] * s - (base_y - y)) / layer))
        body, y_top = stack(cx, y, z["ring_in"] * s, n, layer, TIER[z["name"]][0], TIER[z["name"]][1], rx=4)
        parts.append(f'<g class="tier t{i + 1}">{body}</g>')
        y = y_top
    parts.append(f'<rect x="{cx - 70}" y="{base_y}" width="240" height="7" rx="3.5" fill="{C["ink"]}"/>')
    # record + stop lines
    for val, col, lab, dy in [(t["record_height_in"], C["pink4"], "record", 14),
                              (t["build_to_in"], C["ink"], "stop line", -2)]:
        yy = base_y - val * s
        parts.append(f'<g class="later"><line x1="{rx}" x2="{cx + 66}" y1="{yy:.1f}" y2="{yy:.1f}" stroke="{col}" stroke-width="2" stroke-dasharray="6 5"/>')
        parts.append(text(cx + 74, yy + dy, f"{val:g} in", 15, col, 700, MONO) + text(cx + 74, yy + dy + 18, lab, 13, col, 500, MONO) + "</g>")
    parts.append(mascot(cx + 62, base_y - 96, 96, "hop"))
    parts.append("</g>\n</svg>\n")
    return "\n".join(parts)


# ---------------------------------------------------------------- tower drawing
def tower(spec, plan) -> str:
    W, H = 1280, 1000
    t, meta = spec["target"], spec["meta"]
    s = 17
    base_y, cx = 884, 432
    layer = plan["thickness_in"] * (1 - t["settle_ratio"]) * s
    parts = [svg_open(W, H, "Pancake Tower elevation and plan, drawn to scale from recipe.toml")]
    parts.append(f'<rect width="{W}" height="{H}" rx="28" fill="{C["bg"]}"/>')
    # drawing grid, 3 in squares
    g = []
    for gx in range(72, 760, 51):
        g.append(f'<line x1="{gx}" x2="{gx}" y1="72" y2="{base_y}" />')
    for gy in range(base_y, 70, -51):
        g.append(f'<line x1="72" x2="760" y1="{gy}" y2="{gy}" />')
    parts.append(f'<g stroke="{C["faint"]}" stroke-width="1">{"".join(g)}</g>')
    parts.append(eyebrow(72, 56, "Elevation", 14))
    parts.append(text(180, 56, "to scale · grid = 3 in", 14, C["sub"], 400, MONO))

    # tiers
    y = base_y
    tiers = []
    for z in plan["sizes"]:
        n = z["in_tower"]
        if z["name"] == "top":
            n = min(n, round((t["build_to_in"] * s - (base_y - y)) / layer))
        body, y_top = stack(cx, y, z["ring_in"] * s, n, layer, TIER[z["name"]][0], TIER[z["name"]][1])
        parts.append(body)
        tiers.append((z, n, y, y_top))
        y = y_top

    # laser A, plumb
    parts.append(f'<line x1="{cx}" x2="{cx}" y1="82" y2="{base_y + 6}" stroke="{C["purple4"]}" stroke-width="1.5" stroke-dasharray="2 5"/>')
    parts.append(text(cx + 8, 92, "LASER A · plumb", 13, C["purple4"], 600, MONO))

    # left callouts
    for z, n, yb, yt in tiers:
        ym = (yb + yt) / 2
        xl = cx - z["ring_in"] * s / 2
        parts.append(f'<line x1="{xl - 8}" x2="292" y1="{ym:.1f}" y2="{ym:.1f}" stroke="{C["ink"]}" stroke-width="1"/>')
        parts.append(f'<circle cx="{xl - 8}" cy="{ym:.1f}" r="2.5" fill="{C["ink"]}"/>')
        parts.append(text(286, ym - 6, z["name"].upper(), 15, C["ink"], 700, MONO, "end", ' letter-spacing="1.2"'))
        cnt = f"{n} of {z['in_tower']}" if n != z["in_tower"] else f"{n}"
        parts.append(text(286, ym + 15, f"Ø {z['ring_in']} in · {cnt}", 14, C["sub"], 400, MONO, "end"))

    # height dimensions
    def vdim(x, y1, y2, label, bold=False):
        o = [f'<g stroke="{C["ink"]}" stroke-width="1">',
             f'<line x1="{x}" x2="{x}" y1="{y1 + 1:.1f}" y2="{y2 - 1:.1f}"/>',
             f'<line x1="{x - 5}" x2="{x + 5}" y1="{y1:.1f}" y2="{y1:.1f}"/><line x1="{x - 5}" x2="{x + 5}" y1="{y2:.1f}" y2="{y2:.1f}"/>',
             "</g>"]
        o.append(text(x + 9, (y1 + y2) / 2 + 5, label, 14 if not bold else 15, C["ink"], 700 if bold else 500, MONO))
        return "\n".join(o)

    for z, n, yb, yt in tiers:
        parts.append(vdim(cx + 92, yt, yb, f"{(yb - yt) / s:.1f}"))
    parts.append(vdim(cx + 150, tiers[-1][3], base_y, f"{t['build_to_in']:g} in", bold=True))

    # height gauge
    gx = 662
    parts.append(f'<rect x="{gx - 4}" y="{base_y - 48 * s}" width="8" height="{48 * s}" rx="2" fill="{C["paper"]}" stroke="{C["ink"]}"/>')
    parts.append(f'<rect x="{gx - 28}" y="{base_y - 6}" width="56" height="6" rx="2" fill="{C["ink"]}"/>')
    for i in range(0, 49, 3):
        parts.append(f'<line x1="{gx - 4}" x2="{gx + 2 + (4 if i % 6 == 0 else 0)}" y1="{base_y - i * s}" y2="{base_y - i * s}" stroke="{C["ink"]}"/>')
    parts.append(text(gx, base_y - 48 * s - 14, "GAUGE", 13, C["sub"], 600, MONO, "middle", ' letter-spacing="1.2"'))
    for val, col, lab in [(t["record_height_in"], C["pink4"], "RECORD"), (t["slow_down_at_in"], C["yellow4"], "SLOW"),
                          (t["build_to_in"], C["ink"], "STOP")]:
        yy = base_y - val * s
        parts.append(f'<line x1="{cx - 60}" x2="{gx - 4}" y1="{yy:.1f}" y2="{yy:.1f}" stroke="{col}" stroke-width="1.2" stroke-dasharray="5 4"/>')
        off = {"RECORD": 14, "SLOW": 2, "STOP": -10}[lab]
        parts.append(text(gx + 14, yy + 5 + off, f"{lab} {val:g}", 13, col, 700, MONO))

    # table
    parts.append(f'<rect x="250" y="{base_y}" width="450" height="14" rx="3" fill="{C["ink"]}"/>')
    parts.append(f'<rect x="270" y="{base_y + 14}" width="10" height="56" fill="{C["ink"]}"/><rect x="670" y="{base_y + 14}" width="10" height="56" fill="{C["ink"]}"/>')
    parts.append(text(475, base_y + 96, "Heavy table · level < 0.2° · printed Ø 9 in circle", 14, C["sub"], 400, MONO, "middle"))

    # plan view
    px0, py0, pw, ph = 812, 72, 396, 392
    pcx, pcy, ps = px0 + pw / 2, py0 + 196, 26
    parts.append(f'<rect x="{px0}" y="{py0}" width="{pw}" height="{ph}" rx="18" fill="{C["paper"]}" stroke="{C["line"]}"/>')
    parts.append(eyebrow(px0 + 22, py0 + 34, "Plan", 14))
    parts.append(text(px0 + 70, py0 + 34, "from above · to scale", 14, C["sub"], 400, MONO))
    for z in plan["sizes"]:
        r = z["ring_in"] * ps / 2
        parts.append(f'<circle cx="{pcx}" cy="{pcy}" r="{r}" fill="{C[TIER[z["name"]][0]]}" stroke="{C["paper"]}" stroke-width="2"/>')
    parts.append(f'<line x1="{pcx}" x2="{pcx}" y1="{py0 + 52}" y2="{py0 + ph - 18}" stroke="{C["purple4"]}" stroke-width="1.5" stroke-dasharray="2 5"/>')
    parts.append(f'<line x1="{px0 + 18}" x2="{px0 + pw - 18}" y1="{pcy}" y2="{pcy}" stroke="{C["purple4"]}" stroke-width="1.5" stroke-dasharray="2 5"/>')
    parts.append(text(pcx + 8, py0 + 64, "A", 13, C["purple4"], 700, MONO))
    parts.append(text(px0 + pw - 22, pcy - 8, "B", 13, C["purple4"], 700, MONO, "end"))
    # quarter-turn arrow
    r = 4.5 * ps + 18
    a0, a1 = math.radians(-22), math.radians(-62)
    x0, y0 = pcx + r * math.cos(a0), pcy + r * math.sin(a0)
    x1, y1 = pcx + r * math.cos(a1), pcy + r * math.sin(a1)
    parts.append(f'<path d="M{x0:.1f} {y0:.1f} A{r} {r} 0 0 0 {x1:.1f} {y1:.1f}" fill="none" stroke="{C["ink"]}" stroke-width="1.5"/>')
    parts.append(f'<path d="M{x1:.1f} {y1:.1f} l9 -3 l-3 9 z" fill="{C["ink"]}"/>')
    parts.append(text(px0 + pw - 20, py0 + 62, "¼ turn per pancake", 13, C["ink"], 500, MONO, "end"))
    lx = px0 + 22
    for z in plan["sizes"]:
        parts.append(f'<rect x="{lx}" y="{py0 + ph - 34}" width="14" height="14" rx="4" fill="{C[TIER[z["name"]][0]]}"/>')
        lab = f"Ø {z['ring_in']} {z['name']}"
        parts.append(text(lx + 20, py0 + ph - 22, lab, 13, C["ink"], 500, MONO))
        lx += 34 + len(lab) * 8

    # notes
    ny = 500
    parts.append(eyebrow(812, ny, "Notes", 14))
    notes = ["Nothing touches the tower but pancakes.", "Lower each one from an edge. Never slide.",
             "Spotters call drift every 10 pancakes.", f"Slow at {t['slow_down_at_in']:g} in. Stop at {t['build_to_in']:g} in.",
             f"Hold {spec['rules']['hold_seconds']} s, hands off. Then measure."]
    for i, n in enumerate(notes):
        yy = ny + 36 + i * 34
        parts.append(f'<circle cx="824" cy="{yy - 5}" r="11" fill="none" stroke="{C["ink"]}"/>')
        parts.append(text(824, yy, str(i + 1), 13, C["ink"], 700, MONO, "middle"))
        parts.append(text(846, yy, n, 16, C["ink"]))

    # title block
    tx, ty, tw, th = 812, 720, 396, 214
    parts.append(f'<rect x="{tx}" y="{ty}" width="{tw}" height="{th}" rx="18" fill="{C["paper"]}" stroke="{C["ink"]}" stroke-width="1.5"/>')
    parts.append(f'<line x1="{tx}" x2="{tx + tw}" y1="{ty + 84}" y2="{ty + 84}" stroke="{C["ink"]}"/>')
    parts.append(f'<line x1="{tx + tw / 2}" x2="{tx + tw / 2}" y1="{ty + 84}" y2="{ty + th}" stroke="{C["ink"]}"/>')
    parts.append(f'<line x1="{tx}" x2="{tx + tw}" y1="{ty + 150}" y2="{ty + 150}" stroke="{C["ink"]}"/>')
    parts.append(display(tx + 22, ty + 52, "PANCAKE TOWER", 34, tw - 22 - 86))
    parts.append(text(tx + 22, ty + 72, "Elevation & plan · units: inches", 14, C["sub"], 400, MONO))
    parts.append(mascot(tx + tw - 74, ty + 14, 56))
    cells = [("SPEC", f"v{meta['version']}"), ("STATUS", meta["status"].upper()),
             ("TOWER", f"{sum(n for _, n, _, _ in tiers)} pancakes"), ("BUILT BY", None)]
    for i, (k, v) in enumerate(cells):
        cx2 = tx + 22 + (i % 2) * tw / 2
        cy2 = ty + 108 + (i // 2) * 66
        parts.append(text(cx2, cy2, k, 12, C["sub"], 600, MONO, extra=' letter-spacing="1.2"'))
        if v:
            col = C["pink4"] if v == "UNTESTED" else C["ink"]
            parts.append(text(cx2, cy2 + 26, v, 18, col, 700, MONO))
        else:
            parts.append(logo(cx2, cy2 + 8, 80))
    parts.append("</svg>\n")
    return "\n".join(parts)


# ---------------------------------------------------------------- record history
def records(spec, plan) -> str:
    """The page's record chart: a card on cream, pink bars, our stop line dashed in purple."""
    W, H = 1280, 660
    recs = tomllib.loads((ROOT / "data/records.toml").read_text())["record"]
    t, ev = spec["target"], spec["event"]
    parts = [svg_open(W, H, f"Tallest pancake stack record, {recs[0]['year']} to {recs[-1]['year']}, "
                            f"and our {t['build_to_in']:g} inch target")]
    parts.append(f'<rect width="{W}" height="{H}" rx="28" fill="{C["bg"]}"/>')
    parts.append(display(72, 94, f"Every record since {recs[0]['year']}.", 44, W - 144))
    parts.append(text(72, 128, "Tallest stack of pancakes, height in inches", 18, C["sub"]))
    parts.append(f'<rect x="48" y="156" width="{W - 96}" height="440" rx="24" fill="{C["paper"]}" stroke="{C["faint"]}"/>')
    x0, x1, yb, ytop = 136, 1196, 520, 216
    s = (yb - ytop) / 48
    for v in range(0, 49, 12):
        yy = yb - v * s
        parts.append(f'<line x1="{x0}" x2="{x1}" y1="{yy:.1f}" y2="{yy:.1f}" stroke="{C["faint"] if v else C["ink"]}" '
                     f'stroke-width="{1 if v else 1.5}"/>')
        parts.append(text(x0 - 14, round(yy + 5, 1), f"{v}", 13, C["sub"], 500, SANS, "end"))
    n = len(recs) + 1
    band = (x1 - x0) / n
    bw = 72
    best = max(r["cm"] for r in recs)
    for i, r in enumerate(recs):
        h_in = r["cm"] / 2.54
        cx = round(x0 + band * (i + 0.5), 1)
        hh = h_in * s
        parts.append(f'<rect x="{cx - bw / 2:.1f}" y="{yb - hh:.1f}" width="{bw}" height="{hh:.1f}" rx="10" fill="{C["pink"]}"/>')
        bold = r["cm"] == best
        parts.append(text(cx, round(yb - hh + 26, 1), f"{h_in:.1f}", 16 if bold else 15, C["ink"], 700 if bold else 600, SANS, "middle"))
        parts.append(text(cx, yb + 30, str(r["year"]), 15, C["ink"], 600, SANS, "middle"))
        parts.append(text(cx, yb + 50, r["place"], 13, C["sub"], 400, SANS, "middle"))
    # ours
    cx = round(x0 + band * (n - 0.5), 1)
    hh = t["build_to_in"] * s
    parts.append(f'<rect x="{cx - bw / 2:.1f}" y="{yb - hh:.1f}" width="{bw}" height="{hh:.1f}" rx="10" fill="{C["purple1"]}" '
                 f'stroke="{C["purple4"]}" stroke-width="2" stroke-dasharray="7 5"/>')
    parts.append(text(cx, round(yb - hh - 12, 1), f"{t['build_to_in']:g}?", 16, C["purple4"], 700, SANS, "middle"))
    parts.append(text(cx, yb + 30, ev["date"], 15, C["purple4"], 600, SANS, "middle"))
    parts.append(text(cx, yb + 50, ev["place"], 13, C["sub"], 400, SANS, "middle"))
    parts.append(mascot(round(cx - 30, 1), round(yb - hh / 2 - 30, 1), 60))
    # record line
    yy = yb - t["record_height_in"] * s
    parts.append(f'<line x1="{x0}" x2="{x1}" y1="{yy:.1f}" y2="{yy:.1f}" stroke="{C["pink4"]}" stroke-width="1.5" stroke-dasharray="6 5"/>')
    parts.append(text(x0 + 8, round(yy - 10, 1), f"Record to beat · {t['record_height_in']} in", 14, C["ink"], 600, SANS))
    parts.append(text(72, 634, "Heights as reported at the time. Sources in data/records.toml.", 14, C["sub"]))
    parts.append("</svg>\n")
    return "\n".join(parts)


# ---------------------------------------------------------------- process strip
def top_band(x, y, w, r, h, fill) -> str:
    """A strip of height h along the top of a rounded rect (corner radius r > h), following its corners."""
    dx = r - math.sqrt(r * r - (r - h) ** 2)
    return (f'<path d="M{x + dx:.2f} {y + h} A{r} {r} 0 0 1 {x + r:.2f} {y} H{x + w - r:.2f} '
            f'A{r} {r} 0 0 1 {x + w - dx:.2f} {y + h} Z" fill="{fill}"/>')


def process(spec, plan) -> str:
    W, H = 1280, 380
    t, c = spec["target"], spec["cook"]
    rows = [
        [("Batter", f"rest {spec['batter']['rest_minutes']} min", "yellow"),
         ("Ring + dose", f"{c['griddle_temp_f'][0]}–{c['griddle_temp_f'][1]} °F", "yellow"),
         ("Flip once", "top goes matte", "yellow"),
         ("Cool flat", f"{c['cool_flat_minutes']} min, on a rack", "yellow"),
         ("Stack of 10", f"≈ {10 * c['target_cooked_thickness_in']:.1f} in?", "check")],
        [("Eat or donate", "nothing in the trash", "green"),
         ("Hold, measure", f"{spec['rules']['hold_seconds']} s, hands off", "pink"),
         ("Stop", f"at {t['build_to_in']:g} in", "pink"),
         ("Stack", "¼ turn each", "purple"),
         ("Sort", "by ring size", "purple")],
    ]
    parts = [svg_open(W, H, "From batter to plate: the process, step by step")]
    parts.append(f'<rect width="{W}" height="{H}" rx="28" fill="{C["bg"]}"/>')
    bw, bh, gap, r = 196, 96, 46, 24
    x0 = (W - (5 * bw + 4 * gap)) / 2
    ys = [96, 252]
    parts.append(eyebrow(x0, 58, "From batter to plate"))
    bands = {"yellow": C["yellow"], "check": C["yellow"], "purple": C["purple"], "pink": C["pink"], "green": C["green"]}
    centers = {}
    for row_i, row in enumerate(rows):
        for i, (title, sub, kind) in enumerate(row):
            x, y = x0 + i * (bw + gap), ys[row_i]
            # the check is a gate, not a step: a dashed edge
            edge = (f'stroke="{C["ink"]}" stroke-width="1" stroke-dasharray="5 4"' if kind == "check"
                    else f'stroke="{C["faint"]}" stroke-width="0.5"')
            parts.append(f'<rect x="{x:.0f}" y="{y}" width="{bw}" height="{bh}" rx="{r}" fill="{C["paper"]}"/>')
            parts.append(top_band(x, y, bw, r, 8, bands[kind]))
            parts.append(f'<rect x="{x:.0f}" y="{y}" width="{bw}" height="{bh}" rx="{r}" fill="none" {edge}/>')
            parts.append(display(x + 20, y + 54, title, 24, bw - 40))
            parts.append(text(x + 20, y + 78, sub, 14, C["sub"], 500, SANS))
            centers[(row_i, i)] = (x, y)
    def arrow(x1, y1, x2, y2):
        a = f'<line x1="{x1:.0f}" y1="{y1:.0f}" x2="{x2:.0f}" y2="{y2:.0f}" stroke="{C["ink"]}" stroke-width="2"/>'
        if x2 > x1: head = f'<path d="M{x2:.0f} {y2:.0f} l-9 -5 v10 z" fill="{C["ink"]}"/>'
        elif x2 < x1: head = f'<path d="M{x2:.0f} {y2:.0f} l9 -5 v10 z" fill="{C["ink"]}"/>'
        else: head = f'<path d="M{x2:.0f} {y2:.0f} l-5 -9 h10 z" fill="{C["ink"]}"/>'
        return a + head
    for i in range(4):
        x, y = centers[(0, i)]
        parts.append(arrow(x + bw + 6, y + bh / 2, x + bw + gap - 6, y + bh / 2))
        x, y = centers[(1, i + 1)]
        parts.append(arrow(x - 6, y + bh / 2, x - gap + 6, y + bh / 2))
    x, y = centers[(0, 4)]
    parts.append(arrow(x + bw / 2, y + bh + 6, x + bw / 2, ys[1] - 6))
    parts.append(text(x + bw / 2 + 10, y + bh + 34, "yes", 13, C["ink"], 600, SANS))
    # "no" loop back to the dose
    xd, yd = centers[(0, 1)]
    parts.append(f'<path d="M{x + bw / 2:.0f} {y - 6} V{y - 26} H{xd + bw / 2:.0f} V{yd - 6}" fill="none" stroke="{C["pink4"]}" stroke-width="2" stroke-dasharray="6 4"/>')
    parts.append(f'<path d="M{xd + bw / 2:.0f} {yd - 4} l-5 -9 h10 z" fill="{C["pink4"]}"/>')
    parts.append(text((x + xd + bw) / 2, y - 34, "no: fix the dose", 13, C["pink4"], 600, SANS, "middle"))
    parts.append("</svg>\n")
    return "\n".join(parts)


# ---------------------------------------------------------------- page
def path_bbox(*paths: str) -> tuple[float, float, float, float]:
    """Bounding box of absolute-coordinate paths (control points included, so a hair generous)."""
    nums = [float(n) for d in paths for n in re.findall(r"-?\d+(?:\.\d+)?(?:e-?\d+)?", d)]
    xs, ys = nums[0::2], nums[1::2]
    return min(xs), min(ys), max(xs), max(ys)


def sprite() -> str:
    """Symbols the page reuses with <use>: logo, mascot, a two-tone pancake, a check."""
    mon = (BRAND / "pancake-monster.svg").read_text()
    side, top = re.findall(r'<path d="([^"]+)" fill="[^"]+"/>', mon)[:2]  # the bottom pancake
    x0, y0, x1, y1 = path_bbox(side, top)
    check = re.search(r'<path d="([^"]+)"', (BRAND / "icon-check.svg").read_text()).group(1)
    return (
        '<svg class="sprite" aria-hidden="true" focusable="false"><defs>'
        f'<symbol id="logo" viewBox="0 0 422 166"><path fill="currentColor" d="{logo_path()}"/></symbol>'
        f'<symbol id="mascot" viewBox="340 362 348 352">{mascot_inner()}</symbol>'
        f'<symbol id="cake" viewBox="{x0:.1f} {y0:.1f} {x1 - x0:.1f} {y1 - y0:.1f}" preserveAspectRatio="none">'
        f'<path d="{side}" fill="var(--cake-side)"/><path d="{top}" fill="var(--cake-top)"/></symbol>'
        f'<symbol id="check" viewBox="0 0 24 24"><path fill="currentColor" d="{check}"/></symbol>'
        "</defs></svg>"
    )


def step_art(kind: str) -> str:
    """The three failure modes, drawn with the two-tone pancake. Colours come from the card's --cake-* tokens."""
    W, H, ground, cx = 464, 426, 352, 232
    ink = C["ink"]
    out = [f'<svg class="step-art" viewBox="0 0 {W} {H}" aria-hidden="true" focusable="false">']

    def cake(x_mid, bottom, w, h, rot=0.0):
        turn = f' transform="rotate({rot:g} {x_mid:.1f} {bottom - h / 2:.1f})"' if rot else ""
        return f'<use href="#cake" x="{x_mid - w / 2:.1f}" y="{bottom - h:.1f}" width="{w:.1f}" height="{h:.1f}"{turn}/>'

    def pile(sizes):
        bottom, tops = ground, []
        for w, h, dx in sizes:
            out.append(cake(cx + dx, bottom, w, h))
            tops.append(bottom - h)
            bottom -= h * 0.3
        return tops[-1]

    if kind == "squash":
        top = pile([(316, 40, 0), (296, 46, 0), (278, 52, 0), (262, 58, 0), (250, 63, 0), (240, 68, 0)])
        for dx in (-44, 44):
            x = cx + dx
            out.append(f'<path d="M{x} {top - 76:.1f}V{top - 22:.1f}M{x - 9} {top - 33:.1f}L{x} {top - 22:.1f}L{x + 9} {top - 33:.1f}" '
                       f'stroke="{ink}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" fill="none"/>')
    elif kind == "lean":
        top = pile([(232, 62, i * 11 - 44) for i in range(9)])
        out.append(f'<line x1="{cx - 44}" x2="{cx - 44}" y1="{ground + 6}" y2="{top - 44:.1f}" stroke="{ink}" '
                   f'stroke-width="2" stroke-dasharray="2 7" stroke-linecap="round"/>')
        out.append(f'<path d="M{cx - 36} {top - 30:.1f}H{cx + 40}M{cx + 31} {top - 38:.1f}L{cx + 40} {top - 30:.1f}L{cx + 31} {top - 22:.1f}" '
                   f'stroke="{ink}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" fill="none"/>')
    else:  # greedy
        top = pile([(240, 62, 0)] * 7)
        line_y = top - 20
        out.append(f'<line x1="40" x2="424" y1="{line_y:.1f}" y2="{line_y:.1f}" stroke="{C["pink4"]}" stroke-width="2.5" '
                   f'stroke-dasharray="8 7" stroke-linecap="round"/>')
        out.append(cake(cx + 92, line_y - 34, 220, 58, -16))
        for i, r in enumerate((18, 30)):
            out.append(f'<path d="M{cx - 30 - i * 14} {line_y - 66 - i * 10:.1f}q{-r} 6 {-r - 8} {r}" stroke="{ink}" '
                       f'stroke-width="2.5" stroke-linecap="round" fill="none"/>')
    out.append(f'<line x1="56" x2="408" y1="{ground + 8}" y2="{ground + 8}" stroke="{ink}" stroke-width="2.5" stroke-linecap="round"/>')
    out.append("</svg>")
    return "".join(out)


def art(name: str, cls: str, stretch: bool = False) -> str:
    """A brand SVG from assets/brand, inlined as decoration. The cream core follows the page colour.
    stretch: the art may widen past its artboard without growing taller (pancake.ai's hero above 1654 px)."""
    head, body = (BRAND / f"{name}.svg").read_text().strip().split(">", 1)
    head = re.sub(r'\s(?:width|height|xmlns)="[^"]*"', "", head)
    par = ' preserveAspectRatio="none"' if stretch else ""
    svg = head.replace("<svg", f'<svg class="{cls}" aria-hidden="true" focusable="false"{par}', 1) + ">" + body
    return re.sub(r'fill="#(?:FBF6F1|fbf6f1)"', 'class="core"', svg)


def fmt_value(v, spec: str) -> str:
    if spec:
        return format(v, spec)
    if isinstance(v, float):
        return f"{v:g}"
    return str(v)


def fill_numbers(tpl: str, ns: dict) -> str:
    """{{spec.cook.rest|.2f}} -> the value from recipe.toml / the plan. Every number in the copy comes from here."""
    def sub(m):
        cur = ns[m.group(1)]
        for key in m.group(2).split("."):
            cur = cur[int(key)] if isinstance(cur, list) else cur[key]
        return html.escape(fmt_value(cur, m.group(3) or ""))
    return re.sub(r"\{\{(spec|plan|best|first|calc)\.([a-z0-9_.]+)(?:\|([^}]+))?\}\}", sub, tpl)


def page(spec, plan, recs, tower_svg) -> str:
    site = ROOT / "site"
    tpl = (site / "index.template.html").read_text()
    css, js = (site / "page.css").read_text(), (site / "page.js").read_text()
    assert "</style" not in css and "</script" not in js, "page.css / page.js must not close their own tag"
    best = max(recs, key=lambda r: r["cm"])
    best = {**best, "in": round(best["cm"] / 2.54, 1)}
    first = {**recs[0], "in": round(recs[0]["cm"] / 2.54, 1)}
    ns = {"spec": spec, "plan": plan, "best": best, "first": first, "calc": {
        "thick_min": round(spec["cook"]["reject_below_in"] - 0.02, 3),   # the slider reaches past both reject limits
        "settle_pct": round(spec["target"]["settle_ratio"] * 100),
        "spare_pct": round(spec["cook"]["spare_ratio"] * 100),
        "stack10_in": round(10 * plan["thickness_in"], 2),
        "major": spec["meta"]["version"].split(".")[0],
    }}
    blocks = {
        "{{TOKENS_CSS}}": tokens_css(), "{{SPRITE}}": sprite(), "{{TOWER_SVG}}": tower_svg,
        "{{ART_HERO}}": art("rainbow-hero", "rainbow", stretch=True), "{{ART_FOOTER}}": art("rainbow-footer", "rainbow"),
        "{{ART_CTA_LEFT}}": art("rainbow-cta-left", "sliver sliver-l"),
        "{{ART_CTA_RIGHT}}": art("rainbow-cta-right", "sliver sliver-r"),
        "{{ART_CLOUD_A}}": art("sky-cloud-a", "cloud cloud-a"), "{{ART_CLOUD_B}}": art("sky-cloud-b", "cloud cloud-b"),
        "{{ART_HILL_TOP}}": art("sky-hill-top", "hill hill-top"),
        "{{ART_HILL_BOTTOM}}": art("sky-hill-top", "hill hill-bottom"),
        "{{ART_STEP_SQUASH}}": step_art("squash"), "{{ART_STEP_LEAN}}": step_art("lean"),
        "{{ART_STEP_GREEDY}}": step_art("greedy"),
    }
    for key, val in blocks.items():
        assert key in tpl, f"placeholder {key} missing from the template"
        tpl = tpl.replace(key, val)
    tpl = fill_numbers(tpl, ns)
    left = re.findall(r"\{\{[^}]*\}\}", tpl.replace("{{CSS}}", "").replace("{{JS}}", "").replace("{{SPEC_JSON}}", ""))
    assert not left, f"unresolved placeholders: {left}"
    data =json.dumps({"spec": spec, "plan": plan, "records": recs}, separators=(",", ":")).replace("<", "\\u003c")
    return tpl.replace("{{CSS}}", css).replace("{{JS}}", js).replace("{{SPEC_JSON}}", data)


def outputs() -> dict[Path, str]:
    spec = load_spec()
    plan = compute(spec)
    recs = tomllib.loads((ROOT / "data/records.toml").read_text())["record"]
    tower_svg = tower(spec, plan)  # bare: the page inlines it and brings its own fonts
    return {
        ROOT / "docs/index.html": page(spec, plan, recs, tower_svg),
        ROOT / "docs/.nojekyll": "",
        ROOT / "docs/tower.svg": with_font(tower_svg),
        ROOT / "assets/hero.svg": with_font(hero(spec, plan)),
        ROOT / "assets/tower.svg": with_font(tower_svg),
        ROOT / "assets/records.svg": with_font(records(spec, plan)),
        ROOT / "assets/process.svg": with_font(process(spec, plan)),
        ROOT / "docs/spec.json": json.dumps({"spec": spec, "plan": plan, "records": recs}, indent=2) + "\n",
    }


def main() -> int:
    check = "--check" in sys.argv
    stale = []
    for path, content in outputs().items():
        if check:
            if not path.exists() or path.read_text() != content:
                stale.append(path.relative_to(ROOT))
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
            print(f"wrote {path.relative_to(ROOT)}")
    if stale:
        print("Out of date, run python3 tools/render.py:", *stale, sep="\n  ")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
