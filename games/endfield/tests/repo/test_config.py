#!/usr/bin/env python3

# SPDX-License-Identifier: AGPL-3.0
"""

属性配置模块单元测试

"""

import unittest

from games.endfield.calc.core.config import (
    CHARACTER_NORMAL_ATTRS,
    CHARACTER_SKILL_ATTRS,
    WEAPON_BASE_ATTRS,
    WEAPON_BONUS_ATTR_SUFFIX,
    get_attribute_category,
    get_default_growth_params,
    is_character_attribute,
    is_skill_attribute,
    is_weapon_attribute,
    validate_growth_params,
)


class TestConfigConstants(unittest.TestCase):
    """测试配置常量"""

    def test_character_normal_attrs(self):
        """测试角色普通属性列表"""

        self.assertIsInstance(CHARACTER_NORMAL_ATTRS, list)

        self.assertIn("力量", CHARACTER_NORMAL_ATTRS)

        self.assertIn("敏捷", CHARACTER_NORMAL_ATTRS)

        self.assertIn("智识", CHARACTER_NORMAL_ATTRS)

        self.assertIn("意志", CHARACTER_NORMAL_ATTRS)

        self.assertIn("基础攻击力", CHARACTER_NORMAL_ATTRS)

    def test_character_skill_attrs(self):
        """测试角色技能属性列表"""

        self.assertIsInstance(CHARACTER_SKILL_ATTRS, list)

        self.assertIn("战技倍率", CHARACTER_SKILL_ATTRS)

        self.assertIn("连携技倍率", CHARACTER_SKILL_ATTRS)

        self.assertIn("终结技倍率", CHARACTER_SKILL_ATTRS)

    def test_weapon_base_attrs(self):
        """测试武器基础属性列表"""

        self.assertIsInstance(WEAPON_BASE_ATTRS, list)

        self.assertIn("基础攻击力", WEAPON_BASE_ATTRS)

    def test_weapon_bonus_suffix(self):
        """测试武器附加属性后缀"""

        self.assertEqual(WEAPON_BONUS_ATTR_SUFFIX, "+")


class TestConfigFunctions(unittest.TestCase):
    """测试配置功能函数"""

    def test_get_default_growth_params(self):
        """测试获取默认成长参数"""

        params = get_default_growth_params()

        self.assertIsInstance(params, dict)

        for attr in CHARACTER_NORMAL_ATTRS:
            self.assertIn(attr, params)

            self.assertIsInstance(params[attr], dict)

            self.assertIn("base", params[attr])

            self.assertIn("growth", params[attr])

            self.assertIn("divisor", params[attr])

            self.assertIn("offset", params[attr])

    def test_get_attribute_category(self):
        """测试获取属性分类"""

        self.assertEqual(get_attribute_category("力量"), "character_normal")

        self.assertEqual(get_attribute_category("战技倍率"), "character_skill")

        # 基础攻击力同时属于角色和武器，优先返回角色分类

        self.assertEqual(get_attribute_category("基础攻击力"), "character_normal")

        self.assertEqual(get_attribute_category("敏捷+"), "weapon_bonus")

        self.assertEqual(get_attribute_category("未知属性"), "unknown")

    def test_is_character_attribute(self):
        """测试是否为角色属性"""

        self.assertTrue(is_character_attribute("力量"))

        self.assertTrue(is_character_attribute("战技倍率"))

        # 基础攻击力同时属于角色和武器

        self.assertTrue(is_character_attribute("基础攻击力"))

        self.assertFalse(is_character_attribute("敏捷+"))

    def test_is_weapon_attribute(self):
        """测试是否为武器属性"""

        self.assertTrue(is_weapon_attribute("基础攻击力"))

        self.assertTrue(is_weapon_attribute("敏捷+"))

        self.assertFalse(is_weapon_attribute("力量"))

        self.assertFalse(is_weapon_attribute("战技倍率"))

    def test_is_skill_attribute(self):
        """测试是否为技能属性"""

        self.assertTrue(is_skill_attribute("战技倍率"))

        self.assertTrue(is_skill_attribute("连携技倍率"))

        self.assertTrue(is_skill_attribute("终结技倍率"))

        self.assertFalse(is_skill_attribute("力量"))

        self.assertFalse(is_skill_attribute("基础攻击力"))

    def test_validate_growth_params_valid(self):
        """测试验证有效成长参数"""

        params = {"base": 100, "growth": 50, "divisor": 10, "offset": 0}

        result = validate_growth_params(params)

        self.assertTrue(result["valid"])

        self.assertEqual(result["errors"], [])

    def test_validate_growth_params_invalid(self):
        """测试验证无效成长参数"""

        params = {"base": 100, "growth": 50}  # 缺少必要字段

        result = validate_growth_params(params)

        self.assertFalse(result["valid"])

        self.assertGreater(len(result["errors"]), 0)

    def test_validate_growth_params_divisor_zero(self):
        """测试除数为零的情况"""

        params = {"base": 100, "growth": 50, "divisor": 0, "offset": 0}

        result = validate_growth_params(params)

        self.assertFalse(result["valid"])


if __name__ == "__main__":
    unittest.main()
