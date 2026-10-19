#!/usr/bin/env python3
"""Draws the repo's figures from recipe.toml and data/records.toml.

    python3 tools/render.py          # writes assets/*.svg and docs/spec.json
    python3 tools/render.py --check  # exit 1 if any output is out of date

Change a number in recipe.toml, run this, and the drawings follow.
"""

from __future__ import annotations

import json
import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from calc import compute, load_spec  # noqa: E402

# Pancake brand palette (get-pancake/website, _design-kit/tokens.css)
C = {
    "bg": "#FBF6F1", "paper": "#FFFCF8", "ink": "#2C002A", "sub": "#85687C", "line": "#DDCFCD",
    "faint": "#EFE4DC", "pink": "#FF7AA0", "pink2": "#FFBBC7", "pink4": "#E33A6A",
    "purple": "#BA8BFF", "purple1": "#EFDDF1", "purple2": "#DEC3F5", "purple4": "#8D43FD",
    "yellow": "#FFBD7A", "yellow2": "#FFDBB5", "yellow4": "#F38F43", "green": "#68CEA7", "blue": "#4660E7",
}
SANS = "Geist, 'Helvetica Neue', Helvetica, Arial, sans-serif"
MONO = "'Geist Mono', ui-monospace, 'SF Mono', Menlo, Consolas, monospace"
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
def hero(spec, plan) -> str:
    W, H = 1280, 640
    t = spec["target"]
    s = 10  # px per inch
    base_y, cx = 584, 872
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
    # rainbow arcs, bottom-right corner (landing page motif)
    for r, col in [(960, "green"), (905, "blue"), (885, "purple"), (830, "pink"), (775, "yellow"), (720, "bg")]:
        parts.append(f'<circle cx="2000" cy="500" r="{r}" fill="{C[col]}"/>')
    # left column
    parts.append(logo(72, 60, 168))
    parts.append(text(74, 196, "OPEN SOURCE  ·  OCT 29, 2026  ·  SAN FRANCISCO", 15, C["sub"], 500, MONO, extra=' letter-spacing="1.6"'))
    parts.append(text(70, 274, "We promised a", 68, C["ink"], 700, extra=' letter-spacing="-2"'))
    parts.append(text(70, 350, "world record.", 68, C["ink"], 700, extra=' letter-spacing="-2"'))
    parts.append(text(70, 426, "Here’s the recipe.", 68, C["pink4"], 700, extra=' letter-spacing="-2"'))
    parts.append(text(72, 482, "Recipe, build protocol and calculator for the", 22, C["sub"]))
    parts.append(text(72, 512, "tallest pancake stack ever built.", 22, C["sub"]))
    x = 72
    for label in [f"{t['record_height_in']} in to beat", f"{t['build_to_in']:g} in stop line",
                  f"~{plan['pancakes_in_tower']} pancakes", f"{spec['rules']['hold_seconds']} s hold"]:
        w = 24 + len(label) * 8.7
        parts.append(f'<rect x="{x}" y="548" width="{w:.0f}" height="38" rx="19" fill="{C["paper"]}" stroke="{C["line"]}"/>')
        parts.append(text(x + w / 2, 572, label, 14, C["ink"], 500, MONO, "middle"))
        x += w + 10
    # ruler
    rx = cx - 78
    parts.append(f'<g class="later"><line x1="{rx}" x2="{rx}" y1="{base_y}" y2="{base_y - 48 * s}" stroke="{C["sub"]}" stroke-width="1.5"/>')
    for i in range(0, 49, 6):
        yy = base_y - i * s
        parts.append(f'<line x1="{rx - 8}" x2="{rx}" y1="{yy}" y2="{yy}" stroke="{C["sub"]}" stroke-width="1.5"/>')
        parts.append(text(rx - 14, yy + 5, f"{i}", 13, C["sub"], 500, MONO, "end"))
    parts.append(text(rx - 14, base_y - 49.5 * s, "in", 13, C["sub"], 500, MONO, "end"))
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
    parts.append(text(72, 56, "ELEVATION", 14, C["sub"], 600, MONO, extra=' letter-spacing="1.5"'))
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
    parts.append(text(px0 + 22, py0 + 34, "PLAN", 14, C["sub"], 600, MONO, extra=' letter-spacing="1.5"'))
    parts.append(text(px0 + 70, py0 + 34, "from above · to scale", 14, C["sub"], 400, MONO))
    for z in plan["sizes"]:
        r = z["ring_in"] * ps / 2
        parts.append(f'<circle cx="{pcx}" cy="{pcy}" r="{r}" fill="{C[TIER[z["name"]][0]]}" stroke="{C["paper"]}" stroke-width="2"/>')
    parts.append(f'<line x1="{pcx}" x2="{pcx}" y1="{py0 + 52}" y2="{py0 + ph - 18}" stroke="{C["purple4"]}" stroke-width="1.5" stroke-dasharray="2 5"/>')
    parts.append(f'<line x1="{px0 + 18}" x2="{px0 + pw - 18}" y1="{pcy}" y2="{pcy}" stroke="{C["purple4"]}" stroke-width="1.5" stroke-dasharray="2 5"/>')
    parts.append(text(pcx + 8, py0 + 64, "A", 13, C["purple4"], 700, MONO))
    parts.append(text(px0 + pw - 22, pcy - 8, "B", 13, C["purple4"], 700, MONO, "end"))
    # quarter-turn arrow
    import math
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
    parts.append(text(812, ny, "NOTES", 14, C["sub"], 600, MONO, extra=' letter-spacing="1.5"'))
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
    parts.append(text(tx + 22, ty + 50, "PANCAKE TOWER", 26, C["ink"], 700, extra=' letter-spacing="-0.5"'))
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
    W, H = 1280, 660
    recs = tomllib.loads((ROOT / "data/records.toml").read_text())["record"]
    t = spec["target"]
    x0, x1, yb, ytop = 150, 1210, 548, 168
    s = (yb - ytop) / 48
    parts = [svg_open(W, H, "Tallest pancake stack record, 2012 to 2025, and our 45 inch target")]
    parts.append(f'<rect width="{W}" height="{H}" rx="28" fill="{C["bg"]}"/>')
    parts.append(text(72, 84, "Every record since 2012", 36, C["ink"], 700, extra=' letter-spacing="-1"'))
    parts.append(text(72, 118, "Tallest stack of pancakes, height in inches", 18, C["sub"]))
    for v in range(0, 49, 12):
        yy = yb - v * s
        parts.append(f'<line x1="{x0}" x2="{x1}" y1="{yy:.1f}" y2="{yy:.1f}" stroke="{C["line"] if v else C["ink"]}" stroke-width="{1 if v else 1.5}"/>')
        parts.append(text(x0 - 14, yy + 5, f"{v}", 14, C["sub"], 500, MONO, "end"))
    parts.append(text(x0 - 14, ytop - 18, "in", 14, C["sub"], 500, MONO, "end"))
    n = len(recs) + 1
    band = (x1 - x0) / n
    bw = 70
    best = max(r["cm"] for r in recs)
    for i, r in enumerate(recs):
        h_in = r["cm"] / 2.54
        cx = x0 + band * (i + 0.5)
        hh = h_in * s
        parts.append(f'<rect x="{cx - bw / 2:.1f}" y="{yb - hh:.1f}" width="{bw}" height="{hh:.1f}" rx="10" fill="{C["pink"]}"/>')
        for k in range(1, int(h_in // 2) - 1):
            yy = yb - k * 2 * s
            parts.append(f'<line x1="{cx - bw / 2 + 6:.1f}" x2="{cx + bw / 2 - 6:.1f}" y1="{yy:.1f}" y2="{yy:.1f}" stroke="{C["pink2"]}" stroke-width="1.2"/>')
        bold = r["cm"] == best
        parts.append(text(cx, yb - hh + 26, f"{h_in:.1f}", 17 if bold else 15, C["ink"], 700 if bold else 600, MONO, "middle"))
        parts.append(text(cx, yb + 28, str(r["year"]), 16, C["ink"], 700, MONO, "middle"))
        parts.append(text(cx, yb + 50, r["place"], 14, C["sub"], 400, SANS, "middle"))
    # ours
    cx = x0 + band * (n - 0.5)
    hh = t["build_to_in"] * s
    parts.append(f'<rect x="{cx - bw / 2:.1f}" y="{yb - hh:.1f}" width="{bw}" height="{hh:.1f}" rx="10" fill="{C["purple1"]}" stroke="{C["purple4"]}" stroke-width="2" stroke-dasharray="7 5"/>')
    parts.append(text(cx, yb - hh - 12, f"{t['build_to_in']:g}?", 17, C["purple4"], 700, MONO, "middle"))
    parts.append(text(cx, yb + 28, "Oct 29, 2026", 16, C["purple4"], 700, MONO, "middle"))
    parts.append(text(cx, yb + 50, "San Francisco", 14, C["sub"], 400, SANS, "middle"))
    parts.append(mascot(cx - 30, yb - hh / 2 - 30, 60))
    # record line
    yy = yb - t["record_height_in"] * s
    parts.append(f'<line x1="{x0}" x2="{x1}" y1="{yy:.1f}" y2="{yy:.1f}" stroke="{C["pink4"]}" stroke-width="1.5" stroke-dasharray="6 5"/>')
    parts.append(text(x0 + 8, yy - 10, f"record to beat · {t['record_height_in']} in", 14, C["pink4"], 600, MONO))
    parts.append(text(72, 636, "Heights as reported at the time. Sources in data/records.toml.", 14, C["sub"]))
    parts.append("</svg>\n")
    return "\n".join(parts)


# ---------------------------------------------------------------- process strip
def process(spec, plan) -> str:
    W, H = 1280, 380
    t, c = spec["target"], spec["cook"]
    rows = [
        [("Batter", f"rest {spec['batter']['rest_minutes']} min", "yellow"),
         ("Ring + dose", f"{c['griddle_temp_f'][0]}–{c['griddle_temp_f'][1]} °F", "yellow"),
         ("Flip once", "top goes matte", "yellow"),
         ("Cool flat", f"{c['cool_flat_minutes']} min, on a rack", "yellow"),
         ("Stack of 10", "1.45–1.75 in?", "check")],
        [("Eat or donate", "nothing in the trash", "green"),
         ("Hold, measure", f"{spec['rules']['hold_seconds']} s, hands off", "pink"),
         ("Stop", f"at {t['build_to_in']:g} in", "pink"),
         ("Stack", "¼ turn each", "purple"),
         ("Sort", "by ring size", "purple")],
    ]
    parts = [svg_open(W, H, "From batter to plate: the process, step by step")]
    parts.append(f'<rect width="{W}" height="{H}" rx="28" fill="{C["bg"]}"/>')
    parts.append(text(56, 58, "FROM BATTER TO PLATE", 14, C["sub"], 600, MONO, extra=' letter-spacing="1.5"'))
    bw, bh, gap = 196, 92, 46
    x0 = (W - (5 * bw + 4 * gap)) / 2
    ys = [96, 252]
    fills = {"yellow": "yellow2", "check": "paper", "purple": "purple2", "pink": "pink2", "green": "faint"}
    centers = {}
    for r, row in enumerate(rows):
        for i, (title, sub, kind) in enumerate(row):
            x = x0 + i * (bw + gap)
            y = ys[r]
            stroke = C["ink"] if kind == "check" else "none"
            dash = ' stroke-dasharray="6 4"' if kind == "check" else ""
            parts.append(f'<rect x="{x:.0f}" y="{y}" width="{bw}" height="{bh}" rx="18" fill="{C[fills[kind]]}" stroke="{stroke}" stroke-width="1.5"{dash}/>')
            parts.append(text(x + 20, y + 40, title, 20, C["ink"], 700))
            parts.append(text(x + 20, y + 66, sub, 14, C["sub"], 500, MONO))
            centers[(r, i)] = (x, y)
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
    parts.append(text(x + bw / 2 + 10, y + bh + 36, "yes", 13, C["ink"], 700, MONO))
    # "no" loop back to the dose
    xd, yd = centers[(0, 1)]
    parts.append(f'<path d="M{x + bw / 2:.0f} {y - 6} V{y - 26} H{xd + bw / 2:.0f} V{yd - 6}" fill="none" stroke="{C["pink4"]}" stroke-width="2" stroke-dasharray="6 4"/>')
    parts.append(f'<path d="M{xd + bw / 2:.0f} {yd - 4} l-5 -9 h10 z" fill="{C["pink4"]}"/>')
    parts.append(text((x + xd + bw) / 2, y - 34, "no: fix the dose", 13, C["pink4"], 700, MONO, "middle"))
    parts.append("</svg>\n")
    return "\n".join(parts)


def page(spec, plan, recs, tower_svg) -> str:
    tpl = (ROOT / "site/index.template.html").read_text()
    data = json.dumps({"spec": spec, "plan": plan, "records": recs}, separators=(",", ":")).replace("</", "<\\/")
    return (tpl.replace("{{LOGO_PATH}}", logo_path())
               .replace("{{MASCOT}}", mascot_inner())
               .replace("{{TOWER_SVG}}", tower_svg.replace("<title>", '<title id="tower-title">', 1))
               .replace("{{SPEC_JSON}}", data))


def outputs() -> dict[Path, str]:
    spec = load_spec()
    plan = compute(spec)
    recs = tomllib.loads((ROOT / "data/records.toml").read_text())["record"]
    tower_svg = tower(spec, plan)
    return {
        ROOT / "docs/index.html": page(spec, plan, recs, tower_svg),
        ROOT / "docs/.nojekyll": "",
        ROOT / "assets/hero.svg": hero(spec, plan),
        ROOT / "assets/tower.svg": tower_svg,
        ROOT / "assets/records.svg": records(spec, plan),
        ROOT / "assets/process.svg": process(spec, plan),
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
