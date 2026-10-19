#!/usr/bin/env python3
"""Pancake Tower calculator.

Reads recipe.toml and prints the cooking plan, the shopping list and the
height check. Python 3.11+, no dependencies.

    python3 calc.py                      # plan for one attempt
    python3 calc.py --attempts 2         # enough pancakes for a second try
    python3 calc.py --thickness 0.15     # re-plan with your measured thickness
    python3 calc.py --check              # exit 1 if the spec breaks a rule
    python3 calc.py --json               # spec + plan as JSON (feeds the page)
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ML_PER_CUBIC_IN = 16.387064
ML_PER_FL_OZ = 29.5735
ML_PER_GALLON = 3785.41
G_PER_OZ = 28.3495
MILK_G_PER_ML = 1.03
PCT_KEYS = ["flour_all_purpose", "whole_milk", "eggs", "sugar", "salt", "baking_powder", "neutral_oil"]


def load_spec(path: Path = ROOT / "recipe.toml") -> dict:
    with path.open("rb") as f:
        return tomllib.load(f)


def compute(spec: dict, attempts: int = 1, spare: float | None = None, thickness: float | None = None) -> dict:
    """Every derived number, in one place. The page and the drawings read this."""
    cook, batter, target, rules = spec["cook"], spec["batter"], spec["target"], spec["rules"]
    spare = cook["spare_ratio"] if spare is None else spare
    thick = cook["target_cooked_thickness_in"] if thickness is None else thickness
    dens = batter["density_g_per_ml"]
    settled = thick * (1 - target["settle_ratio"])

    sizes, total_ml, total_cook, total_tower = [], 0.0, 0, 0
    for z in spec["size"]:
        r = z["ring_in"] / 2
        ml = math.pi * r * r * cook["raw_depth_in"] * ML_PER_CUBIC_IN
        n_cook = math.ceil(z["in_tower"] * attempts * (1 + spare))
        sizes.append({
            "name": z["name"],
            "ring_in": z["ring_in"],
            "in_tower": z["in_tower"],
            "to_cook": n_cook,
            "dose_ml": round(ml, 1),
            "dose_fl_oz": round(ml / ML_PER_FL_OZ, 2),
            "dose_g": round(ml * dens, 1),
            "tier_height_in": round(z["in_tower"] * settled, 2),
        })
        total_ml += ml * n_cook
        total_cook += n_cook
        total_tower += z["in_tower"]

    exp = {k: v for k, v in spec.get("experimental", {}).items() if v}
    pct_total = sum(batter[k] for k in PCT_KEYS) + sum(exp.values())
    batter_g = total_ml * dens
    flour_g = batter_g / pct_total * 100
    shopping = []
    for k in PCT_KEYS + list(exp):
        pct = batter.get(k, exp.get(k))
        g = flour_g * pct / 100
        item = {"key": k, "pct": pct, "g": round(g)}
        if k == "whole_milk":
            item["l"] = round(g / MILK_G_PER_ML / 1000, 1)
            item["gal"] = round(g / MILK_G_PER_ML / ML_PER_GALLON, 1)
        if k == "eggs":
            item["count"] = math.ceil(g / cook["egg_weight_g"])
        shopping.append(item)

    height = total_tower * settled
    warnings = []
    if height < target["build_to_in"]:
        warnings.append(f"Tower of {total_tower} only reaches ~{height:.1f} in: add pancakes or check thickness.")
    for z in spec["size"]:
        if z["ring_in"] > rules["max_diameter_in"] - 0.5:
            warnings.append(f"{z['name']} ring {z['ring_in']} in leaves < 0.5 in under the max width.")
        if z["ring_in"] < rules["min_diameter_in"] + 0.5:
            warnings.append(f"{z['name']} ring {z['ring_in']} in leaves < 0.5 in above the min width.")
    if thick > rules["max_thickness_in"]:
        warnings.append("Cooked thickness is over the 0.39 in limit.")
    if exp:
        warnings.append(f"Experimental ingredients ON ({', '.join(exp)}): needs written adjudicator approval.")

    return {
        "attempts": attempts,
        "spare_ratio": spare,
        "thickness_in": thick,
        "sizes": sizes,
        "pancakes_in_tower": total_tower,
        "pancakes_to_cook": total_cook,
        "batter_l": round(total_ml / 1000, 1),
        "batter_gal": round(total_ml / ML_PER_GALLON, 1),
        "batter_kg": round(batter_g / 1000, 1),
        "shopping": shopping,
        "height_in": round(height, 1),
        "pancakes_to_stop_line": math.ceil(target["build_to_in"] / settled),
        "warnings": warnings,
    }


def lb_oz(grams: float) -> str:
    total_oz = grams / G_PER_OZ
    lb, oz = divmod(total_oz, 16)
    return f"{int(lb)} lb {oz:.0f} oz" if lb >= 1 else f"{total_oz:.1f} oz"


def report(spec: dict, plan: dict) -> str:
    t, cook = spec["target"], spec["cook"]
    out = [f"# Pancake Tower plan — spec v{spec['meta']['version']} ({spec['meta']['status']})\n"]
    if spec["meta"]["status"] != "validated":
        out.append("> Untested numbers. Validate them at the rehearsal and log results in TESTLOG.md.\n")
    out += ["## What to cook\n",
            "| Size | Ring | In tower | To cook | Batter per pancake | Weight per pancake |",
            "|---|---|---|---|---|---|"]
    for z in plan["sizes"]:
        out.append(f"| {z['name']} | {z['ring_in']} in | {z['in_tower'] * plan['attempts']} | {z['to_cook']} | "
                   f"{z['dose_fl_oz']:.1f} fl oz ({z['dose_ml']:.0f} ml) | {z['dose_g'] / G_PER_OZ:.1f} oz ({z['dose_g']:.0f} g) |")
    out.append(f"| **total** | | **{plan['pancakes_in_tower'] * plan['attempts']}** | **{plan['pancakes_to_cook']}** | | |\n")

    out += ["## Shopping list\n",
            f"Batter needed: {plan['batter_l']} L ({plan['batter_gal']} gal), {plan['batter_kg']} kg. "
            f"Rest it {spec['batter']['rest_minutes']} min, covered.\n",
            "| Ingredient | % of flour | Metric | US |", "|---|---|---|---|"]
    for s in plan["shopping"]:
        name = s["key"].replace("_", " ")
        if "gal" in s:
            metric, us = f"{s['l']} L", f"{s['gal']} gal"
        elif "count" in s:
            metric, us = f"{s['g'] / 1000:.2f} kg", f"{s['count']} large eggs"
        else:
            metric = f"{s['g'] / 1000:.2f} kg" if s["g"] >= 1000 else f"{s['g']} g"
            us = lb_oz(s["g"])
        out.append(f"| {name} | {s['pct']:g} | {metric} | {us} |")

    out += ["\n## Height check\n",
            f"- Cooked thickness used: {plan['thickness_in']:.3f} in "
            f"(reject below {cook['reject_below_in']} or above {cook['reject_above_in']} in)",
            f"- One tower of {plan['pancakes_in_tower']} pancakes ≈ **{plan['height_in']} in** after settling",
            f"- Record to beat: {t['record_height_in']} in. Slow down at {t['slow_down_at_in']} in. STOP at {t['build_to_in']} in",
            f"- Pancakes needed to reach the STOP line at this thickness: ~{plan['pancakes_to_stop_line']}"]
    if plan["warnings"]:
        out.append("\n## Warnings\n")
        out += [f"- {w}" for w in plan["warnings"]]
    return "\n".join(out)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--spec", default=ROOT / "recipe.toml", type=Path)
    p.add_argument("--attempts", type=int, default=1, help="number of full towers to cook for")
    p.add_argument("--spare", type=float, help="override spare ratio (0.30 = +30%%)")
    p.add_argument("--thickness", type=float, help="measured cooked thickness, inches")
    p.add_argument("--check", action="store_true", help="exit 1 if the spec triggers any warning")
    p.add_argument("--json", action="store_true", help="print spec + plan as JSON")
    a = p.parse_args()

    spec = load_spec(a.spec)
    plan = compute(spec, a.attempts, a.spare, a.thickness)
    if a.json:
        print(json.dumps({"spec": spec, "plan": plan}, indent=2))
    else:
        print(report(spec, plan))
    return 1 if (a.check and plan["warnings"]) else 0


if __name__ == "__main__":
    sys.exit(main())
