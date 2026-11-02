#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""确认计算核心失败可见性回归测试（P1-01）。

背景：乘区表是文档声明的核心输出，但 ``_on_confirm`` 捕获其异常后只写
warning，界面仍显示“已确认”，用户无法感知主输出缺失。
"""

from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import patch

from games.endfield.gui import endfield_actions
from games.endfield.gui.endfield_actions import ActionsMixin


class _Panel:
    def get_selected_data(self) -> dict[str, str]:
        return {"名称": "测试"}


class _Preset:
    char_name = "测试角色"
    weapon_name = "测试武器"

    def to_dict(self) -> dict[str, str]:
        return {}


class _Loadout:
    def to_loadout_preset(self) -> _Preset:
        return _Preset()


class _Request:
    loadout = _Loadout()


class _Columns:
    def __init__(self) -> None:
        self.refreshed = False
        self.last_request: object | None = None

    def refresh(self, request: object) -> None:
        self.refreshed = True
        self.last_request = request


class _History:
    def __init__(self) -> None:
        self.entries: list[object] = []

    def push(self, entry: object) -> None:
        self.entries.append(entry)


class _StubApp(ActionsMixin):
    def __init__(self, *, compute_sheet_error: Exception | None) -> None:
        self._confirm_in_progress = False
        self.char_panel = _Panel()
        self.weapon_panel = _Panel()
        self.control_dock = SimpleNamespace()
        self.columns = _Columns()
        self._compute_sheet_error = compute_sheet_error
        self.computing_calls = 0
        self.confirmed_calls = 0
        self.pending_calls = 0
        self.last_synced_request: object | None = None

    def _build_request(self) -> _Request:
        return _Request()

    def _sync_evaluation(self, request: object) -> None:
        self.last_synced_request = request

    def _refresh_compute_sheet(self) -> None:
        if self._compute_sheet_error is not None:
            raise self._compute_sheet_error

    def _set_confirm_ui_computing(self) -> None:
        self.computing_calls += 1

    def _set_confirm_ui_confirmed(self) -> None:
        self.confirmed_calls += 1

    def _set_confirm_ui_pending(self) -> None:
        self.pending_calls += 1

    def _update_total_damage_panel(self) -> None:
        return None

    def _refresh_search_estimate(self) -> None:
        return None


class TestConfirmCoreFailureVisibility(unittest.TestCase):
    def _run_confirm(self, app: _StubApp):
        with (
            patch.object(endfield_actions.QApplication, "processEvents"),
            patch.object(endfield_actions.QMessageBox, "warning") as warning,
            patch.object(endfield_actions, "get_app_calculation_history", return_value=_History()),
            patch.object(endfield_actions, "refresh_damage_snapshot"),
        ):
            app._on_confirm()
        return warning

    def test_compute_sheet_failure_is_visible_and_not_confirmed(self) -> None:
        app = _StubApp(compute_sheet_error=RuntimeError("适配器目录缺少 meta.json"))

        warning = self._run_confirm(app)

        self.assertTrue(warning.called, "乘区表失败时必须弹出可见错误")
        self.assertGreaterEqual(app.pending_calls, 1, "失败后按钮不应停留在完整成功状态")
        self.assertEqual(app.confirmed_calls, 1)

    def test_normal_path_does_not_warn(self) -> None:
        app = _StubApp(compute_sheet_error=None)

        warning = self._run_confirm(app)

        self.assertFalse(warning.called, "正常路径不应弹错误")
        self.assertEqual(app.confirmed_calls, 1)
        self.assertEqual(app.pending_calls, 0)


if __name__ == "__main__":
    unittest.main()
