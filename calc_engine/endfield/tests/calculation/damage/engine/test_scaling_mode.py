#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""整数 / 小数取整模式：行为规格测试。"""

import contextlib
import io
import unittest

from calc_engine.endfield.calc.damage.formula import (
    calculate_bonus_attribute,
    calculate_skill_curve,
    has_fractional_part,
    infer_decimal_mode,
)
from calc_engine.endfield.calc.damage.inverse import _is_decimal_data, fit_skill_formula_no_special


class TestScalingMode(unittest.TestCase):
    """输入为真小数时 ×10 取整；纯整数（含 10.0）时直接 floor。"""

    def test_has_fractional_part(self):
        self.assertFalse(has_fractional_part(10))
        self.assertFalse(has_fractional_part(10.0))
        self.assertTrue(has_fractional_part(5.4))
        self.assertTrue(has_fractional_part(23.4))

    def test_infer_decimal_mode_from_special_only(self):
        """seed 荧光雷羽：base 为 int，special 含 23.4 仍走小数模式"""
        self.assertTrue(infer_decimal_mode(3, 12, 5, 0, special=[23.4]))

    def test_integer_params_use_direct_floor(self):
        expected = [10.0, 18.0, 26.0, 34.0, 42.0, 51.0, 59.0, 67.0, 79]
        self.assertEqual(
            calculate_bonus_attribute(10, 41, 5, 0, special=[79]),
            expected,
        )

    def test_whole_number_float_params_match_integer_floor(self):
        """反推若误返回 41.0，也不应触发 ×10"""
        int_curve = calculate_bonus_attribute(10, 41, 5, 0, special=[79])
        float_whole = calculate_bonus_attribute(10.0, 41.0, 5.0, 0.0, special=[79.0])
        self.assertEqual(float_whole, int_curve)

    def test_true_decimal_params_use_scale_by_10(self):
        self.assertEqual(
            calculate_bonus_attribute(3.0, 12, 5, 0, is_decimal=True, max_level=5),
            [3.0, 5.4, 7.8, 10.2, 12.6],
        )

    def test_decimal_input_data_detection(self):
        self.assertFalse(_is_decimal_data([10, 18, 26]))
        self.assertTrue(_is_decimal_data([3.0, 5.4, 7.8]))

    def test_fit_integer_weapon_bonus_rebuilds_with_integer_floor(self):
        from calc_engine.endfield.calc.damage.formula import calculate_bonus_attribute

        curve = [12, 14, 17, 19, 22, 24, 26, 29, 34]
        with contextlib.redirect_stdout(io.StringIO()):
            base, growth, divisor, offset, special = fit_skill_formula_no_special(curve)
        rebuilt = calculate_bonus_attribute(base, growth, divisor, offset, special=special, is_decimal=False)
        self.assertEqual(rebuilt, curve)

    def test_fit_decimal_curve_rebuilds_with_decimal_floor(self):
        data = [3.0, 5.4, 7.8, 10.2, 12.6, 15.0, 17.4, 19.8, 23.4]
        with contextlib.redirect_stdout(io.StringIO()):
            base, growth, divisor, offset, special = fit_skill_formula_no_special(data)
        rebuilt = calculate_bonus_attribute(base, growth, divisor, offset, special=special, is_decimal=True)
        self.assertEqual(rebuilt, data)

    def test_skill_curve_decimal_via_special(self):
        result = calculate_skill_curve(3, 12, 5, 0, special_values=[23.4, 24, 25])
        self.assertEqual(result[0], 3.0)
        self.assertEqual(result[1], 5.4)


if __name__ == "__main__":
    unittest.main()
