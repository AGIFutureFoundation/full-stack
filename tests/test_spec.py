"""The spec has to stay inside the record rules. If a change breaks one, CI goes red."""

import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from calc import compute, load_spec  # noqa: E402


class SpecTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec = load_spec()
        cls.plan = compute(cls.spec)

    def test_rings_inside_width_limits_with_margin(self):
        r = self.spec["rules"]
        for z in self.spec["size"]:
            self.assertLessEqual(z["ring_in"], r["max_diameter_in"] - 0.5, z["name"])
            self.assertGreaterEqual(z["ring_in"], r["min_diameter_in"] + 0.5, z["name"])

    def test_pyramid_never_widens_going_up(self):
        rings = [z["ring_in"] for z in self.spec["size"]]
        self.assertEqual(rings, sorted(rings, reverse=True))

    def test_thickness_under_limit(self):
        c = self.spec["cook"]
        self.assertLess(c["reject_above_in"], self.spec["rules"]["max_thickness_in"])
        self.assertLess(c["reject_below_in"], c["target_cooked_thickness_in"])
        self.assertLess(c["target_cooked_thickness_in"], c["reject_above_in"])

    def test_tower_reaches_stop_line(self):
        self.assertGreaterEqual(self.plan["height_in"], self.spec["target"]["build_to_in"])

    def test_stop_line_beats_record(self):
        t = self.spec["target"]
        self.assertGreater(t["build_to_in"], t["record_height_in"])
        self.assertGreater(t["slow_down_at_in"], t["record_height_in"])
        self.assertGreater(t["build_to_in"], t["slow_down_at_in"])

    def test_whole_batches_only(self):
        for z in self.plan["sizes"]:
            self.assertEqual(z["to_cook"], z["batches"] * z["per_batch"], z["name"])

    def test_matches_chef_sheet(self):
        """The chef's sheet of Oct 28: 156 x 9 in + 140 x 7 in, 72 batches."""
        cooked = {z["ring_in"]: z["to_cook"] for z in self.plan["sizes"]}
        self.assertEqual(cooked, {9: 156, 7: 140})
        totals = {s["key"]: s["total"] for s in self.plan["shopping"]}
        self.assertEqual(self.plan["batches"], 72)
        self.assertEqual(totals["flour_all_purpose"], 18000)
        self.assertEqual(totals["eggs"], 72)
        self.assertEqual(totals["sugar"], 216)
        self.assertEqual(totals["whole_milk"], 108)
        self.assertEqual(totals["water"], 36)

    def test_dose_under_thickness_limit(self):
        limit_mm = self.spec["rules"]["max_thickness_in"] * 25.4
        for z in self.plan["sizes"]:
            self.assertLess(z["raw_depth_mm"], limit_mm, z["name"])

    def test_spares_cover_the_tower(self):
        for z in self.plan["sizes"]:
            self.assertGreater(z["to_cook"], z["in_tower"])

    def test_experimental_off_by_default(self):
        self.assertFalse(any(self.spec.get("experimental", {}).values()))


if __name__ == "__main__":
    unittest.main()
