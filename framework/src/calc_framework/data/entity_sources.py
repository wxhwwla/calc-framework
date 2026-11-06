#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""实体来源与数据文件名的共享映射（无 PySide6 依赖）。"""

from __future__ import annotations

# 实体来源 -> data/ 下数据文件名（不含 .json）
SOURCE_DATA_STEMS: dict[str, str] = {
    "character": "characters",
    "weapon": "weapons",
    "equipment": "equipments",
    "enemy": "enemies",
}

# 数据文件名 -> 实体来源
DATA_STEM_SOURCE: dict[str, str] = {stem: source for source, stem in SOURCE_DATA_STEMS.items()}

# 实体来源的界面显示名
SOURCE_DISPLAY_NAMES: dict[str, str] = {
    "character": "角色",
    "weapon": "武器",
    "equipment": "装备",
    "enemy": "敌人",
}

__all__ = ["DATA_STEM_SOURCE", "SOURCE_DATA_STEMS", "SOURCE_DISPLAY_NAMES"]
