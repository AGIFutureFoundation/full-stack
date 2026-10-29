#!/usr/bin/env python3
"""Pancake Tower calculator.

Reads recipe.toml and prints the cooking plan, the shopping list and the
height check. Python 3.11+, no dependencies.

    python3 calc.py                      # plan for one attempt
    python3 calc.py --attempts 2         # enough pancakes for a second try
    python3 calc.py --thickness 0.17     # re-plan with your measured thickness
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
ML_PER_CUP = 236.588
ML_PER_GALLON = 3785.41
CUPS_PER_GALLON = 16
G_PER_OZ = 28.3495
G_PER_LB = 453.592
CM2_PER_IN2 = 6.4516
# grams in one unit of an ingredient, for the units a cook measures with
G_PER_UNIT = {
    ("sugar", "tsp"): 4.2,
    ("salt", "tsp"): 6.0,
    ("baking_powder", "tsp"): 4.6,
    ("whole_milk", "cup"): ML_PER_CUP * 1.03,
    ("water", "cup"): ML_PER_CUP,
    ("neutral_oil", "tbsp"): 13.6,
}


def load_spec(path: Path = ROOT / "recipe.toml") -> dict:
    with path.open("rb") as f:
        return tomllib.load(f)


def grams(spec: dict, ing: dict) -> float:
    """Weight of one batch's worth of an ingredient."""
    unit = ing["unit"]
    if unit == "g":
        return ing["amount"]
    if unit == "egg":
        return ing["amount"] * spec["cook"]["egg_weight_g"]
    return ing["amount"] * G_PER_UNIT[(ing["key"], unit)]


def buy(key: str, total: float, unit: str, g: float, margin: float, bag_lb: float) -> str:
    """What to put in the cart: the batch total plus the margin, in store units."""
    need = total * (1 + margin)
    if key == "water":
        return "tap water"
    if unit == "egg":
        return f"{math.ceil(need / 12)} dozen"
    if key == "whole_milk":
        return f"{math.ceil(need / CUPS_PER_GALLON)} gal"
    if key.startswith("flour"):
        return f"{math.ceil(g * (1 + margin) / G_PER_LB / bag_lb)} × {bag_lb:g} lb bags"
    return lb_oz(g * (1 + margin))


def compute(spec: dict, attempts: int = 1, spare: float | None = None, thickness: float | None = None) -> dict:
    """Every derived number, in one place. The page and the drawings read this.

    The batter is counted in whole batches of the chef's base batch: each size says how
    many pancakes one batch makes, so the doses and the shopping list follow from it.
    """
    cook, batter, target, rules = spec["cook"], spec["batter"], spec["target"], spec["rules"]
    spare = cook["spare_ratio"] if spare is None else spare
    thick = cook["target_cooked_thickness_in"] if thickness is None else thickness
    dens = batter["density_g_per_ml"]
    settled = thick * (1 - target["settle_ratio"])
    ings = batter["ingredient"]
    batch_g = sum(grams(spec, i) for i in ings)
    batch_ml = batch_g / dens

    sizes, total_ml, total_cook, total_tower, batches = [], 0.0, 0, 0, 0
    for z in spec["size"]:
        ml = batch_ml / z["per_batch"]
        n_batches = math.ceil(math.ceil(z["in_tower"] * attempts * (1 + spare)) / z["per_batch"])
        n_cook = n_batches * z["per_batch"]
        area_cm2 = math.pi * (z["ring_in"] / 2) ** 2 * CM2_PER_IN2
        sizes.append({
            "name": z["name"],
            "ring_in": z["ring_in"],
            "in_tower": z["in_tower"],
            "per_batch": z["per_batch"],
            "batches": n_batches,
            "to_cook": n_cook,
            "dose_ml": round(ml, 1),
            "dose_fl_oz": round(ml / ML_PER_FL_OZ, 2),
            "dose_cups": round(ml / ML_PER_CUP, 2),
            "dose_g": round(ml * dens, 1),
            "raw_depth_mm": round(ml / area_cm2 * 10, 1),
            "tier_height_in": round(z["in_tower"] * settled, 2),
        })
        total_ml += ml * n_cook
        total_cook += n_cook
        total_tower += z["in_tower"]
        batches += n_batches

    flour_g = sum(grams(spec, i) for i in ings if i["key"].startswith("flour"))
    shop_cfg = spec.get("shopping", {})
    margin, bag_lb = shop_cfg.get("margin", 0.0), shop_cfg.get("flour_bag_lb", 5)
    shopping = []
    for i in ings:
        g1 = grams(spec, i)
        total = i["amount"] * batches
        g = g1 * batches
        item = {"key": i["key"], "why": i.get("why", ""), "per_batch": i["amount"], "unit": i["unit"],
                "total": round(total, 2), "pct": round(g1 / flour_g * 100, 1), "g": round(g)}
        if i["unit"] == "cup":
            item["gal"] = round(total / CUPS_PER_GALLON, 2)
            item["l"] = round(total * ML_PER_CUP / 1000, 1)
        if i["unit"] == "egg":
            item["count"] = math.ceil(total)
        item["buy"] = buy(i["key"], total, i["unit"], g, margin, bag_lb)
        shopping.append(item)
    if cook.get("spray_cans"):
        shopping.append({"key": "cooking_spray", "why": "Griddle and rings", "per_batch": None, "unit": "can",
                         "total": cook["spray_cans"], "pct": None, "g": None, "buy": f"{cook['spray_cans']} cans"})

    exp = {k: v for k, v in spec.get("experimental", {}).items() if v}
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
        warnings.append(f"Experimental ingredients ON ({', '.join(exp)}): not allowed, standard ingredients only.")

    return {
        "attempts": attempts,
        "spare_ratio": spare,
        "thickness_in": thick,
        "sizes": sizes,
        "batches": batches,
        "batch_g": round(batch_g),
        "batch_ml": round(batch_ml),
        "pancakes_in_tower": total_tower,
        "pancakes_to_cook": total_cook,
        "batter_l": round(total_ml / 1000, 1),
        "batter_gal": round(total_ml / ML_PER_GALLON, 1),
        "batter_kg": round(total_ml * dens / 1000, 1),
        "shopping": shopping,
        "height_in": round(height, 1),
        "pancakes_to_stop_line": math.ceil(target["build_to_in"] / settled),
        "pancakes_to_record": math.ceil(target["record_height_in"] / settled),
        "warnings": warnings,
    }


