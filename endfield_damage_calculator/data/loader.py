#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一加载层（运行时唯一数据接缝）

GUI、乘区计算、测试仅通过 ``get_characters()`` / ``get_weapons()`` 读取**预烘焙 JSON**。
录入与 BWIKI 同步经 ``add_character`` / ``add_weapon`` 写回后 ``reload_*`` 刷新缓存。
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, List, Optional, Tuple

from utils.path_utils import get_resource_path

logger = logging.getLogger(__name__)


class DataLoadError(Exception):
    """游戏数据 JSON 加载失败"""

    def __init__(self, filepath: str, reason: str):
        self.filepath = filepath
        self.reason = reason
        super().__init__(f"无法加载 {filepath}: {reason}")


_characters: Optional[List[dict[str, Any]]] = None
_weapons: Optional[List[dict[str, Any]]] = None

CHARACTERS_JSON_PATH: str = "character_weapon_equipment/character_data/characters.json"
WEAPONS_JSON_PATH: str = "character_weapon_equipment/weapon_data/weapons.json"


def load_json_file(filepath: str, *, strict: bool = False) -> List[dict[str, Any]]:
    """加载 JSON 文件并返回数据列表。"""
    full_path = get_resource_path(filepath)
    try:
        if not full_path.exists():
            msg = f"文件不存在: {full_path}"
            logger.warning(msg)
            if strict:
                raise DataLoadError(filepath, msg)
            return []

        with open(full_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            msg = "根节点必须是 JSON 数组"
            logger.error("%s — %s", filepath, msg)
            if strict:
                raise DataLoadError(filepath, msg)
            return []
        return data
    except json.JSONDecodeError as exc:
        msg = f"JSON 解析失败: {exc}"
        logger.error("%s — %s", filepath, msg)
        if strict:
            raise DataLoadError(filepath, msg) from exc
        return []
    except DataLoadError:
        raise
    except Exception as exc:
        msg = str(exc)
        logger.error("%s — %s", filepath, msg)
        if strict:
            raise DataLoadError(filepath, msg) from exc
        return []


def get_characters() -> List[dict[str, Any]]:
    """获取所有角色数据（带缓存）。"""
    global _characters
    if _characters is None:
        _characters = load_json_file(CHARACTERS_JSON_PATH, strict=True)
    return _characters


def get_weapons() -> List[dict[str, Any]]:
    """获取所有武器数据（带缓存）。"""
    global _weapons
    if _weapons is None:
        _weapons = load_json_file(WEAPONS_JSON_PATH, strict=True)
    return _weapons


def preload_game_data() -> None:
    """预加载角色与武器数据到缓存；失败时抛出 DataLoadError。"""
    get_characters()
    get_weapons()


def fetch_game_data_for_gui() -> Tuple[List[dict[str, Any]], List[dict[str, Any]], Optional[DataLoadError]]:
    """供 GUI 加载角色/武器列表；失败时返回空列表与错误对象（不抛异常）。"""
    try:
        return get_characters(), get_weapons(), None
    except DataLoadError as exc:
        return [], [], exc


def reload_characters() -> None:
    """重新加载角色数据（清除缓存）。"""
    global _characters
    _characters = None


def reload_weapons() -> None:
    """重新加载武器数据（清除缓存）。"""
    global _weapons
    _weapons = None


def save_characters(data: List[dict[str, Any]]) -> bool:
    """保存角色数据到 JSON 文件。"""
    try:
        full_path = get_resource_path(CHARACTERS_JSON_PATH)
        with open(full_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        reload_characters()
        return True
    except Exception:
        return False


def save_weapons(data: List[dict[str, Any]]) -> bool:
    """保存武器数据到 JSON 文件。"""
    try:
        full_path = get_resource_path(WEAPONS_JSON_PATH)
        with open(full_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        reload_weapons()
        return True
    except Exception:
        return False


def check_and_save_characters(characters: List[dict[str, Any]]) -> None:
    """检查并保存角色数据（仅在数据有变化时保存）。"""
    if not characters:
        return
    current_data = get_characters()
    if not current_data or characters != current_data:
        save_characters(characters)


def check_and_save_weapons(weapons: List[dict[str, Any]]) -> None:
    """检查并保存武器数据（仅在数据有变化时保存）。"""
    if not weapons:
        return
    current_data = get_weapons()
    if not current_data or weapons != current_data:
        save_weapons(weapons)
