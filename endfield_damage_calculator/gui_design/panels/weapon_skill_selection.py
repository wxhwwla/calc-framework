#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GUI 层武器技能面板适配（re-export calculation 核心 + 面板读写）。"""

from __future__ import annotations

from typing import Any

from calculation.skills.weapon_selection import (
    WeaponSkillSelection,
    normalize_weapon_specials_tuple,
)

__all__ = [
    "WeaponSkillSelection",
    "normalize_weapon_specials_tuple",
    "apply_weapon_skill_selection_to_panel",
    "read_weapon_skill_selection_from_panel",
]


def read_weapon_skill_selection_from_panel(weapon_panel: Any) -> WeaponSkillSelection:
    """从武器选择面板读取当前武器技能选用状态。"""
    def _call(name: str, fallback: str) -> Any:
        getter = getattr(weapon_panel, name, None)
        if callable(getter):
            return getter()
        return getattr(weapon_panel, fallback)()

    raw = (
        _call("get_normal_skill_1_name", "get_special_ability_1_name"),
        _call("get_normal_skill_1_level", "get_special_ability_1_level"),
        _call("get_normal_skill_2_name", "get_special_ability_2_name"),
        _call("get_normal_skill_2_level", "get_special_ability_2_level"),
        _call("get_normal_skill_3_name", "get_special_ability_3_name"),
        _call("get_normal_skill_3_level", "get_special_ability_3_level"),
        _call("get_special_skill_1_name", "get_weapon_special_name"),
        _call("get_special_skill_1_level", "get_weapon_special_level"),
        _call("get_special_skill_1_stack", "get_weapon_special_stack"),
        _call("get_special_skill_2_name", "get_weapon_special_2_name"),
        _call("get_special_skill_2_level", "get_weapon_special_2_level"),
        _call("get_special_skill_2_stack", "get_weapon_special_2_stack"),
    )
    return WeaponSkillSelection.from_legacy_tuple(raw)


def apply_weapon_skill_selection_to_panel(
    weapon_panel: Any,
    selection: WeaponSkillSelection,
) -> None:
    """将选用状态写回武器面板（仅更新等级/层数，名称由武器数据刷新决定）。"""
    panel = getattr(weapon_panel, "special_ability_panel", None)
    if panel is None:
        return

    n1, n2, n3 = selection.normal_skills
    s1, s2 = selection.special_skills

    def _set_level(level_var: Any, level: int) -> None:
        if level_var is not None and hasattr(level_var, "set"):
            level_var.set(str(max(0, int(level))))

    if getattr(panel, "current_special_ability_1_name", ""):
        _set_level(getattr(panel, "special_ability_1_level", None), n1[1])
    if getattr(panel, "current_special_ability_2_name", ""):
        _set_level(getattr(panel, "special_ability_2_level", None), n2[1])
    if getattr(panel, "current_special_ability_3_name", ""):
        _set_level(getattr(panel, "special_ability_3_level", None), n3[1])
    if getattr(panel, "current_weapon_special_name", ""):
        _set_level(getattr(panel, "weapon_special_level", None), s1[1])
        _set_level(getattr(panel, "weapon_special_stack", None), s1[2])
    if getattr(panel, "current_weapon_special_2_name", ""):
        _set_level(getattr(panel, "weapon_special_2_level", None), s2[1])
        _set_level(getattr(panel, "weapon_special_2_stack", None), s2[2])
