# pancake-tower

**Flip it till you make it.** The open-source recipe and build protocol behind Pancake's attempt at the tallest stack of pancakes ever built: Oct 29, 2026, San Francisco.

We promised a world record if we hit #1 on Product Hunt. We did. This repo is how we're keeping the promise, in the open.

> **Status: v0.1.0, untested.** These are engineering estimates, not proven numbers yet. They get replaced by measured values after our rehearsal. See [TESTLOG.md](TESTLOG.md).

## The target

| | |
|---|---|
| Height to beat | **42.6 in** (108.3 cm, 230 pancakes) |
| We build to | **45 in**, then hands off |
| Must stand | 5 seconds, freestanding |
| Pancakes in the tower | ~300, in 3 sizes |

## How it works

Most attempts fail on construction, not on taste. So we treat the tower like a structure:

1. **Thin, dense, barely leavened pancakes.** Fluffy pancakes compress unpredictably. We aim for 0.16 in cooked, every time.
2. **Same dose, same ring, every pancake.** Volume is controlled by a portion dispenser, not by eye.
3. **A three-step pyramid.** 9 in at the base, 8 in for the body, 6 in on top. Less load on the bottom layers, more room for placement error.
4. **Nothing touches the tower but pancakes.** No rings, rods, glue or syrup between layers. Height and plumb are read with lasers and a freestanding gauge.
5. **Stop on height, not on count.** Thickness varies; the STOP line doesn't.

## Files

| File | What's in it |
|---|---|
| [`recipe.toml`](recipe.toml) | The spec. Every number lives here |
| [`calc.py`](calc.py) | Turns the spec into a cooking plan, shopping list and height check |
| [`RECIPE.md`](RECIPE.md) | Batter, cooking and quality control |
| [`STACKING.md`](STACKING.md) | Tower geometry, roles and build protocol |
| [`RULES.md`](RULES.md) | The record rules as publicly reported, and what we're confirming |
| [`TESTLOG.md`](TESTLOG.md) | Test runs and the numbers that replace our guesses |

## Quick start

```bash
python3 calc.py                  # one tower + 30% spares
python3 calc.py --attempts 2     # cook for a second attempt
python3 calc.py --thickness 0.15 # re-plan with your measured thickness
```

Python 3.11+, no dependencies.

## Try it yourself

Break our record? Open a PR with your `TESTLOG.md` numbers. Better recipe? `git push --syrup`.

Built by [Pancake](https://pancake.ai), AI agents for go-to-market teams, in Slack.

## License

Code: MIT. Docs and recipe: CC BY 4.0. See [LICENSE](LICENSE).
