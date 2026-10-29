"""The page and the drawings are generated. Broken plumbing should fail CI, not ship."""

import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))
import render  # noqa: E402


class PageTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.out = render.outputs()
        cls.html = cls.out[ROOT / "docs/index.html"]

    def test_no_placeholder_left(self):
        self.assertNotIn("{{", self.html)
        self.assertNotIn("}}", re.sub(r"<script[\s\S]*?</script>|<style[\s\S]*?</style>", "", self.html))

    def test_ids_are_unique(self):
        ids = re.findall(r'\sid="([^"]+)"', self.html)
        dupes = sorted({i for i in ids if ids.count(i) > 1})
        self.assertEqual(dupes, [])

    def test_every_href_hash_has_a_target(self):
        ids = set(re.findall(r'\sid="([^"]+)"', self.html))
        for target in re.findall(r'href="#([^"]+)"', self.html):
            self.assertIn(target, ids)

    def test_numbers_come_from_the_spec(self):
        spec = render.load_spec()
        t = spec["target"]
        self.assertIn(f'{t["record_height_in"]}<small>in</small>', self.html)
        self.assertIn(f'value="{render.compute(spec)["thickness_in"]}"', self.html)
        self.assertIn(f'max="{spec["rules"]["max_thickness_in"]}"', self.html)

    def test_inline_tower_is_a_bare_drawing(self):
        tower = self.out[ROOT / "assets/tower.svg"]
        self.assertIn("@font-face", tower)  # the README copy carries its headline font
        bare = render.tower(render.load_spec(), render.compute(render.load_spec()))
        self.assertNotIn("<style", bare)
        self.assertNotIn(' id="', bare)


if __name__ == "__main__":
    unittest.main()
