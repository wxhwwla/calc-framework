#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""
统一数据加载层（运行时唯一数据接缝）。

核心功能：
- 提供角色、武器、装备数据的统一访问接口
- 实现懒加载缓存机制（委托框架 JsonDataLoader），避免重复读取文件
- 支持数据修改后的缓存刷新
- 提供数据持久化功能

缓存机制说明：
- 三个 JsonDataLoader 实例管理缓存：characters / weapons / equipments
- 首次调用 get_*() 时加载 JSON 文件并填充缓存
- 后续调用直接返回缓存数据，无需重复读取
- reload_*() 函数清除对应缓存，下次调用 get_*() 时重新加载

数据流向：
┌─────────────────────────────────────────────────────────────────┐
│                    JSON 文件（预烘焙数据）                      │
│  characters.json / weapons.json / equipments.json             │
└──────────────────────────┬──────────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│              JsonDataLoader 缓存（框架组件）                   │
│  _character_loader / _weapon_loader / _equipment_loader       │
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

from calc_framework.data.json_loader import JsonDataLoader
from calc_framework.logging import get_logger
from utils.path_utils import get_resource_path

from games.endfield.data_loading import DataLoadingError
from games.endfield.data_loading.curve_materialize import materialize_character_list, materialize_weapon_list

logger = get_logger("endfield.data_loader")


class DataLoadError(DataLoadingError):
    """游戏数据 JSON 加载失败异常。

    Attributes:
        filepath: 失败的文件路径
        reason: 失败原因
    """

    def __init__(self, filepath: str, reason: str):
        self.filepath = filepath
        self.reason = reason
        super().__init__(f"无法加载 {filepath}: {reason}")


# JSON 文件路径常量（相对于仓库根，由 get_resource_path 解析）
CHARACTERS_JSON_PATH: str = "games/endfield/data/characters.json"
WEAPONS_JSON_PATH: str = "games/endfield/data/weapons.json"
EQUIPMENTS_JSON_PATH: str = "games/endfield/data/equipments.json"


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


# ── 懒加载器实例（框架 JsonDataLoader）─────────────────

_character_loader = JsonDataLoader(
    lambda: materialize_character_list(load_json_file(CHARACTERS_JSON_PATH, strict=True))
)
_weapon_loader = JsonDataLoader(lambda: materialize_weapon_list(load_json_file(WEAPONS_JSON_PATH, strict=True)))
_equipment_loader = JsonDataLoader(lambda: load_json_file(EQUIPMENTS_JSON_PATH, strict=True))


# ── 公共访问接口 ────────────────────────────────────


def get_characters() -> list[dict[str, Any]]:
    """获取所有角色数据（带懒加载缓存）。"""
    return _character_loader.get()


def get_weapons() -> list[dict[str, Any]]:
    """获取所有武器数据（带懒加载缓存）。"""
    return _weapon_loader.get()


def get_equipments() -> list[dict[str, Any]]:
    """获取所有装备数据（带懒加载缓存）。"""
    return _equipment_loader.get()


def reload_characters() -> None:
    """重新加载角色数据（清除缓存）。"""
    _character_loader.reload()


def reload_weapons() -> None:
    """重新加载武器数据（清除缓存）。"""
    _weapon_loader.reload()


def reload_equipments() -> None:
    """重新加载装备数据（清除缓存）。"""
    _equipment_loader.reload()


# ── 批量操作 ───────────────────────────────────────


def preload_game_data() -> None:
    """预加载角色、武器与装备到缓存。

    通过 GameDataFacade 预加载所有游戏数据，失败时抛出 DataLoadError。
    适用于应用启动时的初始化阶段。

    Raises:
        DataLoadError: 加载失败时抛出
    """
    from games.endfield.data_loading.game_data_facade import GameDataFacade

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
    from games.endfield.data_loading.game_data_facade import GameDataFacade

    facade = GameDataFacade.create()
    return facade.characters, facade.weapons, facade.load_error
