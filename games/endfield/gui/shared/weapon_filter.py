# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""
武器过滤逻辑（纯 Python）。

从 endfield_shell.py 提取，不依赖 PySide6，可被 Web/CLI/测试复用。
"""

from __future__ import annotations

from typing import Any


def resolve_weapon_type(char_data: dict[str, Any] | None) -> str:
    """从角色数据中提取武器类型。

    Args:
        char_data: 角色数据字典（可能为 None）

    Returns:
        武器类型字符串，无数据时返回空字符串。
    """
    if not char_data:
        return ""
    return char_data.get("武器", "")


def filter_weapons_for_character(
    all_weapons: list[dict[str, Any]],
    char_data: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    """根据角色武器类型过滤武器列表。

    若角色无武器类型或过滤结果为空，返回完整武器列表。

    Args:
        all_weapons: 全部武器数据列表
        char_data: 角色数据字典（可能为 None）

    Returns:
        过滤后的武器列表（若无法过滤则返回全部）。
    """
    weapon_type = resolve_weapon_type(char_data)
    if not weapon_type:
        return list(all_weapons)
    filtered = [w for w in all_weapons if w.get("类型") == weapon_type]
    if not filtered:
        return list(all_weapons)
    return filtered
