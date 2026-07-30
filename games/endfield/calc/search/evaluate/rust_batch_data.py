# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""Rust 全批量评估数据预处理。

将 Python 数据结构转换为 Rust 可接受的格式。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class WeaponData:
    """武器数据（Rust 可接受格式）。"""

    name: str
    final_attack: float
    effects: list[tuple[str, float]] = field(default_factory=list)


@dataclass
class EquipmentCombo:
    """装备组合（Rust 可接受格式）。"""

    chest_name: str
    gloves_name: str
    acc_a_name: str
    acc_b_name: str
    effects: list[tuple[str, float]] = field(default_factory=list)
    flat_stats: dict[str, float] = field(default_factory=dict)
    atk_percent: float = 0.0


@dataclass
class CharData:
    """角色数据（Rust 可接受格式）。"""

    name: str
    level: int
    base_attack: float
    base_hp: float = 0.0
    base_defense: float = 0.0
    # ... 其他属性


@dataclass
class CalcParams:
    """计算参数（Rust 可接受格式）。"""

    skill_multiplier: float = 1.0
    damage_type: str = "物理"
    skill_type: str = "战技"
    is_unbalanced: bool = False
    is_true_damage: bool = False
    enemy_defense: float = 100.0
    enemy_resistance: float = 0.0
    ignore_resistance: float = 0.0
    imbalance_vulnerability_coeff: float = 1.3
    crit_rate: float = 0.05
    crit_damage: float = 0.5
    damage_type_bonus: float = 0.0
    skill_type_bonus: float = 0.0
    imbalance_damage_bonus: float = 0.0
    other_damage_bonus: float = 0.0
    combo_stacks: int = 0
    break_defense_stacks: int = 0
    base_damage_bonus: float = 0.0
    crit_mode: str = "non_crit"
    damage_pipeline: str = "normal"


@dataclass
class LoadoutResult:
    """配装结果（Rust 返回格式）。"""

    weapon_name: str
    final_damage: float
    loadout_names: dict[str, str]


def resolve_equipment_slot_lists(
    equipment_catalog: dict[str, list[dict[str, Any]]],
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
]:
    """将装备目录规范为四槽列表 ``(chest, gloves, acc_a, acc_b)``。

    支持两种输入：

    1. 四槽显式：``accessory_a`` / ``accessory_b``
    2. 三槽 canonical：``accessories`` — 展开为 A/B 共用同一列表（笛卡尔积由调用方生成）

    若四槽键已有非空列表，优先使用四槽，忽略 ``accessories``。
    """
    chest_list = list(equipment_catalog.get("chest", []) or [])
    gloves_list = list(equipment_catalog.get("gloves", []) or [])
    acc_a_list = list(equipment_catalog.get("accessory_a", []) or [])
    acc_b_list = list(equipment_catalog.get("accessory_b", []) or [])

    if not acc_a_list and not acc_b_list:
        accessories = list(equipment_catalog.get("accessories", []) or [])
        if accessories:
            acc_a_list = accessories
            acc_b_list = accessories

    return chest_list, gloves_list, acc_a_list, acc_b_list


def prepare_weapon_data(
    weapons: list[Any],
    search_eval: Any,
) -> list[WeaponData]:
    """预处理武器数据。

    Args:
        weapons: 武器候选列表
        search_eval: 搜索评估上下文

    Returns:
        预处理后的武器数据列表
    """
    result = []
    for weapon in weapons:
        weapon_data = search_eval.weapon_data_by_name.get(weapon.name)
        if weapon_data is None:
            continue

        # 提取效果列表
        effects = []
        for eff in weapon.effects:
            effects.append((eff.effect_type, float(eff.value)))

        result.append(
            WeaponData(
                name=weapon.name,
                final_attack=weapon.final_attack,
                effects=effects,
            )
        )

    return result


