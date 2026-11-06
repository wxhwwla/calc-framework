# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""增强工具弹窗拆分结构测试（P2-07）。

锁定各子模块 ≤400 行，并保证 ``qt_dialogs`` 继续再导出原来的公开类。
"""

from __future__ import annotations

from pathlib import Path

_MODULE_NAMES = (
    "games.endfield.gui.controls.enhancement.qt_dialogs",
    "games.endfield.gui.controls.enhancement.qt_dialogs_styles",
    "games.endfield.gui.controls.enhancement.qt_calc_history_dialog",
    "games.endfield.gui.controls.enhancement.qt_compare_presets_dialog",
    "games.endfield.gui.controls.enhancement.qt_damage_dashboard_dialog",
)


def _line_count(module_name: str) -> int:
    module = __import__(module_name, fromlist=["__file__"])
    return len(Path(module.__file__).read_text(encoding="utf-8").splitlines())


def test_dialog_modules_stay_within_target() -> None:
    for module_name in _MODULE_NAMES:
        assert _line_count(module_name) <= 400, module_name


def test_aggregator_reexports_dialog_classes() -> None:
    from games.endfield.gui.controls.enhancement import (
        qt_calc_history_dialog,
        qt_compare_presets_dialog,
        qt_damage_dashboard_dialog,
        qt_dialogs,
        qt_dialogs_styles,
    )

    assert qt_dialogs.QtCalcHistoryDialog is qt_calc_history_dialog.QtCalcHistoryDialog
    assert qt_dialogs.QtComparePresetsDialog is qt_compare_presets_dialog.QtComparePresetsDialog
    assert qt_dialogs.QtDamageDashboardDialog is qt_damage_dashboard_dialog.QtDamageDashboardDialog
    assert qt_dialogs._SEC_BTN_STYLE is qt_dialogs_styles._SEC_BTN_STYLE
