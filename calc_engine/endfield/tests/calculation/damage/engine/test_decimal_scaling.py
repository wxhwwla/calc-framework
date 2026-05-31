#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""
测试小数乘10处理逻辑

数据处理规则：
1. 整数数据：直接按公式计算
2. 小数数据：乘10→整数计算→除10
3. 百分比数据：移除%→按整数/小数处理
"""

from calc_engine.endfield.calc.damage.formula import (
    calculate_bonus_attribute,
    calculate_growth_curve,
    calculate_skill_curve,
)
from calc_engine.endfield.calc.damage.inverse import fit_skill_formula_no_special
from scripts.inverse_cli import parse_percent


def test_integer_data_direct_calculation():
    """测试整数数据直接计算"""
    # 整数数据：base=34, growth=31, divisor=9, offset=8
    result = calculate_growth_curve(34, 31, 9, 8, max_level=5)
    # 计算: 34 + floor((31*(lv-1) + 8)/9)
    # lv=1: 34 + floor(8/9) = 34
    # lv=2: 34 + floor(39/9) = 38
    # lv=3: 34 + floor(70/9) = 41
    # lv=4: 34 + floor(101/9) = 45
    # lv=5: 34 + floor(132/9) = 48
    expected = [34.0, 38.0, 41.0, 45.0, 48.0]
    assert result == expected, f"整数计算失败: {result} != {expected}"
    print("✓ 整数数据直接计算测试通过")


def test_decimal_data_scale_by_10():
    """测试小数数据乘10处理"""
    # 小数数据：base=3.0, growth=12, divisor=5, offset=0
    # 期望：3.0, 5.4, 7.8, 10.2, 12.6
    result = calculate_bonus_attribute(3.0, 12, 5, 0, max_level=5, is_decimal=True)
    expected = [3.0, 5.4, 7.8, 10.2, 12.6]
    assert result == expected, f"小数乘10计算失败: {result} != {expected}"
    print("✓ 小数数据乘10处理测试通过")


def test_decimal_data_with_special_value():
    """测试小数数据带特殊值"""
    # 荧光雷羽攻击力+数据
    result = calculate_bonus_attribute(3.0, 12, 5, 0, special=[23.4], max_level=9)
    expected = [3.0, 5.4, 7.8, 10.2, 12.6, 15.0, 17.4, 19.8, 23.4]
    assert result == expected, f"小数数据带特殊值失败: {result} != {expected}"
    print("✓ 小数数据带特殊值测试通过")


def test_percent_integer_parsing():
    """测试整数百分比解析"""
    value = "89%"
    result, is_decimal = parse_percent(value)
    assert result == 89, f"整数百分比解析失败: {result} != 89"
    assert is_decimal is False, "整数百分比类型判断失败"
    print("✓ 整数百分比解析测试通过")


def test_percent_decimal_parsing():
    """测试小数百分比解析"""
    value = "8.9%"
    result, is_decimal = parse_percent(value)
    # 小数百分比应该乘10
    assert result == 89, f"小数百分比解析失败: {result} != 89"
    assert is_decimal is True, "小数百分比类型判断失败"
    print("✓ 小数百分比解析测试通过")


def test_inverse_formula_decimal_fitting():
    """测试小数数据反推公式"""
    data = [3.0, 5.4, 7.8, 10.2, 12.6, 15.0, 17.4, 19.8, 23.4]
    base, growth, divisor, offset, special = fit_skill_formula_no_special(data)

    assert base == 3.0, f"base错误: {base} != 3.0"
    # 该数据无法用单一公式拟合，第9级作为special值
    assert special == [23.4], f"special错误: {special} != [23.4]"

    result = calculate_bonus_attribute(base, growth, divisor, offset, special, max_level=9, is_decimal=True)
    assert result == data, f"反推参数计算结果不匹配: {result} != {data}"
    print(f"✓ 小数数据反推公式测试通过 (参数: base={base}, growth={growth}, divisor={divisor}, offset={offset})")


def test_skill_curve_with_decimal():
    """测试技能曲线计算（小数数据）"""
    result = calculate_skill_curve(3.0, 12, 5, 0, is_decimal=True)
    # 前9级应该是：3.0, 5.4, 7.8, 10.2, 12.6, 15.0, 17.4, 19.8, 22.2
    expected_first_9 = [3.0, 5.4, 7.8, 10.2, 12.6, 15.0, 17.4, 19.8, 22.2]
    assert result[:9] == expected_first_9, f"技能曲线计算失败: {result[:9]} != {expected_first_9}"
    print("✓ 技能曲线计算（小数数据）测试通过")


if __name__ == "__main__":
    print("=" * 60)
    print("          小数乘10处理逻辑测试")
    print("=" * 60)

    test_integer_data_direct_calculation()
    test_decimal_data_scale_by_10()
    test_decimal_data_with_special_value()
    test_percent_integer_parsing()
    test_percent_decimal_parsing()
    test_inverse_formula_decimal_fitting()
    test_skill_curve_with_decimal()

    print("=" * 60)
    print("          所有测试通过！")
    print("=" * 60)
