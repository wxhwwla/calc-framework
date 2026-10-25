# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""
预设对比服务（纯 Python）。

从 qt_dialogs.py 提取，不依赖 PySide6，可被 Web/CLI/测试复用。
提供加载预设文件 + 运行对比的便捷封装。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from games.endfield.gui.app.loadout_preset import (
    LoadoutPreset,
    import_presets_from_json_text,
)
from games.endfield.gui.shared.preset_batch_compare import compare_presets_parallel


def load_presets_from_files(
    file_paths: list[str | Path],
) -> list[LoadoutPreset]:
    """从 JSON 文件列表加载预设。

    Args:
        file_paths: JSON 文件路径列表

    Returns:
        加载的预设列表。

    Raises:
        Exception: 文件读取或解析失败时抛出。
    """
    presets: list[LoadoutPreset] = []
    for p in file_paths:
        text = Path(p).read_text(encoding="utf-8")
        presets.extend(import_presets_from_json_text(text))
    return presets


def compare_presets_from_files(
    file_paths: list[str | Path],
    *,
    current_preset: LoadoutPreset,
    characters: list[dict[str, Any]],
    weapons: list[dict[str, Any]],
    equipments: list[dict[str, Any]],
    enemy_defense: float = 100.0,
    max_workers: int = 1,
) -> list[Any]:
    """加载预设文件并与当前配装对比。

    Args:
        file_paths: JSON 文件路径列表
        current_preset: 当前配装预设（排在第一位）
        characters: 角色数据
        weapons: 武器数据
        equipments: 装备数据
        enemy_defense: 敌方防御力
        max_workers: 并行线程数

    Returns:
        对比结果列表（按伤害排名）。
    """
    file_presets = load_presets_from_files(file_paths)
    all_presets = [current_preset, *file_presets]
    return compare_presets_parallel(
        all_presets,
        characters=characters,
        weapons=weapons,
        equipments=equipments,
        enemy_defense=enemy_defense,
        max_workers=max_workers,
    )
