#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
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
from .core.config import (
    CHARACTER_NORMAL_ATTRS,
    CHARACTER_SKILL_ATTRS,
    DEFAULT_GROWTH_PARAMS,
    WEAPON_BASE_ATTRS,
    WEAPON_BONUS_ATTR_SUFFIX,
    get_attribute_category,
    get_default_growth_params,
    is_character_attribute,
    is_skill_attribute,
    is_weapon_attribute,
    is_weapon_base_attribute,
    is_weapon_bonus_attribute,
    validate_growth_params,
)

# 曲线烘焙（录入 / BWIKI 同步共用）
from .core.curve_baker import bake_character_curves, bake_weapon_curves

# 数据生成器
from .core.data_generator import (
    generate_attributes,
    generate_character_attributes,
    generate_weapon_attributes,
)

# 正向计算公式
from .damage.formula import (
    calculate_bonus_attribute,
    calculate_growth_curve,
    calculate_skill_curve,
    levels,
    talent,
    trust,
    trust_add,
)

# 反向推导公式
from .damage.inverse import (
    fit_attribute_formula,
    fit_formula,
    fit_skill_formula,
    fit_skill_formula_no_special,
    remove_duplicates,
    validate_attribute_formula,
    validate_formula,
    validate_skill_formula,
    validate_skill_formula_no_special,
)

# 伤害乘区计算
from .multiplicative_zones import (
    AbilityBonusZone,
    AttributeMultiplierZone,
    AttributeZoneManager,
    BaseZone,
    DefenseReductionZone,
    FinalAttackZone,
    ZoneManager,
    calculate_ability_bonus,
    calculate_ability_bonus_with_details,
    calculate_attribute_zones,
    calculate_attribute_zones_with_details,
    calculate_final_attack,
    calculate_final_attack_with_details,
)

__all__ = [
    # 配置常量
    "CHARACTER_NORMAL_ATTRS",
    "CHARACTER_SKILL_ATTRS",
    "DEFAULT_GROWTH_PARAMS",
    "WEAPON_BASE_ATTRS",
    "WEAPON_BONUS_ATTR_SUFFIX",
    "AbilityBonusZone",
    "AttributeMultiplierZone",
    "AttributeZoneManager",
    "BaseZone",
    "DefenseReductionZone",
    "FinalAttackZone",
    # 乘区类
    "ZoneManager",
    "bake_character_curves",
    "bake_weapon_curves",
    "calculate_ability_bonus",
    "calculate_ability_bonus_with_details",
    "calculate_attribute_zones",
    "calculate_attribute_zones_with_details",
    "calculate_bonus_attribute",
    "calculate_final_attack",
    "calculate_final_attack_with_details",
    # 正向计算
    "calculate_growth_curve",
    "calculate_skill_curve",
    "fit_attribute_formula",
    "fit_formula",
    "fit_skill_formula",
    "fit_skill_formula_no_special",
    # 数据生成器
    "generate_attributes",
    "generate_character_attributes",
    "generate_weapon_attributes",
    "get_attribute_category",
    # 配置函数
    "get_default_growth_params",
    "is_character_attribute",
    "is_skill_attribute",
    "is_weapon_attribute",
    "is_weapon_base_attribute",
    "is_weapon_bonus_attribute",
    # 常量
    "levels",
    # 反向推导
    "remove_duplicates",
    "talent",
    "trust",
    "trust_add",
    "validate_attribute_formula",
    "validate_formula",
    "validate_growth_params",
    "validate_skill_formula",
    "validate_skill_formula_no_special",
]
