#!/usr/bin/env python3

# SPDX-License-Identifier: AGPL-3.0
"""
CRUD 操作模块（数据持久化）。

从 loader.py 拆分出的增删改/持久化操作，保持与核心加载/缓存层解耦。
"""

from __future__ import annotations

import json
from typing import Any

from utils.path_utils import get_resource_path

from games.endfield.framework_bridge import get_logger

from .loader import (
    CHARACTERS_JSON_PATH,
    EQUIPMENTS_JSON_PATH,
    WEAPONS_JSON_PATH,
    get_characters,
    get_weapons,
    reload_characters,
    reload_equipments,
    reload_weapons,
)

_logger = get_logger(__name__)


def save_characters(data: list[dict[str, Any]]) -> bool:
    """保存角色数据到 JSON 文件。

    保存后自动调用 reload_characters() 刷新缓存。

    Args:
        data: 要保存的角色数据列表

    Returns:
        True 保存成功，False 保存失败
    """
    try:
        full_path = get_resource_path(CHARACTERS_JSON_PATH)
        with open(full_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        reload_characters()
        return True
    except Exception:
        _logger.warning("保存角色数据失败", exc_info=True)
        return False


def save_weapons(data: list[dict[str, Any]]) -> bool:
    """保存武器数据到 JSON 文件。

    保存后自动调用 reload_weapons() 刷新缓存。

    Args:
        data: 要保存的武器数据列表

    Returns:
        True 保存成功，False 保存失败
    """
    try:
        full_path = get_resource_path(WEAPONS_JSON_PATH)
        with open(full_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        reload_weapons()
        return True
    except Exception:
        _logger.warning("保存武器数据失败", exc_info=True)
        return False


def save_equipments(data: list[dict[str, Any]]) -> bool:
    """保存装备数据到 JSON 文件。

    保存后自动调用 reload_equipments() 刷新缓存。

    Args:
        data: 要保存的装备数据列表

    Returns:
        True 保存成功，False 保存失败
    """
    try:
        full_path = get_resource_path(EQUIPMENTS_JSON_PATH)
        with open(full_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        reload_equipments()
        return True
    except Exception:
        _logger.warning("保存装备数据失败", exc_info=True)
        return False


def check_and_save_characters(characters: list[dict[str, Any]]) -> None:
    """检查并保存角色数据（仅在数据有变化时保存）。

    比较新数据与当前缓存数据，仅在数据不同时才执行保存操作，避免不必要的 IO。

    Args:
        characters: 新的角色数据列表
    """
    if not characters:
        return
    current_data = get_characters()
    if not current_data or characters != current_data:
        save_characters(characters)


def check_and_save_weapons(weapons: list[dict[str, Any]]) -> None:
    """检查并保存武器数据（仅在数据有变化时保存）。

    比较新数据与当前缓存数据，仅在数据不同时才执行保存操作，避免不必要的 IO。

    Args:
        weapons: 新的武器数据列表
    """
    if not weapons:
        return
    current_data = get_weapons()
    if not current_data or weapons != current_data:
        save_weapons(weapons)
