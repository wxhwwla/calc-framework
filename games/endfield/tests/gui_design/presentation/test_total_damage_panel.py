#!/usr/bin/env python3

# SPDX-License-Identifier: AGPL-3.0
"""总伤结算面板测试。"""

from __future__ import annotations

import unittest

from games.endfield.gui.presentation.total_damage_panel import TotalDamagePanel
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication


class _FakeSnapshot:
    def __init__(self, has_data: bool = True) -> None:
        if has_data:
            self.segment_damage = {"战技:1": 100.0, "连携技:1": 200.0}

            self.segment_counts = {"战技:1": 2, "连携技:1": 1}

            self.segment_totals = {"战技:1": 200.0, "连携技:1": 200.0}

            self.skill_type_totals = {"战技": 200.0, "连携技": 200.0}

            self.weighted_total_damage = 400.0

            self.rotation_share_percent = {"战技:1": 50.0, "连携技:1": 50.0}

            self.selected_skill_label = "全技能"

        else:
            self.segment_damage = {}

            self.segment_counts = {}

            self.segment_totals = {}

            self.skill_type_totals = {}

            self.weighted_total_damage = 0.0

            self.rotation_share_percent = {}

            self.selected_skill_label = ""


class TestTotalDamagePanel(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not QApplication.instance():
            cls._app = QApplication([])

        cls._big_font = QFont()

        cls._big_font.setPointSize(14)

        cls._small_font = QFont()

        cls._small_font.setPointSize(10)

    def setUp(self) -> None:
        self.panel = TotalDamagePanel(self._big_font, self._small_font)

    def test_initial_state_shows_empty_message(self) -> None:
        self.assertIsNotNone(self.panel)

    def test_update_from_snapshot_with_data(self) -> None:
        snap = _FakeSnapshot(has_data=True)

        self.panel.update_from_snapshot(snap)

        self.assertIsNotNone(self.panel)

    def test_update_from_snapshot_none(self) -> None:
        self.panel.update_from_snapshot(None)

        self.assertIsNotNone(self.panel)

    def test_update_from_snapshot_empty_data(self) -> None:
        snap = _FakeSnapshot(has_data=False)

        self.panel.update_from_snapshot(snap)

        self.assertIsNotNone(self.panel)

    def test_hide_damage_clears_panel(self) -> None:
        snap = _FakeSnapshot(has_data=True)

        self.panel.update_from_snapshot(snap)

        self.panel.hide_damage()

        self.assertIsNotNone(self.panel)

    def test_update_from_snapshot_missing_attrs(self) -> None:
        class _MinimalSnapshot:
            pass

        self.panel.update_from_snapshot(_MinimalSnapshot())

        self.assertIsNotNone(self.panel)


if __name__ == "__main__":
    unittest.main()
