#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重构后的反向计算公式单元测试
"""

from typing import cast, Tuple

import unittest
from calculation.inverse import (
    fit_attribute_formula,
    fit_skill_formula,
    fit_skill_formula_no_special,
    fit_formula,
    _is_decimal_data,
    _scale_data,
    _find_best_params,
)


class TestInverseRefactored(unittest.TestCase):
    """测试重构后的反向计算模块"""

    def test_is_decimal_data_integer(self):
        """测试整数数据检测"""
        data = [100, 105, 110, 115]
        self.assertFalse(_is_decimal_data(data))

    def test_is_decimal_data_float(self):
        """测试小数数据检测"""
        data = [3.0, 5.4, 7.8, 10.2]
        self.assertTrue(_is_decimal_data(data))

    def test_scale_data_integer(self):
        """测试整数数据缩放（无缩放）"""
        data = [100, 105, 110]
        scaled, factor = _scale_data(data)
        self.assertEqual(scaled, data)
        self.assertEqual(factor, 1)

    def test_scale_data_float(self):
        """测试小数数据缩放（乘10）"""
        data = [3.0, 5.4, 7.8]
        scaled, factor = _scale_data(data)
        self.assertEqual(scaled, [30, 54, 78])
        self.assertEqual(factor, 10)

    def test_find_best_params_basic(self):
        """测试查找最佳参数"""
        data = [100, 105, 110, 115, 120, 125, 130, 135, 140]
        base = 100
        scaled_base = 100
        scale_factor = 1
        params = _find_best_params(data, base, scaled_base, scale_factor, num_levels=9)
        self.assertIsNotNone(params)
        # 使用类型断言解决类型检查问题
        params = cast(Tuple[int | float, int, int | float], params)
        self.assertEqual(len(params), 3)  # (growth, divisor, offset)

    def test_find_best_params_prefers_smallest_equivalent_tuple(self):
        """多条等价参数时返回 growth、divisor、|offset| 字典序最小的一组"""
        data = [100 + i * 5 for i in range(9)]
        params = _find_best_params(data, 100, 100, 1, num_levels=9)
        self.assertEqual(params, (5, 1, 0))

    def test_fit_attribute_formula_integer(self):
        """测试属性公式拟合（整数数据）"""
        data = [100 + i * 5 for i in range(90)]  # 简单线性增长
        base, growth, divisor, offset = fit_attribute_formula(data)
        self.assertEqual(base, 100)

    def test_fit_attribute_formula_single_offset_interval(self):
        """offset 可行区间退化为单点时仍能反推（floor 公式的常见情况）"""
        data = [
            29, 31, 34, 37, 40, 43, 46, 49, 51, 54, 57, 60, 63, 66, 69, 71, 74, 77, 80, 83,
            86, 89, 91, 94, 97, 100, 103, 106, 109, 111, 114, 117, 120, 123, 126, 129, 132,
            134, 137, 140, 143, 146, 149, 152, 154, 157, 160, 163, 166, 169, 172, 174, 177,
            180, 183, 186, 189, 192, 194, 197, 200, 203, 206, 209, 212, 214, 217, 220, 223,
            226, 229, 232, 234, 237, 240, 243, 246, 249, 252, 254, 257, 260, 263, 266, 269,
            272, 274, 277, 280, 283,
        ]
        from calculation.formula import calculate_growth_curve

        base, growth, divisor, offset = fit_attribute_formula(data)
        self.assertEqual(base, 29)
        self.assertEqual((growth, divisor, offset), (163, 57, 3))
        calc = calculate_growth_curve(base, growth, divisor, offset)
        self.assertEqual(calc, data)

    def test_fit_skill_formula_no_special_integer(self):
        """测试技能公式拟合（整数数据，无特殊值）"""
        data = [100 + i * 10 for i in range(9)]
        base, growth, divisor, offset, special = fit_skill_formula_no_special(data)
        self.assertEqual(base, 100)
        self.assertEqual(special, [])

    def test_fit_weapon_bonus_matches_seed_params(self):
        """武器附加属性（9级+第9级special）反推结果应能复现 JSON/seed 曲线"""
        import io
        import contextlib

        from calculation.formula import calculate_bonus_attribute

        cases = [
            (
                [10, 18, 26, 34, 42, 51, 59, 67, 79],
                {"base": 10, "growth": 41, "divisor": 5, "offset": 0, "special": [79]},
            ),
            (
                [12, 14, 17, 19, 22, 24, 26, 29, 34],
                {"base": 12, "growth": 12, "divisor": 5, "offset": 2, "special": [34]},
            ),
        ]
        for curve, seed in cases:
            with contextlib.redirect_stdout(io.StringIO()):
                base, growth, divisor, offset, special = fit_skill_formula_no_special(curve)
            self.assertEqual(special, seed["special"])
            self.assertEqual(
                (base, growth, divisor, offset),
                (seed["base"], seed["growth"], seed["divisor"], seed["offset"]),
            )
            self.assertIsInstance(growth, int)
            self.assertIsInstance(offset, int)
            rebuilt = calculate_bonus_attribute(
                base, growth, divisor, offset, special=special, is_decimal=False
            )
            self.assertEqual(rebuilt, curve)

    def test_fit_skill_formula_no_special_float(self):
        """测试技能公式拟合（小数数据）"""
        data = [3.0, 5.4, 7.8, 10.2, 12.6, 15.0, 17.4, 19.8, 23.4]
        base, growth, divisor, offset, special = fit_skill_formula_no_special(data)
        self.assertEqual(base, 3.0)
        self.assertEqual(special, [23.4])

    def test_fit_formula_auto_detect(self):
        """测试自动检测数据类型并拟合公式"""
        # 测试整数数据（9个元素）
        int_data = [100 + i * 5 for i in range(9)]
        base, growth, divisor, offset, special = fit_formula(int_data)
        self.assertEqual(base, 100)
        
        # 测试小数数据
        float_data = [3.0, 5.4, 7.8, 10.2, 12.6, 15.0, 17.4, 19.8, 23.4]
        base, growth, divisor, offset, special = fit_formula(float_data)
        self.assertEqual(base, 3.0)


if __name__ == "__main__":
    unittest.main()
