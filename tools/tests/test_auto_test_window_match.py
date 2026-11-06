# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""自动测试窗口匹配工具的单元测试（不依赖 Windows/pywinauto）。"""

from __future__ import annotations

from scripts.auto_test.utils.window_match import match_window


def test_match_window_by_partial_title() -> None:
    windows = [
        (100, "终末地伤害计算器 v1.0", "Qt5152QWindowIcon"),
        (200, "游戏计算器启动器 v0.7.0-beta", "Qt5152QWindowIcon"),
    ]

    matched = match_window(windows, "游戏计算器启动器")

    assert matched == (200, "游戏计算器启动器 v0.7.0-beta", "Qt5152QWindowIcon")


def test_match_window_ignores_non_matching_titles() -> None:
    windows = [(100, "其他窗口", "Notepad")]

    assert match_window(windows, "终末地伤害计算器") is None


def test_match_window_can_require_class_name() -> None:
    windows = [
        (100, "终末地伤害计算器 v1.0", "Notepad"),
        (200, "终末地伤害计算器 v1.0", "Qt5152QWindowIcon"),
    ]

    matched = match_window(windows, "终末地伤害计算器", class_name="Qt5152QWindowIcon")

    assert matched is not None
    assert matched[0] == 200
