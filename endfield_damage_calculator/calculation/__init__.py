#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
计算模块包

整合所有计算相关功能，提供统一的导入接口。

包含：
- 正向计算公式（通用成长曲线计算）
- 反向推导公式（通过数据反推公式参数）
- 数据生成器（角色/武器属性生成）
- 伤害乘区计算（乘法区伤害计算）
"""

# 配置模块
from calculation.config import (
    CHARACTER_NORMAL_ATTRS,
    CHARACTER_SKILL_ATTRS,
    WEAPON_BASE_ATTRS,
    WEAPON_BONUS_ATTR_SUFFIX,
    DEFAULT_GROWTH_PARAMS,
    get_default_growth_params,
    get_attribute_category,
    is_character_attribute,
    is_weapon_attribute,
    is_weapon_base_attribute,
    is_weapon_bonus_attribute,
    is_skill_attribute,
    validate_growth_params,
)

# 正向计算公式
from calculation.formula import (
    levels,
    talent,
    trust,
    trust_add,
    calculate_growth_curve,
    calculate_skill_curve,
    calculate_bonus_attribute,
)

# 数据生成器
from calculation.data_generator import (
    generate_attributes,
    generate_character_attributes,
    generate_weapon_attributes,
)

# 曲线烘焙（录入 / BWIKI 同步共用）
from calculation.curve_baker import bake_character_curves, bake_weapon_curves

# 反向推导公式
from calculation.inverse import (
    remove_duplicates,
    fit_attribute_formula,
    fit_skill_formula,
    fit_skill_formula_no_special,
    fit_formula,
    validate_attribute_formula,
    validate_skill_formula,
    validate_skill_formula_no_special,
    validate_formula,
)

# 伤害乘区计算
from calculation.multiplicative_zones import (
    ZoneManager,
    BaseZone,
    DefenseReductionZone,
    AttributeMultiplierZone,
    AttributeZoneManager,
    calculate_attribute_zones,
    calculate_attribute_zones_with_details,
    AbilityBonusZone,
    calculate_ability_bonus,
    calculate_ability_bonus_with_details,
    FinalAttackZone,
    calculate_final_attack,
    calculate_final_attack_with_details,
)

__all__ = [
    # 配置常量
    "CHARACTER_NORMAL_ATTRS",
    "CHARACTER_SKILL_ATTRS",
    "WEAPON_BASE_ATTRS",
    "WEAPON_BONUS_ATTR_SUFFIX",
    "DEFAULT_GROWTH_PARAMS",
    # 配置函数
    "get_default_growth_params",
    "get_attribute_category",
    "is_character_attribute",
    "is_weapon_attribute",
    "is_weapon_base_attribute",
    "is_weapon_bonus_attribute",
    "is_skill_attribute",
    "validate_growth_params",
    # 常量
    "levels",
    "talent",
    "trust",
    "trust_add",
    # 正向计算
    "calculate_growth_curve",
    "calculate_skill_curve",
    "calculate_bonus_attribute",
    # 数据生成器
    "generate_attributes",
    "generate_character_attributes",
    "generate_weapon_attributes",
    "bake_character_curves",
    "bake_weapon_curves",
    # 反向推导
    "remove_duplicates",
    "fit_attribute_formula",
    "fit_skill_formula",
    "fit_skill_formula_no_special",
    "fit_formula",
    "validate_attribute_formula",
    "validate_skill_formula",
    "validate_skill_formula_no_special",
    "validate_formula",
    # 乘区类
    "ZoneManager",
    "BaseZone",
    "DefenseReductionZone",
    "AttributeMultiplierZone",
    "AttributeZoneManager",
    "calculate_attribute_zones",
    "calculate_attribute_zones_with_details",
    "AbilityBonusZone",
    "calculate_ability_bonus",
    "calculate_ability_bonus_with_details",
    "FinalAttackZone",
    "calculate_final_attack",
    "calculate_final_attack_with_details",
]