def prepare_equipment_combos(
    equipment_catalog: dict[str, list[dict[str, Any]]],
    *,
    allow_duplicate_accessory: bool = True,
) -> list[EquipmentCombo]:
    """预处理装备组合。

    Args:
        equipment_catalog: 装备目录。支持：
            - ``chest`` / ``gloves`` / ``accessory_a`` / ``accessory_b``
            - 或 ``chest`` / ``gloves`` / ``accessories``（配件单列表，展开为 A×B）
        allow_duplicate_accessory: 是否允许两件同名配件

    Returns:
        预处理后的装备组合列表
    """
    from games.endfield.calc.equipment.affix import aggregate_loadout_modifiers
    from games.endfield.calc.equipment.system import build_four_slot_loadout

    chest_list, gloves_list, acc_a_list, acc_b_list = resolve_equipment_slot_lists(equipment_catalog)

    if not chest_list or not gloves_list or not acc_a_list or not acc_b_list:
        return []

    result = []
    for chest in chest_list:
        for glove in gloves_list:
            for acc_a in acc_a_list:
                for acc_b in acc_b_list:
                    try:
                        loadout = build_four_slot_loadout(
                            chest=chest,
                            gloves=glove,
                            accessory_a=acc_a,
                            accessory_b=acc_b,
                            allow_duplicate_accessory=allow_duplicate_accessory,
                        )
                        equip_effects, flat_stats, atk_percent = aggregate_loadout_modifiers(loadout)

                        effects = [(eff.effect_type, float(eff.value)) for eff in equip_effects]

                        result.append(
                            EquipmentCombo(
                                chest_name=chest.get("名称", ""),
                                gloves_name=glove.get("名称", ""),
                                acc_a_name=acc_a.get("名称", ""),
                                acc_b_name=acc_b.get("名称", ""),
                                effects=effects,
                                flat_stats=dict(flat_stats),
                                atk_percent=float(atk_percent),
                            )
                        )
                    except (ValueError, KeyError, TypeError):
                        continue

    return result


def prepare_char_data(
    search_eval: Any,
) -> CharData:
    """预处理角色数据。

    Args:
        search_eval: 搜索评估上下文

    Returns:
        预处理后的角色数据
    """
    char_data = search_eval.char_data
    return CharData(
        name=char_data.get("名称", ""),
        level=search_eval.char_level,
        base_attack=float(
            char_data.get("基础攻击", [0])[0]
            if isinstance(char_data.get("基础攻击"), list)
            else char_data.get("基础攻击", 0)
        ),
        base_hp=float(
            char_data.get("基础生命值", [0])[0]
            if isinstance(char_data.get("基础生命值"), list)
            else char_data.get("基础生命值", 0)
        ),
        base_defense=float(
            char_data.get("基础防御力", [0])[0]
            if isinstance(char_data.get("基础防御力"), list)
            else char_data.get("基础防御力", 0)
        ),
    )


def prepare_calc_params(
    base_context: Any,
) -> CalcParams:
    """预处理计算参数。

    Args:
        base_context: 基础伤害上下文

    Returns:
        预处理后的计算参数
    """
    return CalcParams(
        skill_multiplier=base_context.skill_multiplier,
        damage_type=base_context.damage_type,
        skill_type=base_context.skill_type,
        is_unbalanced=base_context.is_unbalanced,
        is_true_damage=base_context.is_true_damage,
        enemy_defense=base_context.enemy_defense,
        enemy_resistance=base_context.enemy_resistance,
        ignore_resistance=base_context.ignore_resistance,
        imbalance_vulnerability_coeff=base_context.imbalance_vulnerability_coeff,
        crit_rate=base_context.crit_rate,
        crit_damage=base_context.crit_damage,
        damage_type_bonus=base_context.damage_type_bonus,
        skill_type_bonus=base_context.skill_type_bonus,
        imbalance_damage_bonus=base_context.imbalance_damage_bonus,
        other_damage_bonus=base_context.other_damage_bonus,
        combo_stacks=base_context.combo_stacks,
        break_defense_stacks=base_context.break_defense_stacks,
        base_damage_bonus=base_context.base_damage_bonus,
        crit_mode=getattr(base_context, "crit_mode", "non_crit"),
        damage_pipeline=getattr(base_context, "damage_pipeline", "normal"),
    )


__all__ = [
    "CalcParams",
    "CharData",
    "EquipmentCombo",
    "LoadoutResult",
    "WeaponData",
    "prepare_calc_params",
    "prepare_char_data",
    "prepare_equipment_combos",
    "prepare_weapon_data",
    "resolve_equipment_slot_lists",
]
