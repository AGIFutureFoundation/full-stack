# Test log

Every guess in `recipe.toml` gets replaced by a number measured here. When the rehearsal confirms the spec, set `status = "validated"`.

## What we measure

| Measure | How | Target |
|---|---|---|
| Cooked thickness | Stack of 10 cooled pancakes ÷ 10, per size | ~0.18 in (4.5 mm) |
| Thickness spread | Calipers on 10 single pancakes | 0.12–0.35 in |
| Diameter after settling | Calipers on the 3 bottom pancakes, 10 min after building | < 9.5 in on a 9 in ring |
| Settling | Tower height at t0 and t+10 min | ≤ 5% |
| Lean | Laser offset every 20 layers | < 1/8 in per 20 layers |
| Tap test | Same tap on the table, watch the tower | No visible sway |
| Batter density | Weigh 1 cup | Update `density_g_per_ml` |

## Bench test: 3 columns of 60 pancakes, 8 in

| Variant | Change | Thickness (in) | Settling 10 min | Lean | Notes |
|---|---|---|---|---|---|
| A | Spec as written | | | | |
| B | No baking powder | | | | |
| C | 15% bread flour | | | | |

Then on the winner: stack at warm (~105 °F), room temp and fridge-cold. Same measures.

**Decision:** _variant ___ at ___ °F, because ___._

## Rehearsal (full height)

| Date | Pancakes | Height at t0 | Height at t+10 min | Bottom diameter | 5 s hold | Notes |
|---|---|---|---|---|---|---|
| | | | | | | |

## Changes to the spec

| Date | Field | Old | New | Why |
|---|---|---|---|---|
| Oct 25 | batter | v0.1 (0.5% baking powder, ~4 mm) | v1 (25% bread flour, egg whites, 2% baking powder, ~6 mm) | Rehearsal recipe. Fewer, thicker pancakes. Not committed here at the time |
| Oct 28 | whole spec | v1, rings 9/8/6 in | v2.0.0, the chef's sheet: rings 9/7 in, batch of 250 g flour, 1 egg, 3 tsp sugar, 1½ cups milk, ½ cup water | Chef's plan for Oct 29: 145 × 9 in + 125 × 7 in, ~4.5 mm each, 242 to pass the record |
| Oct 28 | grease | wiped oil | cooking spray (6 cans) | Chef's choice. Adds soy to the allergen list |
