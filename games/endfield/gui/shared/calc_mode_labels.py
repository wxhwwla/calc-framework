#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""计算模式下拉：界面中文文案 ↔ 内部模式标识。"""

from __future__ import annotations

# (界面显示, 内部标识)
CALC_MODE_OPTIONS: tuple[tuple[str, str], ...] = (
    ("单段伤害计算", "single_hit"),
    ("乘区快照", "zone_snapshot"),
    ("单技能遍历(快速预览)", "single_skill_search"),
    ("多技能遍历(快速预览)", "multi_skill_search"),
)

DEFAULT_CALC_MODE_LABEL = CALC_MODE_OPTIONS[1][0]

CALC_MODE_LABELS: tuple[str, ...] = tuple(label for label, _ in CALC_MODE_OPTIONS)

_LABEL_TO_MODE: dict[str, str] = dict(CALC_MODE_OPTIONS)
_INTERNAL_MODE_IDS: frozenset[str] = frozenset(mode_id for _, mode_id in CALC_MODE_OPTIONS)


def calculation_mode_label(mode_id: str) -> str:
    """内部模式标识 → 界面下拉文案。"""
    mid = (mode_id or "").strip()
    for label, internal in CALC_MODE_OPTIONS:
        if internal == mid:
            return label
    return DEFAULT_CALC_MODE_LABEL


def calculation_mode_from_label(label: str) -> str:
    """将下拉框当前文案转为 display_view / 确认刷新使用的内部模式。"""
    text = (label or "").strip()
    if text in _INTERNAL_MODE_IDS:
        return text
    if text in _LABEL_TO_MODE:
        return _LABEL_TO_MODE[text]
    for option_label, _mode_id in CALC_MODE_OPTIONS:
        if option_label.startswith("单技能遍历") and text.startswith("单技能遍历"):
            return "single_skill_search"
        if option_label.startswith("多技能遍历") and text.startswith("多技能遍历"):
            return "multi_skill_search"
    return "single_hit"
