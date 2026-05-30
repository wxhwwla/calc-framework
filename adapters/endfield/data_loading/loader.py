#!/usr/bin/env python3
"""
统一数据加载层（运行时唯一数据接缝）。

核心功能：
- 提供角色、武器、装备数据的统一访问接口
- 实现懒加载缓存机制，避免重复读取文件
- 支持数据修改后的缓存刷新
- 提供数据持久化功能

缓存机制说明：
- 三个全局变量存储缓存：_characters、_weapons、_equipments
- 首次调用 get_*() 时加载 JSON 文件并填充缓存
- 后续调用直接返回缓存数据，无需重复读取
- reload_*() 函数清除对应缓存，下次调用 get_*() 时重新加载
- save_*() 函数保存数据后自动调用 reload_*() 刷新缓存

数据流向：
┌─────────────────────────────────────────────────────────────────┐
│                    JSON 文件（预烘焙数据）                      │
│  characters.json / weapons.json / equipments.json             │
└──────────────────────────┬──────────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    全局缓存变量                                │
│  _characters / _weapons / _equipments                         │
└──────────────────────────┬──────────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    访问接口（get_* / reload_* / save_*）       │
└─────────────────────────────────────────────────────────────────┘

设计原则：
- GUI、乘区计算、测试仅通过 get_characters() / get_weapons() / get_equipments() 读取数据
- 录入与 BWIKI 同步经 add_character / add_weapon 写回后调用 reload_* 刷新缓存
- 数据变更通过 save_* 方法持久化，并自动刷新缓存
"""

from __future__ import annotations

import json
from typing import Any

from calc_framework.logging import get_logger

from utils.path_utils import get_resource_path

logger = get_logger("endfield.data_loader")


class DataLoadError(Exception):
    """游戏数据 JSON 加载失败异常。

    Attributes:
        filepath: 失败的文件路径
        reason: 失败原因
    """

    def __init__(self, filepath: str, reason: str):
        self.filepath = filepath
        self.reason = reason
        super().__init__(f"无法加载 {filepath}: {reason}")


# 全局缓存变量（懒加载）
_characters: list[dict[str, Any]] | None = None
"""角色数据缓存，首次调用 get_characters() 时初始化"""

_weapons: list[dict[str, Any]] | None = None
"""武器数据缓存，首次调用 get_weapons() 时初始化"""

_equipments: list[dict[str, Any]] | None = None
"""装备数据缓存，首次调用 get_equipments() 时初始化"""

# JSON 文件路径常量
CHARACTERS_JSON_PATH: str = "character_weapon_equipment/character_data/characters.json"
"""角色数据 JSON 文件路径"""

WEAPONS_JSON_PATH: str = "character_weapon_equipment/weapon_data/weapons.json"
"""武器数据 JSON 文件路径"""

EQUIPMENTS_JSON_PATH: str = "character_weapon_equipment/equipment_data/equipments.json"
"""装备数据 JSON 文件路径"""


def load_json_file(filepath: str, *, strict: bool = False) -> list[dict[str, Any]]:
    """加载 JSON 文件并返回数据列表。

    Args:
        filepath: JSON 文件相对路径
        strict: 是否启用严格模式（严格模式下失败会抛出 DataLoadError）

    Returns:
        JSON 数据列表，如果加载失败且非严格模式则返回空列表

    Raises:
        DataLoadError: 严格模式下加载失败时抛出
    """
    full_path = get_resource_path(filepath)
    try:
        if not full_path.exists():
            msg = f"文件不存在: {full_path}"
            logger.warning(msg)
            if strict:
                raise DataLoadError(filepath, msg)
            return []

        with open(full_path, encoding="utf-8") as f:
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


def get_characters() -> list[dict[str, Any]]:
    """获取所有角色数据（带懒加载缓存）。

    首次调用时从 JSON 文件加载数据并填充缓存，后续调用直接返回缓存。

    Returns:
        角色数据列表
    """
    global _characters
    if _characters is None:
        _characters = load_json_file(CHARACTERS_JSON_PATH, strict=True)
    return _characters


def get_weapons() -> list[dict[str, Any]]:
    """获取所有武器数据（带懒加载缓存）。

    首次调用时从 JSON 文件加载数据并填充缓存，后续调用直接返回缓存。

    Returns:
        武器数据列表
    """
    global _weapons
    if _weapons is None:
        _weapons = load_json_file(WEAPONS_JSON_PATH, strict=True)
    return _weapons


def preload_game_data() -> None:
    """预加载角色、武器与装备到缓存。

    通过 GameDataFacade 预加载所有游戏数据，失败时抛出 DataLoadError。
    适用于应用启动时的初始化阶段。

    Raises:
        DataLoadError: 加载失败时抛出
    """
    from adapters.endfield.data_loading.game_data_facade import GameDataFacade

    facade = GameDataFacade.create()
    if facade.load_error is not None:
        raise facade.load_error
    if facade.equipment_load_error is not None:
        raise facade.equipment_load_error


def fetch_game_data_for_gui() -> tuple[list[dict[str, Any]], list[dict[str, Any]], DataLoadError | None]:
    """供 GUI 加载角色/武器列表。

    失败时返回空列表与错误对象，不抛出异常，适用于 GUI 界面初始化。

    Returns:
        三元组：(角色列表, 武器列表, 加载错误)
    """
    from adapters.endfield.data_loading.game_data_facade import GameDataFacade

    facade = GameDataFacade.create()
    return facade.characters, facade.weapons, facade.load_error


def get_equipments() -> list[dict[str, Any]]:
    """获取所有装备数据（带懒加载缓存）。

    首次调用时从 JSON 文件加载数据并填充缓存，后续调用直接返回缓存。

    Returns:
        装备数据列表
    """
    global _equipments
    if _equipments is None:
        _equipments = load_json_file(EQUIPMENTS_JSON_PATH, strict=True)
    return _equipments


def reload_characters() -> None:
    """重新加载角色数据（清除缓存）。

    清除角色数据缓存，下次调用 get_characters() 时会重新从文件加载。
    """
    global _characters
    _characters = None


def reload_weapons() -> None:
    """重新加载武器数据（清除缓存）。

    清除武器数据缓存，下次调用 get_weapons() 时会重新从文件加载。
    """
    global _weapons
    _weapons = None


def reload_equipments() -> None:
    """重新加载装备数据（清除缓存）。

    清除装备数据缓存，下次调用 get_equipments() 时会重新从文件加载。
    """
    global _equipments
    _equipments = None


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
