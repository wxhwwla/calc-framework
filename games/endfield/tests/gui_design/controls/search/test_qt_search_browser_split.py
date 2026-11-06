# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""历史搜索浏览弹窗拆分结构测试（P2-07）。"""

from __future__ import annotations

from pathlib import Path

_MODULE_NAMES = (
    "games.endfield.gui.controls.search.qt_search_browser",
    "games.endfield.gui.controls.search.qt_search_browser_build_mixin",
)


def _line_count(module_name: str) -> int:
    module = __import__(module_name, fromlist=["__file__"])
    return len(Path(module.__file__).read_text(encoding="utf-8").splitlines())


def test_search_browser_modules_stay_within_target() -> None:
    for module_name in _MODULE_NAMES:
        assert _line_count(module_name) <= 400, module_name


def test_search_browser_uses_build_mixin() -> None:
    from games.endfield.gui.controls.search.qt_search_browser import SearchHistoryDialog
    from games.endfield.gui.controls.search.qt_search_browser_build_mixin import (
        QtSearchBrowserBuildMixin,
    )

    assert issubclass(SearchHistoryDialog, QtSearchBrowserBuildMixin)
    assert SearchHistoryDialog._build_gui is QtSearchBrowserBuildMixin._build_gui
