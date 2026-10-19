#!/usr/bin/env python3
"""Pancake Tower calculator.

Reads recipe.toml and prints the cooking plan, the shopping list and the
height check. No dependencies beyond Python 3.11+.

    python3 calc.py                      # plan for one attempt
    python3 calc.py --attempts 2         # enough pancakes for a second try
    python3 calc.py --thickness 0.15     # re-plan with your measured thickness
"""

from __future__ import annotations

import argparse
import math
import sys
import tomllib
from pathlib import Path

ML_PER_CUBIC_IN = 16.387064
ML_PER_FL_OZ = 29.5735
ML_PER_GALLON = 3785.41
G_PER_OZ = 28.3495
G_PER_LB = 453.592
MILK_G_PER_ML = 1.03


def lb_oz(grams: float) -> str:
    total_oz = grams / G_PER_OZ
    lb, oz = divmod(total_oz, 16)
    if lb >= 1:
        return f"{int(lb)} lb {oz:.0f} oz"
    return f"{total_oz:.1f} oz"


def load(path: Path) -> dict:
    with path.open("rb") as f:
        return tomllib.load(f)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--spec", default=Path(__file__).with_name("recipe.toml"), type=Path)
    p.add_argument("--attempts", type=int, default=1, help="number of full towers to cook for")
    p.add_argument("--spare", type=float, help="override spare ratio (0.30 = +30%%)")
    p.add_argument("--thickness", type=float, help="measured cooked thickness, inches")
    a = p.parse_args()

    s = load(a.spec)
    cook, batter, target, rules = s["cook"], s["batter"], s["target"], s["rules"]
    spare = cook["spare_ratio"] if a.spare is None else a.spare
    thick = cook["target_cooked_thickness_in"] if a.thickness is None else a.thickness
    dens = batter["density_g_per_ml"]

    print(f"# Pancake Tower plan — spec v{s['meta']['version']} ({s['meta']['status']})\n")
    if s["meta"]["status"] != "validated":
        print("> Untested numbers. Validate them at the rehearsal and log results in TESTLOG.md.\n")

    # --- cooking plan -------------------------------------------------------
    print("## What to cook\n")
    print("| Size | Ring | In tower | To cook | Batter per pancake | Weight per pancake |")
    print("|---|---|---|---|---|---|")
    total_ml = 0.0
    total_cook = 0
    total_tower = 0
    for z in s["size"]:
        r = z["ring_in"] / 2
        ml = math.pi * r * r * cook["raw_depth_in"] * ML_PER_CUBIC_IN
        n_tower = z["in_tower"] * a.attempts
        n_cook = math.ceil(n_tower * (1 + spare))
        total_ml += ml * n_cook
        total_cook += n_cook
        total_tower += z["in_tower"]
        print(f"| {z['name']} | {z['ring_in']} in | {n_tower} | {n_cook} | "
              f"{ml / ML_PER_FL_OZ:.1f} fl oz ({ml:.0f} ml) | {ml * dens / G_PER_OZ:.1f} oz ({ml * dens:.0f} g) |")
    print(f"| **total** | | **{total_tower * a.attempts}** | **{total_cook}** | | |\n")

    # --- shopping list ------------------------------------------------------
    pct_keys = ["flour_all_purpose", "whole_milk", "eggs", "sugar", "salt", "baking_powder", "neutral_oil"]
    exp = {k: v for k, v in s.get("experimental", {}).items() if v}
    pct_total = sum(batter[k] for k in pct_keys) + sum(exp.values())
    batter_g = total_ml * dens
    flour_g = batter_g / pct_total * 100

    print("## Shopping list\n")
    print(f"Batter needed: {total_ml / 1000:.1f} L ({total_ml / ML_PER_GALLON:.1f} gal), "
          f"{batter_g / 1000:.1f} kg. Rest it {batter['rest_minutes']} min, covered.\n")
    print("| Ingredient | % of flour | Metric | US |")
    print("|---|---|---|---|")
    for k in pct_keys + list(exp):
        pct = batter.get(k, exp.get(k))
        g = flour_g * pct / 100
        name = k.replace("_", " ")
        if k == "whole_milk":
            ml = g / MILK_G_PER_ML
            us = f"{ml / ML_PER_GALLON:.1f} gal"
            metric = f"{ml / 1000:.1f} L"
        elif k == "eggs":
            us = f"{math.ceil(g / cook['egg_weight_g'])} large eggs"
            metric = f"{g / 1000:.2f} kg"
        else:
            us = lb_oz(g)
            metric = f"{g / 1000:.2f} kg" if g >= 1000 else f"{g:.0f} g"
        print(f"| {name} | {pct:g} | {metric} | {us} |")
    print()

    # --- height check -------------------------------------------------------
    est = total_tower * thick * (1 - target["settle_ratio"])
    needed = math.ceil(target["build_to_in"] / (thick * (1 - target["settle_ratio"])))
    print("## Height check\n")
    print(f"- Cooked thickness used: {thick:.3f} in (reject below {cook['reject_below_in']} or above {cook['reject_above_in']} in)")
    print(f"- One tower of {total_tower} pancakes ≈ **{est:.1f} in** after settling")
    print(f"- Record to beat: {target['record_height_in']} in. Slow down at {target['slow_down_at_in']} in. STOP at {target['build_to_in']} in")
    print(f"- Pancakes needed to reach the STOP line at this thickness: ~{needed}")

    warnings = []
    if est < target["build_to_in"]:
        warnings.append(f"Tower of {total_tower} only reaches ~{est:.1f} in: add pancakes or check thickness.")
    for z in s["size"]:
        if z["ring_in"] > rules["max_diameter_in"] - 0.5:
            warnings.append(f"{z['name']} ring {z['ring_in']} in leaves < 0.5 in under the max width.")
        if z["ring_in"] < rules["min_diameter_in"] + 0.5:
            warnings.append(f"{z['name']} ring {z['ring_in']} in leaves < 0.5 in above the min width.")
    if thick > rules["max_thickness_in"]:
        warnings.append("Cooked thickness is over the 0.39 in limit.")
    if exp:
        warnings.append(f"Experimental ingredients ON ({', '.join(exp)}): needs written adjudicator approval.")
    if warnings:
        print("\n## Warnings\n")
        for w in warnings:
            print(f"- {w}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
