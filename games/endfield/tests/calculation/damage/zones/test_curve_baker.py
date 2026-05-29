#!/usr/bin/env python3
"""曲线烘焙与录入脚本共用接缝测试。"""

import unittest

from calculation.core.curve_baker import bake_character_curves, bake_weapon_curves
from calculation.damage.formula import calculate_growth_curve


class TestCurveBaker(unittest.TestCase):
    def test_bake_character_curves_matches_growth_formula(self):
        growth = {"base": 10, "growth": 10, "divisor": 5, "offset": 0}
        baked = bake_character_curves(
            strength=growth,
            agility=growth,
            intellect=growth,
            will=growth,
            base_atk=growth,
            sk1=[],
            sk2=[],
            sk3=[],
        )
        expected = calculate_growth_curve(**growth)
        self.assertEqual(baked["力量"], expected)
        self.assertEqual(len(baked["力量"]), 90)

    def test_bake_weapon_curves_appends_plus_suffix(self):
        growth = {"base": 20, "growth": 20, "divisor": 5, "offset": 0}
        baked = bake_weapon_curves(
            base_atk=growth,
            bonus_attrs={"意志": growth},
        )
        self.assertEqual(baked["基础攻击力"], calculate_growth_curve(**growth))
        self.assertIn("意志+", baked)


if __name__ == "__main__":
    unittest.main()
