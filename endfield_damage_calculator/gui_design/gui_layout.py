#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主窗口 grid 布局常量（5 列 + 底栏）。

上排：角色 | 武器 | 角色属性 | 武器属性 | 乘区（通高）
下排：计算与搜索（横跨左侧四列，宽度充足，避免长文案被裁切）
"""

from __future__ import annotations

# 列 0–1 选择区固定宽；列 2–3 属性均分；列 4 乘区主伸缩
APP_COLUMN_WEIGHTS: tuple[int, ...] = (0, 0, 1, 1, 5)

MAIN_CONTENT_ROW = 0
CONTROL_DOCK_ROW = 1

CHAR_COLUMN = 0
WEAPON_COLUMN = 1
CHAR_ATTR_COLUMN = 2
WEAPON_ATTR_COLUMN = 3
ZONE_COLUMN = 4

CONTROL_DOCK_COLUMNSPAN = 4
CONTROL_DOCK_MINSIZE = 300

SELECTION_COLUMN_MINSIZE = 260
ATTR_COLUMN_MINSIZE = 168

# 底栏内三列：操作 | 全量搜索 | 多技能
CONTROL_INNER_COL_ACTIONS_MINSIZE = 200
CONTROL_INNER_COL_SEARCH_WEIGHT = 3
CONTROL_INNER_COL_MULTI_WEIGHT = 2
