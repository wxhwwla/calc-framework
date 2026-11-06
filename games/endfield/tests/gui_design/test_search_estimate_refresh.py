#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""搜索预估刷新回归测试（P0-02）。

背景：``_refresh_search_estimate`` 读取了不存在的 ``estimate_output_label``，
而 ``QtControlDock`` 实际提供的是 ``search_estimate_label``，导致确认计算与
范围变更后持续抛出 ``AttributeError``。
"""

from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import patch

from games.endfield.gui.endfield_search import ActionsSearchMixin
from PySide6.QtWidgets import QApplication, QComboBox


class _Label:
    def __init__(self) -> None:
        self.text = ""

    def setText(self, text: str) -> None:  # noqa: N802 — 模拟 Qt 控件 API
        self.text = text


class _Dock:
    """只提供真实控件属性的最小 dock。"""

    def __init__(self) -> None:
        self.search_estimate_label = _Label()

    def read_workers_choice(self) -> str:
        return "4"

    def read_top_n_choice(self) -> str:
        return "10"


class _Panel:
    def __init__(self, data: dict[str, str] | None) -> None:
        self._data = data

    def get_selected_data(self) -> dict[str, str] | None:
        return self._data


class _StubApp(ActionsSearchMixin):
    def __init__(self, *, job_inputs: object | None) -> None:
        self.control_dock = _Dock()
        self.char_panel = _Panel({"名称": "测试角色"})
        self.weapon_panel = _Panel({"名称": "测试武器"})
        self._search_estimated_total_seconds = 0.0
        self._job_inputs = job_inputs

    def _build_search_job_inputs(self) -> object | None:
        return self._job_inputs


class TestSearchEstimateRefresh(unittest.TestCase):
    def test_missing_estimate_output_label_does_not_raise(self) -> None:
        app = _StubApp(job_inputs=None)

        app._refresh_search_estimate()

        self.assertTrue(app.control_dock.search_estimate_label.text)

    def test_estimate_is_recomputed_from_current_controls(self) -> None:
        app = _StubApp(job_inputs=object())
        estimate = SimpleNamespace(text="预计组合数：42,000", estimated_seconds=12.0)

        with (
            patch(
                "games.endfield.calc.search.plan.controller.prepare_search_job",
                return_value=(object(), None),
            ),
            patch(
                "games.endfield.calc.search.run.single_skill.estimate_single_skill_search",
                return_value=estimate,
            ),
            patch(
                "games.endfield.gui.controls.search.search_settings.resolve_parallel_workers",
                return_value=4,
            ),
            patch(
                "games.endfield.gui.controls.search.search_settings.resolve_top_n",
                return_value=10,
            ),
        ):
            app._refresh_search_estimate()

        self.assertEqual(app.control_dock.search_estimate_label.text, "预计组合数：42,000")
        self.assertEqual(app._search_estimated_total_seconds, 12.0)

    def test_job_error_is_displayed_instead_of_raised(self) -> None:
        app = _StubApp(job_inputs=object())

        with patch(
            "games.endfield.calc.search.plan.controller.prepare_search_job",
            return_value=(None, "技能数据缺失"),
        ):
            app._refresh_search_estimate()

        self.assertIn("技能数据缺失", app.control_dock.search_estimate_label.text)


class TestSearchEstimateTriggers(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not QApplication.instance():
            cls._qt_app = QApplication([])

    def test_fixed_loadout_combo_triggers_estimate_refresh(self) -> None:
        class _TriggerApp(ActionsSearchMixin):
            def __init__(self) -> None:
                self.calls = 0
                self.control_dock = SimpleNamespace(
                    single_skill_scope_combo=QComboBox(),
                    equipment_scope_combo=QComboBox(),
                    search_workers_combo=QComboBox(),
                    search_top_n_combo=QComboBox(),
                    fixed_loadout_slots=[QComboBox()],
                )

            def _refresh_search_estimate(self) -> None:
                self.calls += 1

        app = _TriggerApp()
        app._connect_search_estimate_triggers()

        app.control_dock.fixed_loadout_slots[0].addItem("测试装备")

        self.assertEqual(app.calls, 1)


if __name__ == "__main__":
    unittest.main()
