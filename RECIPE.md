# Recipe

A pancake built to carry weight, not to win brunch. It's still a real pancake: edible, cooked on both sides, served after the attempt.

This is **v2, our chef's sheet** (Candido Blanco, Oct 28, 2026): the quantities we cook on Oct 29. `python3 calc.py` reproduces the sheet from [`recipe.toml`](recipe.toml).

## One batch

| Ingredient | Amount | % of flour | Why |
|---|---|---|---|
| All-purpose flour | 250 g | 100 | Structure |
| Egg | 1 large | 20 | Binds and sets the crumb |
| Sugar | 3 tsp | 5 | Color and taste |
| Whole milk | 1½ cups | 146 | Thin, pourable batter that levels itself in the ring |
| Water | ½ cup | 47 | Thins the batter without adding fat |

No baking powder, no butter, no oil in the batter. Flat, dense pancakes compress less and more evenly than fluffy ones. Toppings go on after the record, on the plates.

**One batch makes 3 pancakes of 9 in, or 7 pancakes of 7 in.**

## The whole run

| Ring | Target | Extras | To cook | Batches | Batter each |
|---|---|---|---|---|---|
| 9 in (bottom) | 145 | 11 | 156 | 52 | ~1 cup (240 ml) |
| 7 in (top) | 125 | 15 | 140 | 20 | a scant ½ cup (105 ml) |
| **Total** | **270** | | **296** | **72** | |

About 242 pancakes reach the record at ~4.5 mm each in the stack; ~255 reach our 45 in stop line.

| Ingredient | All 72 batches | Buy (+5%) |
|---|---|---|
| All-purpose flour | 18 kg (39.7 lb) | 9 × 5 lb bags |
| Eggs | 72 | 7 dozen (6 dozen leaves no spare) |
| Sugar | 216 tsp (~2 lb) | 2 lb+ |
| Whole milk | 108 cups (6.75 gal) | 8 gal (7 leaves ¼ gal of slack) |
| Water | 36 cups (2.25 gal) | tap, cold |
| Cooking spray | | 6 cans |

## Method

1. **Weigh the flour** for each batch. Whisk egg, milk and water, then whisk into the flour and sugar until just smooth.
2. **Rest ~20 min.** Watch the batter, not the clock: in our tests, thickening came from griddle heat, not resting.
3. **Griddle at 330–350 °F**, checked with a surface thermometer. Spray lightly, wipe the excess. No pooled fat.
4. **Ring on the griddle, one cup in.** ~1 cup for 9 in, a scant ½ cup for 7 in. Same cup every time. Don't spread, don't press.
5. Lift the ring when the edge sets. **Flip once**, when the top looks matte. Pale golden, not brown.
6. **Cool flat on a rack, ~18 min**, one layer. Never stack warm: trapped steam turns into a slippery film between layers.
7. Clean the rings. Sort by size into separate, labeled trays.
8. Stack the 9 in pancakes first, then the 7 in.

## Quality control

- **Stack-of-10 test** on the first 10 of each size, cooled: about 1.8 in for 10. Re-plan with `python3 calc.py --thickness <measured ÷ 10>`.
- Reject at the thickest point above **0.35 in (9 mm)**, domed, wedge-shaped, cracked, raw or dark. Rejects are eaten, never binned.
- Measure diameter on a cooled pancake, before stacking: that's when the rule applies.

## Food safety

- Everything that touches batter is food-grade: rings, cups, ladles. No tape or markers inside rings.
- Keep milk, eggs and batter cold until used.
- **Allergens: wheat, milk, eggs, and soy** (most cooking sprays contain soy lecithin). Post them.
- Nothing goes in the trash: every pancake is eaten or donated.

## Earlier versions

- **v0.1** (Oct 19, never cooked): 0.5% baking powder, 1/8 in of batter per ring, ~4 mm pancakes, 300 in three sizes (9, 8, 6 in).
- **v1** (Oct 25 rehearsal): 25% bread flour, egg whites, 2% baking powder, ~6 mm pancakes, ~215 in three sizes.
- **v2** (Oct 28): the chef's sheet above. Two sizes (9 and 7 in), no leavening.

Texturizers (gluten, xanthan, methylcellulose) are out: the adjudicator asked for standard ingredients.
