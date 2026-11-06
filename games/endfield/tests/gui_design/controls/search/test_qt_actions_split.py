# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""搜索动作模块拆分结构测试（P2-07）。"""

from __future__ import annotations

from pathlib import Path

_MODULE_NAMES = (
    "games.endfield.gui.controls.search.qt_actions",
    "games.endfield.gui.controls.search.qt_results_dialog",
)


def _line_count(module_name: str) -> int:
    module = __import__(module_name, fromlist=["__file__"])
    return len(Path(module.__file__).read_text(encoding="utf-8").splitlines())


def test_qt_actions_modules_stay_within_target() -> None:
    for module_name in _MODULE_NAMES:
        assert _line_count(module_name) <= 400, module_name


def test_qt_actions_reexports_dialog_symbols() -> None:
    from games.endfield.gui.controls.search import qt_actions, qt_results_dialog

    assert qt_actions.QtSearchResultsDialog is qt_results_dialog.QtSearchResultsDialog
    assert qt_actions._build_tree_items is qt_results_dialog._build_tree_items


def test_search_worker_stays_patchable_from_qt_actions() -> None:
    from games.endfield.gui.controls.search.qt_actions import SearchWorker

    assert SearchWorker.__module__ == "games.endfield.gui.controls.search.qt_actions"