def lb_oz(grams: float) -> str:
    total_oz = grams / G_PER_OZ
    if total_oz < 16:
        return f"{total_oz:.1f} oz"
    lb, oz = divmod(round(total_oz), 16)
    return f"{lb} lb {oz} oz" if oz else f"{lb} lb"


def fmt_amount(x: float, unit: str) -> str:
    x = round(x, 2)
    n = f"{x:g}"
    if unit == "g":
        return f"{x / 1000:g} kg" if x >= 1000 else f"{n} g"
    if unit == "egg":
        return f"{n} egg" + ("s" if x > 1 else "")
    if unit == "cup":
        return f"{n} cup" + ("s" if x > 1 else "")
    return f"{n} {unit}"


def report(spec: dict, plan: dict) -> str:
    t, cook, meta = spec["target"], spec["cook"], spec["meta"]
    out = [f"# Pancake Tower plan — spec v{meta['version']} ({meta['status']})\n"]
    if meta["status"] != "validated":
        out.append(f"> Source: {meta.get('source', 'estimates')}. Validate the thickness with the stack-of-10 and log it in TESTLOG.md.\n")
    out += ["## What to cook\n",
            "| Size | Ring | In tower | Per batch | Batches | To cook | Batter per pancake | Raw depth |",
            "|---|---|---|---|---|---|---|---|"]
    for z in plan["sizes"]:
        out.append(f"| {z['name']} | {z['ring_in']} in | {z['in_tower'] * plan['attempts']} | {z['per_batch']} | {z['batches']} | "
                   f"{z['to_cook']} | {z['dose_cups']:.2f} cup ({z['dose_ml']:.0f} ml) | {z['raw_depth_mm']} mm |")
    out.append(f"| **total** | | **{plan['pancakes_in_tower'] * plan['attempts']}** | | **{plan['batches']}** | "
               f"**{plan['pancakes_to_cook']}** | | |\n")

    out += ["## Shopping list\n",
            f"{plan['batches']} batches of ~{plan['batch_ml']} ml: {plan['batter_l']} L ({plan['batter_gal']} gal) of batter. "
            f"Rest {spec['batter']['rest_minutes']} min. Buy list includes a {spec.get('shopping', {}).get('margin', 0):.0%} margin.\n",
            "| Ingredient | One batch | All batches | Buy |", "|---|---|---|---|"]
    for s in plan["shopping"]:
        name = s["key"].replace("_", " ")
        one = fmt_amount(s["per_batch"], s["unit"]) if s["per_batch"] is not None else ""
        if s["unit"] == "cup":
            allb = f"{s['total']:g} cups ({s['gal']:g} gal)"
        elif s["unit"] == "g":
            allb = f"{fmt_amount(s['total'], 'g')} ({s['g'] / G_PER_LB:.1f} lb)"
        elif s["unit"] == "can":
            allb = f"{s['total']} cans"
        else:
            allb = fmt_amount(s["total"], s["unit"]) + (f" ({lb_oz(s['g'])})" if s["unit"] == "tsp" else "")
        out.append(f"| {name} | {one} | {allb} | {s['buy']} |")

    out += ["\n## Height check\n",
            f"- Cooked thickness used: {plan['thickness_in']:.3f} in "
            f"(reject below {cook['reject_below_in']} or above {cook['reject_above_in']} in)",
            f"- One tower of {plan['pancakes_in_tower']} pancakes ≈ **{plan['height_in']} in** after settling",
            f"- Record to beat: {t['record_height_in']} in. Slow down at {t['slow_down_at_in']} in. STOP at {t['build_to_in']} in",
            f"- Pancakes needed at this thickness: ~{plan['pancakes_to_record']} to pass the record, "
            f"~{plan['pancakes_to_stop_line']} to the STOP line"]
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
