#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""计算模式下拉：界面文案 ↔ 内部模式标识。"""

from __future__ import annotations

from calc_framework.ui.i18n import tr
from PySide6.QtWidgets import QComboBox

_CALC_MODE_I18N_KEYS: dict[str, str] = {
    "single_hit": "desktop.endfield.calcModeSingleHit",
    "zone_snapshot": "desktop.endfield.calcModeZoneSnapshot",
    "single_skill_search": "desktop.endfield.calcModeSingleSkillSearch",
    "multi_skill_search": "desktop.endfield.calcModeMultiSkillSearch",
}

# (界面显示 canonical 中文, 内部标识) — canonical 用于预设/测试
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
    """内部模式标识 → 界面下拉文案（当前 locale）。"""
    mid = (mode_id or "").strip()
    for _label, internal in CALC_MODE_OPTIONS:
        if internal == mid:
            key = _CALC_MODE_I18N_KEYS.get(internal)
            return tr(key) if key else _label
    return tr(_CALC_MODE_I18N_KEYS["zone_snapshot"])


def populate_calc_mode_combo(combo: QComboBox) -> None:
    """填充计算模式下拉（显示 i18n，itemData 为 mode_id）。"""
    combo.blockSignals(True)
    combo.clear()
    for _label, mode_id in CALC_MODE_OPTIONS:
        key = _CALC_MODE_I18N_KEYS[mode_id]
        combo.addItem(tr(key), mode_id)
    combo.blockSignals(False)


def calculation_mode_from_combo(combo: QComboBox) -> str:
    """从下拉读取内部 mode_id。"""
    data = combo.currentData()
    if data is not None:
        return str(data)
    return calculation_mode_from_label(combo.currentText())


def calculation_mode_from_label(label: str) -> str:
    """将下拉框当前文案转为 display_view / 确认刷新使用的内部模式。"""
    text = (label or "").strip()
    if text in _INTERNAL_MODE_IDS:
        return text
    if text in _LABEL_TO_MODE:
        return _LABEL_TO_MODE[text]
    # 英文或其它 locale 显示文案 → 按 tr 键反查
    for mode_id, key in _CALC_MODE_I18N_KEYS.items():
        if text == tr(key):
            return mode_id
    for option_label, _mode_id in CALC_MODE_OPTIONS:
        if option_label.startswith("单技能遍历") and text.startswith("单技能遍历"):
            return "single_skill_search"
        if option_label.startswith("多技能遍历") and text.startswith("多技能遍历"):
            return "multi_skill_search"
    return "single_hit"
