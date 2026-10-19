# Contributing

Measured numbers beat theory. The best contributions come with a stack of 10 and a ruler.

- **Every number lives in `recipe.toml`.** Change it there, never in the docs.
- After a change, run:
  ```bash
  python3 calc.py --check            # the spec still follows the rules
  python3 tools/render.py            # redraws assets/*.svg and docs/spec.json
  python3 -m unittest discover tests
  ```
- Log what you measured in `TESTLOG.md`, with the date.
- Built a tower? [Report the attempt](../../issues/new?template=attempt-report.yml).

The Pancake name, logo and mascot aren't open source. Forks replace them.
