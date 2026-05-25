#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
集中属性配置模块

此模块集中管理所有属性相关的配置信息，包括：
- 属性名称列表
- 默认成长参数
- 属性分类判断
- 参数验证

消除各模块中的硬编码属性名称，提高代码可维护性。
"""
from typing import Dict, Any, Optional, Tuple, List

# ==================== 属性名称常量 ====================

# 角色普通属性列表
CHARACTER_NORMAL_ATTRS: List[str] = [
    "力量",
    "敏捷",
    "智识",
    "意志",
    "基础攻击力",
]

# 角色技能属性列表
CHARACTER_SKILL_ATTRS: List[str] = [
    "战技倍率",
    "连携技倍率",
    "终结技倍率",
]

# 武器基础属性列表（需要90级成长曲线）
WEAPON_BASE_ATTRS: List[str] = [
    "基础攻击力",
]

# 武器附加属性后缀（需要9级成长曲线）
WEAPON_BONUS_ATTR_SUFFIX: str = '+'

# ==================== 默认参数配置 ====================

DEFAULT_GROWTH_PARAMS: Dict[str, Dict[str, int]] = {
    "力量": {"base": 0, "growth": 0, "divisor": 1, "offset": 0},
    "敏捷": {"base": 0, "growth": 0, "divisor": 1, "offset": 0},
    "智识": {"base": 0, "growth": 0, "divisor": 1, "offset": 0},
    "意志": {"base": 0, "growth": 0, "divisor": 1, "offset": 0},
    "基础攻击力": {"base": 0, "growth": 0, "divisor": 1, "offset": 0},
}


def get_default_growth_params() -> Dict[str, Dict[str, int]]:
    """
    获取默认成长参数配置

    返回：
        默认成长参数字典
    """
    return DEFAULT_GROWTH_PARAMS.copy()


def get_attribute_category(attr_name: str) -> str:
    """
    获取属性分类

    参数：
        attr_name: 属性名称

    返回：
        属性分类：
        - 'character_normal': 角色普通属性
        - 'character_skill': 角色技能属性
        - 'weapon_base': 武器基础属性
        - 'weapon_bonus': 武器附加属性
        - 'unknown': 未知属性
    """
    if attr_name in CHARACTER_NORMAL_ATTRS:
        return 'character_normal'
    elif attr_name in CHARACTER_SKILL_ATTRS:
        return 'character_skill'
    elif attr_name in WEAPON_BASE_ATTRS:
        return 'weapon_base'
    elif attr_name.endswith(WEAPON_BONUS_ATTR_SUFFIX):
        return 'weapon_bonus'
    else:
        return 'unknown'


def is_character_attribute(attr_name: str) -> bool:
    """
    判断是否为角色属性

    参数：
        attr_name: 属性名称

    返回：
        是否为角色属性
    """
    return attr_name in CHARACTER_NORMAL_ATTRS or attr_name in CHARACTER_SKILL_ATTRS


def is_weapon_attribute(attr_name: str) -> bool:
    """
    判断是否为武器属性

    参数：
        attr_name: 属性名称

    返回：
        是否为武器属性
    """
    return attr_name in WEAPON_BASE_ATTRS or attr_name.endswith(WEAPON_BONUS_ATTR_SUFFIX)


def is_weapon_base_attribute(attr_name: str) -> bool:
    """
    判断是否为武器基础属性（需要90级成长曲线）

    参数：
        attr_name: 属性名称

    返回：
        是否为武器基础属性
    """
    return attr_name in WEAPON_BASE_ATTRS


def is_weapon_bonus_attribute(attr_name: str) -> bool:
    """
    判断是否为武器附加属性（需要9级成长曲线）

    参数：
        attr_name: 属性名称

    返回：
        是否为武器附加属性
    """
    return attr_name.endswith(WEAPON_BONUS_ATTR_SUFFIX)


def is_skill_attribute(attr_name: str) -> bool:
    """
    判断是否为技能属性

    参数：
        attr_name: 属性名称

    返回：
        是否为技能属性
    """
    return attr_name in CHARACTER_SKILL_ATTRS


def validate_growth_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    验证成长参数是否有效

    参数：
        params: 成长参数字典

    返回：
        验证结果字典，包含：
        - 'valid': 是否有效
        - 'errors': 错误信息列表
        - 'warnings': 警告信息列表
    """
    errors: List[str] = []
    warnings: List[str] = []

    # 检查必要字段
    required_fields = ['base', 'growth', 'divisor']
    for field in required_fields:
        if field not in params:
            errors.append(f"缺少必要字段: {field}")

    # 检查除数是否为零
    if 'divisor' in params and params['divisor'] == 0:
        errors.append("除数不能为零")

    # 检查数值是否为数字
    numeric_fields = ['base', 'growth', 'divisor', 'offset']
    for field in numeric_fields:
        if field in params and not isinstance(params[field], (int, float)):
            errors.append(f"{field} 必须是数字类型")

    # 检查可选字段
    if 'offset' in params and not isinstance(params['offset'], (int, float)):
        errors.append("offset 必须是数字类型")

    # 检查特殊值字段
    if 'special' in params and not isinstance(params['special'], list):
        errors.append("special 必须是列表类型")

    # 警告：除数为负数
    if 'divisor' in params and params['divisor'] < 0:
        warnings.append("除数为负数，可能导致计算结果不符合预期")

    return {
        'valid': len(errors) == 0,
        'errors': errors,
        'warnings': warnings
    }