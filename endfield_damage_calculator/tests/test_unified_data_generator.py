#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一数据生成器单元测试
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
from typing import List, Dict, Any
from calculation.data_generator import (
    generate_attributes,
    generate_character_attributes,
    generate_weapon_attributes
)


class TestUnifiedDataGenerator(unittest.TestCase):
    """测试统一数据生成器"""

    def test_generate_character_attributes_basic(self):
        """测试基本角色属性生成"""
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
        """测试角色技能倍率生成"""
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
        skill_curves: List[List[float]] = attrs['战技倍率']  # type: ignore
        self.assertEqual(len(skill_curves), 1)
        self.assertEqual(len(skill_curves[0]), 12)

    def test_generate_character_attributes_empty(self):
        """测试空参数生成角色属性"""
        attrs = generate_character_attributes({})
        self.assertEqual(attrs, {})

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
        """测试空参数生成武器属性"""
        attrs = generate_weapon_attributes({})
        self.assertEqual(attrs, {})

    def test_generate_attributes_character_mode(self):
        """测试通用生成函数的角色模式"""
        params = {
            '力量': {'base': 100, 'growth': 50, 'divisor': 10},
            '战技倍率': [{'base': 100, 'growth': 20, 'divisor': 10}]
        }
        attrs = generate_attributes(params, mode='character')
        self.assertIn('力量', attrs)
        self.assertIn('战技倍率', attrs)

    def test_generate_attributes_weapon_mode(self):
        """测试通用生成函数的武器模式"""
        params = {
            '基础攻击力': {'base': 100, 'growth': 50, 'divisor': 10},
            '攻击力+': {'base': 3, 'growth': 12, 'divisor': 5, 'special': [23.4]}
        }
        attrs = generate_attributes(params, mode='weapon')
        self.assertIn('基础攻击力', attrs)
        self.assertIn('攻击力+', attrs)

    def test_generate_attributes_invalid_mode(self):
        """测试无效模式参数"""
        params = {'基础攻击力': {'base': 100, 'growth': 50, 'divisor': 10}}
        with self.assertRaises(ValueError):
            generate_attributes(params, mode='invalid')


if __name__ == '__main__':
    unittest.main()