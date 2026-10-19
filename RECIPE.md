# Recipe

A pancake built to carry weight, not to win brunch. It's still a real pancake: edible, cooked on both sides, served after the attempt.

Quantities for the whole run come from `python3 calc.py`. The ratios below are the recipe.

## Batter (baker's percentages, flour = 100)

| Ingredient | % | Why |
|---|---|---|
| All-purpose flour | 100 | Structure |
| Whole milk | 120 | Thin, pourable batter that levels itself in the ring |
| Whole eggs | 25 | Binds and sets the crumb so it doesn't crush |
| Sugar | 4 | Color and taste, kept low so it doesn't stick or get soft |
| Salt | 1.5 | Taste |
| Baking powder | 0.5 | Barely any lift: fluffy pancakes compress unpredictably |
| Neutral oil | 2 | Just enough to release; fat between layers makes them slide |

No butter in the batter. Toppings go on after the record, on the plates.

## Method

1. Whisk the dry ingredients. Whisk eggs, milk and oil. Combine until just smooth.
2. **Rest 60 min, covered**, cold. The flour hydrates and the thickness gets more consistent.
3. Griddle at **330–350 °F**, wiped once with oil. No pooled fat.
4. Ring on the griddle. **Dispense the fixed dose** for that ring (see table). Don't spread, don't press.
5. Lift the ring when the edge sets. Flip **once**, when the top looks matte. Pale golden, not brown.
6. **Cool flat on a rack, 5 min.** Trapped steam turns into a slippery film between layers.
7. Sort by size into separate, labeled boxes.

## Doses

One assumption drives every dose: **1/8 in of raw batter in the ring.** A fixed volume on a fixed area gives a fixed depth.

| Ring | Dose | ≈ Weight |
|---|---|---|
| 9 in | 4.4 fl oz (130 ml) | 5.1 oz (143 g) |
| 8 in | 3.5 fl oz (103 ml) | 4.0 oz (113 g) |
| 6 in | 2.0 fl oz (58 ml), a 1/4 cup | 2.2 oz (64 g) |

Use one portion scoop or a piston batter dispenser per size, set once and locked. Optional check: a line scribed inside the ring at 1/8 in.

## Quality control

- **The stack-of-10 test.** Every ~30 pancakes per station, stack 10 cooled ones and measure. Target **1.6 in**, accept **1.45–1.75 in**.
- Too low? Raise the dose ~10%. Don't change the recipe or the temperature mid-run.
- Spot-check single pancakes with calipers: reject below **0.13 in** or above **0.18 in**.
- Measure diameter on a cooled pancake, not straight out of the ring.

## Food safety

- Everything that touches batter is food-grade stainless: rings, scoops, dispensers. No tape or markers inside rings.
- Batter and cooked pancakes held at **≤ 41 °F**. Bring the tower stock to **60–68 °F** about 60–90 min before stacking.
- Allergens: wheat, milk, eggs. Post them.
- Nothing goes in the trash: every pancake is eaten or donated.

## Experimental (off by default)

Texturizers mixed into the batter, not between layers. Only with **written adjudicator approval** and an allergen check:

| Additive | Dose (% of flour) | Expected effect |
|---|---|---|
| Vital wheat gluten | 2–3 | Stiffer crumb, less creep |
| Xanthan gum | 0.1–0.2 | More consistent thickness |
| Methylcellulose | 0.3–0.5 | Sets with heat, resists compression |

Switch them on in `recipe.toml` under `[experimental]`; `calc.py` will flag it.
