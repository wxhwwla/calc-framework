#!/usr/bin/env python3
"""
计算模块单元测试
"""

import unittest

from calculation.damage.formula import calculate_bonus_attribute, calculate_growth_curve, calculate_skill_curve
from calculation.damage.inverse import (
    fit_attribute_formula,
    fit_formula,
    fit_skill_formula,
    fit_skill_formula_no_special,
    remove_duplicates,
    validate_formula,
)


class TestFormulaCalculations(unittest.TestCase):
    """测试公式计算函数"""

    def test_calculate_growth_curve_integer(self):
        """测试整数参数的成长曲线计算"""
        result = calculate_growth_curve(100, 50, 10)
        self.assertEqual(len(result), 90)
        self.assertEqual(result[0], 100)
        self.assertEqual(result[-1], 545)

    def test_calculate_growth_curve_decimal(self):
        """测试小数参数的成长曲线计算"""
        result = calculate_growth_curve(8.9, 6.2, 10)
        self.assertEqual(len(result), 90)
        self.assertEqual(result[0], 8.9)
        self.assertAlmostEqual(result[1], 8.9)
        self.assertAlmostEqual(result[2], 9.9)

    def test_calculate_growth_curve_custom_max_level(self):
        """测试自定义最大等级"""
        result = calculate_growth_curve(100, 50, 10, max_level=10)
        self.assertEqual(len(result), 10)

    def test_calculate_growth_curve_invalid_divisor(self):
        """测试无效除数（负数或零）"""
        with self.assertRaises(ValueError):
            calculate_growth_curve(100, 50, 0)
        with self.assertRaises(ValueError):
            calculate_growth_curve(100, 50, -1)

    def test_calculate_skill_curve_with_special(self):
        """测试带特殊值的技能倍率计算"""
        result = calculate_skill_curve(100, 20, 10, special_values=[150, 160, 170])
        self.assertEqual(len(result), 12)
        self.assertEqual(result[:9], [100, 102, 104, 106, 108, 110, 112, 114, 116])
        self.assertEqual(result[9:], [150, 160, 170])

    def test_calculate_skill_curve_without_special(self):
        """测试不带特殊值的技能倍率计算"""
        result = calculate_skill_curve(100, 20, 10)
        self.assertEqual(len(result), 12)
        # 验证结果是数值类型（int或float）
        self.assertIsInstance(result[0], (int, float))

    def test_calculate_bonus_attribute(self):
        """测试附加属性计算"""
        result = calculate_bonus_attribute(10, 5, 10)
        self.assertEqual(len(result), 9)

    def test_calculate_bonus_attribute_with_special(self):
        """测试带特殊值的附加属性计算"""
        result = calculate_bonus_attribute(10, 5, 10, special=[79])
        self.assertEqual(len(result), 9)
        self.assertEqual(result[-1], 79)


class TestInverseCalculations(unittest.TestCase):
    """测试反向推导函数"""

    def test_remove_duplicates(self):
        """测试移除重复数据"""
        data = list(range(94))
        result = remove_duplicates(data)
        self.assertEqual(len(result), 90)
        # 验证移除了正确的索引
        self.assertNotIn(20, [i for i, val in enumerate(data) if val in result])

    def test_fit_attribute_formula(self):
        """测试属性公式拟合"""
        data = [100 + i * 2 for i in range(90)]
        base, growth, divisor, offset = fit_attribute_formula(data)
        self.assertEqual(base, 100)
        self.assertEqual(offset, 0)
        self.assertAlmostEqual(growth / divisor, 2.0, places=5)

    def test_validate_attribute_formula(self):
        """测试属性公式验证"""
        data = [100 + i * 2 for i in range(90)]
        result = validate_formula(100, 2, 1, 0, data)
        self.assertTrue(result)

    def test_fit_skill_formula(self):
        """测试技能倍率公式拟合（12级）"""
        data = [100 + i * 2 for i in range(9)] + [150, 160, 170]
        base, growth, divisor, offset, special = fit_skill_formula(data)
        self.assertEqual(base, 100)
        self.assertEqual(special, [150, 160, 170])

    def test_fit_skill_formula_no_special(self):
        """测试技能倍率公式拟合（9级）"""
        data = [100 + i * 2 for i in range(9)]
        base, growth, divisor, offset, special = fit_skill_formula_no_special(data)
        self.assertEqual(base, 100)

    def test_validate_skill_formula(self):
        """测试技能公式验证"""
        data = [100 + i * 2 for i in range(9)] + [150, 160, 170]
        result = validate_formula(100, 2, 1, 0, data, [150, 160, 170])
        self.assertTrue(result)

    def test_fit_formula_auto_detect(self):
        """测试统一拟合接口自动检测"""
        # 测试90个数据（属性）
        attr_data = [100 + i * 2 for i in range(90)]
        base, growth, divisor, offset, special = fit_formula(attr_data)
        self.assertIsNone(special)

        # 测试12个数据（技能）
        skill_data = [100 + i * 2 for i in range(9)] + [150, 160, 170]
        base, growth, divisor, offset, special = fit_formula(skill_data)
        self.assertIsNotNone(special)


if __name__ == "__main__":
    unittest.main()
