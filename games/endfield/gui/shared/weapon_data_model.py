# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""武器数据解析纯函数 — 从 weapon_data dict 提取附加属性和特殊能力信息。

不依赖 PySide6，可被 GUI/Web/CLI 复用。
"""

from __future__ import annotations

from typing import Any

__all__ = ["extract_bonus_attributes", "read_special_slots"]


def extract_bonus_attributes(weapon_data: dict[str, Any]) -> list[str]:
    """从武器数据中提取附加属性（普通技能效果名称）。

    支持两种数据格式：
    - 新格式：`normal_skills` 列表，每项含 `effect` 字段
    - 旧格式：`基础攻击力` 之后、`特殊能力` 之前的 `xxx+` 键

    Args:
        weapon_data: 武器 JSON 数据字典

    Returns:
        最多 3 个附加属性名称列表
    """
    normal_raw = weapon_data.get("normal_skills")
    if isinstance(normal_raw, list):
        out: list[str] = []
        for item in normal_raw:
            if not isinstance(item, dict):
                continue
            effect = str(item.get("effect", "")).strip()
            if effect:
                out.append(effect)
        return out[:3]

    # 旧格式：基础攻击力 之后的 xxx+ 键
    keys = list(weapon_data.keys())
    try:
        start = keys.index("基础攻击力") + 1
    except ValueError:
        return []
    special_keys = frozenset({"特殊能力", "特殊能力1", "特殊能力2"})
    out = []
    for key in keys[start:]:
        if key in special_keys:
            break
        if key.endswith("+") and isinstance(weapon_data.get(key), list):
            out.append(key)
    return out[:3]


def read_special_slots(weapon_data: dict[str, Any]) -> list[tuple[bool, str, int, int]]:
    """从武器数据中读取特殊能力槽位信息。

    支持两种数据格式：
    - 新格式：`special_skills` 列表，每项含 name/effect/curve/max_stack
    - 旧格式：`特殊能力1`/`特殊能力2` 字典，含 名称/最多叠加层数

    Args:
        weapon_data: 武器 JSON 数据字典

    Returns:
        最多 2 个元组 (available, display_name, default_level, max_stack)
    """
    special_raw = weapon_data.get("special_skills")
    if isinstance(special_raw, list):
        slots: list[tuple[bool, str, int, int]] = []
        for idx in range(2):
            if idx < len(special_raw) and isinstance(special_raw[idx], dict):
                item = special_raw[idx]
                name = str(item.get("name", "")).strip()
                effect = str(item.get("effect", "")).strip()
                curve = item.get("curve")
                max_stack = max(1, int(item.get("max_stack", 1)))
                display_name = name or effect
                available = bool(display_name) and isinstance(curve, list) and len(curve) > 0
                slots.append((available, display_name, 1, max_stack))
            else:
                slots.append((False, "", 1, 1))
        return slots

    # 旧格式
    result: list[tuple[bool, str, int, int]] = []
    for key in ("特殊能力1", "特殊能力2"):
        entry = weapon_data.get(key, {})
        if isinstance(entry, dict):
            name = entry.get("名称", "")
            available = bool(name) and name != "无"
            max_stack = int(entry.get("最多叠加层数", 1))
            result.append((available, name, 1, max_stack))
        else:
            result.append((False, "", 1, 1))
    return result
