#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
乘区快照：确认选择后的窄输入 → 右侧乘区可渲染结构。

GUI 只负责展示；本模块集中能力乘区、能力值加成与最终攻击力链。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from calculation.multiplicative_zones.ability_bonus_zone import (
    calculate_ability_bonus_with_details,
)
from calculation.multiplicative_zones.attribute_zone import (
    calculate_attribute_zones_with_details,
)
from calculation.multiplicative_zones.defense_zone import DefenseReductionZone
from calculation.multiplicative_zones.final_attack_zone import (
    calculate_final_attack_with_details,
)

ATTR_DISPLAY_ORDER = ("力量", "敏捷", "智识", "意志")


@dataclass(frozen=True)
class WeaponBonusSelection:
    """武器潜能 / 特殊能力在乘区中的选用档位。"""

    sa1_name: str = ""
    sa1_level: int = 1
    sa2_name: str = ""
    sa2_level: int = 1
    sa3_name: str = ""
    sa3_level: int = 0
    ws_name: str = ""
    ws_level: int = 0


@dataclass(frozen=True)
class MultiplicativeZoneSelection:
    """已确认的角色、武器与等级选择。"""

    character: dict[str, Any]
    weapon: Optional[dict[str, Any]]
    char_level: int
    weapon_level: int
    trust_level: int = 0
    bonuses: WeaponBonusSelection = WeaponBonusSelection()


@dataclass(frozen=True)
class ZoneDisplayLine:
    """右侧乘区一行展示。"""

    text: str
    color: str = "#B8B8B8"


def compute_multiplicative_zone_snapshot(
    selection: MultiplicativeZoneSelection,
) -> list[ZoneDisplayLine]:
    """计算完整乘区展示行（不含 CTk 控件）。"""
    char = selection.character
    weapon = selection.weapon
    b = selection.bonuses
    lines: list[ZoneDisplayLine] = []

    defense = DefenseReductionZone().calculate()
    lines.append(ZoneDisplayLine(f"敌方防御减伤: {defense:.4f}", "#4ECDC4"))

    attr_details = calculate_attribute_zones_with_details(
        char,
        weapon,
        level=selection.char_level,
        sa1_name=b.sa1_name,
        sa1_level=b.sa1_level,
        sa2_name=b.sa2_name,
        sa2_level=b.sa2_level,
        sa3_name=b.sa3_name,
        sa3_level=b.sa3_level,
        ws_name=b.ws_name,
        ws_level=b.ws_level,
        trust_level=selection.trust_level,
    )
    for attr_name in ATTR_DISPLAY_ORDER:
        details = attr_details.get(attr_name, {"base": 0.0, "bonus": 0.0, "total": 0.0})
        base_value = details["base"]
        bonus_value = details["bonus"]
        total_value = details["total"]
        if bonus_value > 0:
            text = f"{attr_name}: {total_value:.1f} ({base_value:.1f}+{bonus_value:.1f})"
        else:
            text = f"{attr_name}: {total_value:.1f}"
        lines.append(ZoneDisplayLine(text, "#B8B8B8"))

    ability = calculate_ability_bonus_with_details(
        char,
        weapon,
        level=selection.char_level,
        sa1_name=b.sa1_name,
        sa1_level=b.sa1_level,
        sa2_name=b.sa2_name,
        sa2_level=b.sa2_level,
        sa3_name=b.sa3_name,
        sa3_level=b.sa3_level,
        ws_name=b.ws_name,
        ws_level=b.ws_level,
        trust_level=selection.trust_level,
    )
    main_attr = ability["main_attr"]
    sub_attr = ability["sub_attr"]
    if main_attr and sub_attr:
        ab_text = (
            f"能力值加成: {ability['bonus']:.4f} "
            f"({main_attr}:{ability['main_value']:.1f}*0.005+"
            f"{sub_attr}:{ability['sub_value']:.1f}*0.002)"
        )
    else:
        ab_text = f"能力值加成: {ability['bonus']:.4f}"
    lines.append(ZoneDisplayLine(ab_text, "#FFD700"))

    final = calculate_final_attack_with_details(
        char,
        weapon,
        char_level=selection.char_level,
        weapon_level=selection.weapon_level,
        sa1_name=b.sa1_name,
        sa1_level=b.sa1_level,
        sa2_name=b.sa2_name,
        sa2_level=b.sa2_level,
        sa3_name=b.sa3_name,
        sa3_level=b.sa3_level,
        ws_name=b.ws_name,
        ws_level=b.ws_level,
        trust_level=selection.trust_level,
    )
    lines.append(
        ZoneDisplayLine(
            f"基础攻击力: {final['base_attack']:.1f} "
            f"({final['char_base_attack']:.1f}+{final['weapon_base_attack']:.1f})",
            "#00D4AA",
        )
    )
    lines.append(
        ZoneDisplayLine(
            f"攻击加成攻击力: {final['attack_bonus_attack']:.1f} "
            f"({final['base_attack']:.1f}×{final['attack_bonus_multiplier']:.3f})",
            "#9B59B6",
        )
    )
    lines.append(
        ZoneDisplayLine(
            f"中间攻击力: {final['intermediate_attack']:.1f} "
            f"({final['attack_bonus_attack']:.1f}+{final['additional_attack']:.1f})",
            "#3498DB",
        )
    )
    lines.append(
        ZoneDisplayLine(
            f"最终攻击力: {final['final_attack']:.1f} "
            f"({final['intermediate_attack']:.1f}×(1+{final['ability_bonus']:.4f}))",
            "#E74C3C",
        )
    )
    return lines
