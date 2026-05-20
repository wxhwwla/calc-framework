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

    def test_fit_attribute_formula_integer(self):
        """测试属性公式拟合（整数数据）"""
        data = [100 + i * 5 for i in range(90)]  # 简单线性增长
        base, growth, divisor, offset = fit_attribute_formula(data)
        self.assertEqual(base, 100)

    def test_fit_skill_formula_no_special_integer(self):
        """测试技能公式拟合（整数数据，无特殊值）"""
        data = [100 + i * 10 for i in range(9)]
        base, growth, divisor, offset, special = fit_skill_formula_no_special(data)
        self.assertEqual(base, 100)
        self.assertEqual(special, [])

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
