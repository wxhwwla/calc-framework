#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主窗口 grid 布局常量。

- **计算页**：五列（角色 | 武器 | 角色属性 | 武器属性 | 乘区）
- **高级页**：原底栏三列（操作 | 全量搜索 | 多技能次数），窄屏时可两行重排

常量 `MAIN_CONTENT_ROW` / `CONTROL_DOCK_ROW` 分别对应计算页与高级页内的 grid 行号语义。
"""

from __future__ import annotations

# 列 0–1 选择区固定宽；列 2–3 属性均分剩余；列 4 乘区固定宽（文案窄，不宜拉伸）
APP_COLUMN_WEIGHTS: tuple[int, ...] = (0, 0, 1, 1, 0)

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
ZONE_COLUMN_MINSIZE = 340

# 底栏内三列：操作 | 全量搜索 | 多技能次数
CONTROL_DOCK_INNER_COLUMN_COUNT = 3
CONTROL_INNER_COL_ACTIONS_MINSIZE = 200
CONTROL_INNER_COL_SEARCH_WEIGHT = 2
CONTROL_INNER_COL_MULTI_WEIGHT = 3
# 紧凑两行布局第二行：搜索略窄、多技能略宽
CONTROL_INNER_COL_COMPACT_SEARCH_WEIGHT = 2
CONTROL_INNER_COL_COMPACT_MULTI_WEIGHT = 3
# 高级页横向不足时，三列改为两行排布（操作独占一行；搜索+多技能并排）
CONTROL_DOCK_COMPACT_BREAKPOINT = 1480

# 底栏说明文案行高（small_font 约 12–14px + 行距）
HINT_LINE_HEIGHT = 18
HINT_BOX_VERTICAL_PADDING = 10


def hint_text_box_height(line_count: int) -> int:
    """固定高度文案框：按行数计算，避免固定像素过小导致裁切。"""
    lines = max(1, int(line_count))
    return lines * HINT_LINE_HEIGHT + HINT_BOX_VERTICAL_PADDING


def should_use_compact_control_dock(window_width: int) -> bool:
    """根据窗口宽度决定高级页三列是否切为紧凑两行布局。"""
    return int(window_width) < CONTROL_DOCK_COMPACT_BREAKPOINT


def control_dock_layout_needs_update(
    window_width: int,
    *,
    last_width: int | None,
    last_compact: bool | None,
) -> bool:
    """窗口宽度与紧凑模式均未变时跳过重排，避免最小化/恢复时重复 grid。"""
    width = int(window_width)
    compact = should_use_compact_control_dock(width)
    return not (last_width == width and last_compact == compact)


def search_action_button_texts(*, compact: bool) -> tuple[str, str]:
    """按布局密度返回搜索主按钮文案（全量、MVP）。"""
    if compact:
        return ("全量遍历", "MVP导出")
    return ("全量遍历（弹窗）", "MVP搜索导出")


# 底栏可变文案区固定高度，避免换行/改字导致整窗比例跳动
SEARCH_ESTIMATE_BOX_HEIGHT = hint_text_box_height(2)
FIXED_LOADOUT_HINT_BOX_HEIGHT = hint_text_box_height(2)
SEARCH_WORKERS_HINT_BOX_HEIGHT = hint_text_box_height(3)
SEARCH_STATUS_BOX_HEIGHT = hint_text_box_height(2)
# 高级页「更多设置」预留固定视口，展开/收起时不推动整列重排
MORE_SETTINGS_VIEWPORT_HEIGHT = 430

# 统一按钮尺寸：主动作更醒目，次级动作保证密集布局下仍可点击
PRIMARY_ACTION_BUTTON_HEIGHT = 40
SECONDARY_ACTION_BUTTON_HEIGHT = 32

MULTI_SKILL_SEGMENT_ROW_HEIGHT = 28
MULTI_SKILL_SEGMENT_BOX_MIN_HEIGHT = 36
MULTI_SKILL_HINT_BOX_HEIGHT = hint_text_box_height(5)
PHYSICAL_ABNORMAL_HINT_BOX_HEIGHT = hint_text_box_height(7)
SPELL_ABNORMAL_HINT_BOX_HEIGHT = hint_text_box_height(6)
# 异常矩阵行标签列最小宽，避免窄列下四字标签被裁切
ANOMALY_MATRIX_LABEL_MINSIZE = 56


def multi_skill_segment_box_height(segment_count: int) -> int:
    """段数输入区预估高度：随行数线性增长（高级页空间足够，不再设上限滚动）。"""
    if segment_count <= 0:
        return MULTI_SKILL_SEGMENT_BOX_MIN_HEIGHT
    needed = segment_count * MULTI_SKILL_SEGMENT_ROW_HEIGHT + 8
    return max(MULTI_SKILL_SEGMENT_BOX_MIN_HEIGHT, needed)
