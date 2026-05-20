#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据生成器单元测试
"""

import unittest
from typing import List
from character_weapon_equipment.character_data.formula import generate_character_attributes
from character_weapon_equipment.weapon_data.formula import generate_weapon_attributes
from data.loader import get_characters, get_weapons, load_json_file


class TestCharacterDataGenerator(unittest.TestCase):
    """测试角色属性生成器"""

    def test_generate_character_attributes_basic(self):
        """测试基本属性生成"""
        params = {
            '力量': {'base': 100, 'growth': 50, 'divisor': 10},
            '敏捷': {'base': 80, 'growth': 40, 'divisor': 10}
        }
        attrs = generate_character_attributes(params)
        self.assertIn('力量', attrs)
        self.assertIn('敏捷', attrs)
        self.assertEqual(len(attrs['力量']), 90)
        self.assertEqual(len(attrs['敏捷']), 90)

    def test_generate_character_attributes_with_skill_multiplier(self):
        """测试技能倍率生成"""
        params = {
            '力量': {'base': 100, 'growth': 50, 'divisor': 10},
            '战技倍率': [
                {
                    'base': 100,
                    'growth': 20,
                    'divisor': 10,
                    'special': [150, 160, 170]
                }
            ]
        }
        attrs = generate_character_attributes(params)
        self.assertIn('战技倍率', attrs)
        # 使用类型注解帮助类型检查器
        skill_curves: List[List[float]] = attrs['战技倍率']  # type: ignore
        self.assertEqual(len(skill_curves), 1)
        self.assertEqual(len(skill_curves[0]), 12)

    def test_generate_character_attributes_empty(self):
        """测试空参数"""
        attrs = generate_character_attributes({})
        self.assertEqual(attrs, {})


class TestWeaponDataGenerator(unittest.TestCase):
    """测试武器属性生成器"""

    def test_generate_weapon_attributes_basic(self):
        """测试基本武器属性生成"""
        params = {
            '基础攻击力': {'base': 100, 'growth': 50, 'divisor': 10},
            '敏捷+': {'base': 5, 'growth': 3, 'divisor': 10, 'special': [79]}
        }
        attrs = generate_weapon_attributes(params)
        self.assertIn('基础攻击力', attrs)
        self.assertIn('敏捷+', attrs)
        self.assertEqual(len(attrs['基础攻击力']), 90)
        self.assertEqual(len(attrs['敏捷+']), 9)

    def test_generate_weapon_attributes_empty(self):
        """测试空参数"""
        attrs = generate_weapon_attributes({})
        self.assertEqual(attrs, {})


class TestDataLoader(unittest.TestCase):
    """测试数据加载器"""

    def test_get_characters(self):
        """测试获取角色数据"""
        chars = get_characters()
        self.assertIsInstance(chars, list)
        self.assertGreater(len(chars), 0)
        # 验证每个元素是字典
        for char in chars:
            self.assertIsInstance(char, dict)

    def test_get_weapons(self):
        """测试获取武器数据"""
        weapons = get_weapons()
        self.assertIsInstance(weapons, list)
        self.assertGreater(len(weapons), 0)
        # 验证每个元素是字典
        for weapon in weapons:
            self.assertIsInstance(weapon, dict)

    def test_load_json_file(self):
        """测试加载JSON文件"""
        import os
        test_data = {'test': 'data'}
        # 测试缓存功能
        result = load_json_file('character_weapon_equipment/character_data/characters.json')
        self.assertIsInstance(result, list)


if __name__ == '__main__':
    unittest.main()
