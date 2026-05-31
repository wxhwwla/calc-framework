#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""法术异常参数表测试。"""

import unittestfrom games.endfield.calc.manual_buff.spell_params import (    SPELL_ABNORMAL_PARAM_ROWS,    SPELL_BURN_DURATION_SECONDS,    SPELL_BURST_RATIO,    SPELL_CROSS_ANOMALY_INITIAL_RATIO,    SPELL_LEVEL_COEFF_DIVISOR,    base_multiplier_for_formula,    calc_level_from_ui,    preview_level_multipliers,)class TestSpellAbnormalParams(unittest.TestCase):
    def test_param_rows_are_unique_and_complete(self) -> None:
        keys = [row["key"] for row in SPELL_ABNORMAL_PARAM_ROWS]
        self.assertEqual(len(keys), len(set(keys)))
        self.assertEqual(len(keys), 9)
        self.assertIn("灼热异常", keys)
        self.assertIn("灼热爆发", keys)
        self.assertIn("碎冰", keys)

    def test_cross_anomaly_multiplier_at_ui_l0(self) -> None:
        calc_level = calc_level_from_ui(0)
        mult = base_multiplier_for_formula("cross_anomaly", calc_level=calc_level)
        self.assertAlmostEqual(mult, SPELL_CROSS_ANOMALY_INITIAL_RATIO * (1.0 + calc_level))

    def test_burn_includes_ten_second_dot(self) -> None:
        calc_level = calc_level_from_ui(2)
        mult = base_multiplier_for_formula("burn", calc_level=calc_level)
        level_factor = 1.0 + float(calc_level)
        expected = SPELL_CROSS_ANOMALY_INITIAL_RATIO * level_factor + 0.12 * level_factor * float(
            SPELL_BURN_DURATION_SECONDS
        )
        self.assertAlmostEqual(mult, expected)

    def test_shatter_ice_multiplier_scales_with_level(self) -> None:
        calc_level = calc_level_from_ui(3)
        mult = base_multiplier_for_formula("shatter_ice", calc_level=calc_level)
        self.assertAlmostEqual(mult, 1.20 * (1.0 + float(calc_level)))

    def test_burst_is_flat_160_percent(self) -> None:
        for ui_level in range(5):
            calc_level = calc_level_from_ui(ui_level)
            mult = base_multiplier_for_formula("burst", calc_level=calc_level)
            self.assertAlmostEqual(mult, SPELL_BURST_RATIO)

    def test_preview_level_multipliers_has_five_entries(self) -> None:
        coeffs = preview_level_multipliers("cross_anomaly")
        self.assertEqual(len(coeffs), 5)
        self.assertGreater(coeffs[0], 0.0)

    def test_spell_level_coeff_at_90(self) -> None:
        coeff = 1.0 + (90 - 1) / SPELL_LEVEL_COEFF_DIVISOR
        self.assertAlmostEqual(coeff, 1.454, places=3)


if __name__ == "__main__":
    unittest.main()
