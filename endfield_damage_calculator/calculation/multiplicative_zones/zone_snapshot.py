#!/usr/bin/env python3
"""
乘区快照：确认选择后的窄输入 → 右侧乘区可渲染结构。

GUI 只负责展示；本模块集中能力乘区、能力值加成与最终攻击力链。
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

from calculation.multiplicative_zones.ability_bonus_details import (
    calculate_ability_bonus_with_details,
)
from calculation.multiplicative_zones.attribute_zone import (
    calculate_attribute_zones_with_details,
)
from calculation.multiplicative_zones.base_zone import DefenseReductionZone
from calculation.multiplicative_zones.final_attack_zone import (
    calculate_final_attack_with_details,
)

ATTR_DISPLAY_ORDER = ("力量", "敏捷", "智识", "意志")


@dataclass(frozen=True)
class WeaponBonusSelection:
    """武器潜能 / 特殊能力在乘区中的选用档位。"""

    normal_skill_1_name: str = ""
    normal_skill_1_level: int = 1
    normal_skill_2_name: str = ""
    normal_skill_2_level: int = 1
    normal_skill_3_name: str = ""
    normal_skill_3_level: int = 0
    special_skill_1_name: str = ""
    special_skill_1_level: int = 1
    special_skill_1_stack: int = 0
    special_skill_2_name: str = ""
    special_skill_2_level: int = 1
    special_skill_2_stack: int = 0

    sa1_name: str = ""
    sa1_level: int = 1
    sa2_name: str = ""
    sa2_level: int = 1
    sa3_name: str = ""
    sa3_level: int = 0
    ws_name: str = ""
    ws_level: int = 1
    ws_stack: int = 0
    ws2_name: str = ""
    ws2_level: int = 1
    ws2_stack: int = 0

    def legacy_kwargs(self) -> dict[str, int | str]:
        """兼容旧计算函数参数名。"""
        sa1_name = self.normal_skill_1_name or self.sa1_name
        sa1_level = self.normal_skill_1_level if self.normal_skill_1_name else self.sa1_level
        sa2_name = self.normal_skill_2_name or self.sa2_name
        sa2_level = self.normal_skill_2_level if self.normal_skill_2_name else self.sa2_level
        sa3_name = self.normal_skill_3_name or self.sa3_name
        sa3_level = self.normal_skill_3_level if self.normal_skill_3_name else self.sa3_level
        ws_name = self.special_skill_1_name or self.ws_name
        ws_level = self.special_skill_1_level if self.special_skill_1_name else self.ws_level
        ws_stack = self.special_skill_1_stack if self.special_skill_1_name else self.ws_stack
        ws2_name = self.special_skill_2_name or self.ws2_name
        ws2_level = self.special_skill_2_level if self.special_skill_2_name else self.ws2_level
        ws2_stack = self.special_skill_2_stack if self.special_skill_2_name else self.ws2_stack
        return {
            "sa1_name": sa1_name,
            "sa1_level": sa1_level,
            "sa2_name": sa2_name,
            "sa2_level": sa2_level,
            "sa3_name": sa3_name,
            "sa3_level": sa3_level,
            "ws_name": ws_name,
            "ws_level": ws_level,
            "ws_stack": ws_stack,
            "ws2_name": ws2_name,
            "ws2_level": ws2_level,
            "ws2_stack": ws2_stack,
        }

    def calculation_kwargs(self) -> dict[str, int | str]:
        """统一输出给计算链的新参数名（兼容旧字段输入）。"""
        return {
            "normal_skill_1_name": self.normal_skill_1_name or self.sa1_name,
            "normal_skill_1_level": (self.normal_skill_1_level if self.normal_skill_1_name else self.sa1_level),
            "normal_skill_2_name": self.normal_skill_2_name or self.sa2_name,
            "normal_skill_2_level": (self.normal_skill_2_level if self.normal_skill_2_name else self.sa2_level),
            "normal_skill_3_name": self.normal_skill_3_name or self.sa3_name,
            "normal_skill_3_level": (self.normal_skill_3_level if self.normal_skill_3_name else self.sa3_level),
            "special_skill_1_name": self.special_skill_1_name or self.ws_name,
            "special_skill_1_level": (self.special_skill_1_level if self.special_skill_1_name else self.ws_level),
            "special_skill_1_stack": (self.special_skill_1_stack if self.special_skill_1_name else self.ws_stack),
            "special_skill_2_name": self.special_skill_2_name or self.ws2_name,
            "special_skill_2_level": (self.special_skill_2_level if self.special_skill_2_name else self.ws2_level),
            "special_skill_2_stack": (self.special_skill_2_stack if self.special_skill_2_name else self.ws2_stack),
        }

    @classmethod
    def from_calculation_kwargs(cls, kwargs: dict[str, Any]) -> WeaponBonusSelection:
        """由 ``WeaponSkillSelection.calculation_kwargs()`` 等构建。"""
        return cls(
            normal_skill_1_name=str(kwargs.get("normal_skill_1_name", "")),
            normal_skill_1_level=int(kwargs.get("normal_skill_1_level", 1)),
            normal_skill_2_name=str(kwargs.get("normal_skill_2_name", "")),
            normal_skill_2_level=int(kwargs.get("normal_skill_2_level", 1)),
            normal_skill_3_name=str(kwargs.get("normal_skill_3_name", "")),
            normal_skill_3_level=int(kwargs.get("normal_skill_3_level", 0)),
            special_skill_1_name=str(kwargs.get("special_skill_1_name", "")),
            special_skill_1_level=int(kwargs.get("special_skill_1_level", 1)),
            special_skill_1_stack=int(kwargs.get("special_skill_1_stack", 0)),
            special_skill_2_name=str(kwargs.get("special_skill_2_name", "")),
            special_skill_2_level=int(kwargs.get("special_skill_2_level", 1)),
            special_skill_2_stack=int(kwargs.get("special_skill_2_stack", 0)),
        )


@dataclass(frozen=True)
class MultiplicativeZoneSelection:
    """已确认的角色、武器与等级选择。"""

    character: dict[str, Any]
    weapon: dict[str, Any] | None
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
    *,
    use_dag: bool | None = None,
) -> list[ZoneDisplayLine]:
    """计算完整乘区展示行（不含 GUI 控件）。

    参数：
        selection: 角色/武器/等级/武器技能选用组合
        use_dag: None → 检查环境变量 ``ENDFIELD_USE_DAG`` 决定；
                 True → 强制使用 DAG 引擎；
                 False → 强制使用现有引擎
    """
    if use_dag is None:
        use_dag = os.environ.get("ENDFIELD_USE_DAG", "").strip().lower() not in ("0", "false", "no")

    if use_dag:
        from calculation.multiplicative_zones.dag.adapter import compute_snapshot_with_dag
        return compute_snapshot_with_dag(selection)
    char = selection.character
    weapon = selection.weapon
    b = selection.bonuses
    kwargs: dict[str, Any] = b.calculation_kwargs()
    lines: list[ZoneDisplayLine] = []

    defense = DefenseReductionZone().calculate()
    lines.append(ZoneDisplayLine(f"敌方防御减伤: {defense:.4f}", "#4ECDC4"))

    attr_details = calculate_attribute_zones_with_details(
        char,
        weapon,
        level=selection.char_level,
        **kwargs,
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
        **kwargs,
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
        trust_level=selection.trust_level,
        **kwargs,
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
