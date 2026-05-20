#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重构后的反向计算公式单元测试
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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
    """测试重构后的反向计算公式"""

    def test_is_decimal_data_integer(self):
        """测试判断整数数据"""
        data = [100, 105, 110, 115]
        self.assertFalse(_is_decimal_data(data))

    def test_is_decimal_data_float(self):
        """测试判断小数数据"""
        data = [3.0, 5.4, 7.8, 10.2]
        self.assertTrue(_is_decimal_data(data))

    def test_scale_data_integer(self):
        """测试整数数据缩放（不缩放）"""
        data = [100, 105, 110]
        scaled, scale_factor = _scale_data(data)
        self.assertEqual(scale_factor, 1)
        self.assertEqual(scaled, data)

    def test_scale_data_float(self):
        """测试小数数据缩放（乘10）"""
        data = [3.0, 5.4, 7.8]
        scaled, scale_factor = _scale_data(data)
        self.assertEqual(scale_factor, 10)
        self.assertEqual(scaled, [30, 54, 78])

    def test_find_best_params_basic(self):
        """测试查找最佳参数"""
        data = [100, 105, 110, 115, 120, 125, 130, 135, 140]
        base = 100
        scaled_base = 100
        scale_factor = 1
        params = _find_best_params(data, base, scaled_base, scale_factor, num_levels=9)
        self.assertIsNotNone(params)
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
        """测试统一拟合接口自动检测"""
        # 90个数据点 - 属性
        attr_data = [100 + i * 2 for i in range(90)]
        result = fit_formula(attr_data)
        self.assertEqual(len(result), 5)
        
        # 12个数据点 - 技能
        skill_data = [100 + i * 5 for i in range(12)]
        result = fit_formula(skill_data)
        self.assertEqual(len(result), 5)
        
        # 9个数据点 - 技能（无特殊值）
        skill_short_data = [100 + i * 5 for i in range(9)]
        result = fit_formula(skill_short_data)
        self.assertEqual(len(result), 5)


if __name__ == '__main__':
    unittest.main()