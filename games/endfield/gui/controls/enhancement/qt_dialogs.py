# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""PySide6 增强工具弹窗：计算历史 / 多方案对比 / 伤害仪表盘。

P2-07 拆分后本模块只负责再导出，公开导入路径保持不变。
"""

from __future__ import annotations

from .qt_calc_history_dialog import QtCalcHistoryDialog
from .qt_compare_presets_dialog import QtComparePresetsDialog
from .qt_damage_dashboard_dialog import QtDamageDashboardDialog
from .qt_dialogs_styles import (
    _HINT_COLOR,
    _PRIMARY_BTN_STYLE,
    _SEC_BTN_STYLE,
    _SMALL_LABEL,
)

__all__ = [
    "_HINT_COLOR",
    "_PRIMARY_BTN_STYLE",
    "_SEC_BTN_STYLE",
    "_SMALL_LABEL",
    "QtCalcHistoryDialog",
    "QtComparePresetsDialog",
    "QtDamageDashboardDialog",
]
