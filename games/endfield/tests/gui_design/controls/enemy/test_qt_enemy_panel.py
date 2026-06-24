#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""敌方参数面板测试。"""

from __future__ import annotations

import unittest
from unittest.mock import patch

from games.endfield.data_loading.enemy_params import (
    DEFAULT_ENEMY_DEFENSE,
    DEFAULT_ENEMY_RESISTANCE,
    DEFAULT_IGNORE_RESISTANCE,
    DEFAULT_IMBALANCE_VULNERABILITY,
    DEFAULT_IS_UNBALANCED,
)
from games.endfield.gui.controls.enemy.qt_enemy_panel import QtEnemyPanel
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication


class TestQtEnemyPanel(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not QApplication.instance():
            cls._app = QApplication([])
        cls._font = QFont()

    def setUp(self) -> None:
        self.panel = QtEnemyPanel(self._font)

    def tearDown(self) -> None:
        self.panel.deleteLater()

    def test_panel_created(self) -> None:
        self.assertIsNotNone(self.panel)

    def test_get_params_returns_defaults(self) -> None:
        params = self.panel.get_params()
        self.assertEqual(params["enemy_defense"], DEFAULT_ENEMY_DEFENSE)
        self.assertEqual(params["enemy_resistance"], DEFAULT_ENEMY_RESISTANCE)
        self.assertEqual(params["ignore_resistance"], DEFAULT_IGNORE_RESISTANCE)
        self.assertEqual(params["imbalance_vulnerability_coeff"], DEFAULT_IMBALANCE_VULNERABILITY)
        self.assertEqual(params["is_unbalanced"], DEFAULT_IS_UNBALANCED)

    def test_set_params_updates_values(self) -> None:
        self.panel.set_params(
            {
                "enemy_defense": 500.0,
                "enemy_resistance": 30.0,
                "ignore_resistance": 10.0,
                "imbalance_vulnerability_coeff": 1.5,
                "is_unbalanced": True,
            }
        )
        params = self.panel.get_params()
        self.assertEqual(params["enemy_defense"], 500.0)
        self.assertEqual(params["enemy_resistance"], 30.0)
        self.assertEqual(params["ignore_resistance"], 10.0)
        self.assertEqual(params["imbalance_vulnerability_coeff"], 1.5)
        self.assertTrue(params["is_unbalanced"])

    def test_set_params_partial_update(self) -> None:
        self.panel.set_params({"enemy_defense": 999.0})
        params = self.panel.get_params()
        self.assertEqual(params["enemy_defense"], 999.0)
        self.assertEqual(params["enemy_resistance"], DEFAULT_ENEMY_RESISTANCE)

    def test_reset_to_default(self) -> None:
        self.panel.set_params(
            {
                "enemy_defense": 999.0,
                "is_unbalanced": True,
            }
        )
        self.panel._reset_to_default()
        params = self.panel.get_params()
        self.assertEqual(params["enemy_defense"], DEFAULT_ENEMY_DEFENSE)
        self.assertFalse(params["is_unbalanced"])

    def test_current_enemy_id_returns_empty_default(self) -> None:
        eid = self.panel.current_enemy_id()
        self.assertIsInstance(eid, str)

    @patch("games.endfield.gui.controls.enemy.qt_enemy_panel.resolve_enemy_defense", return_value=300.0)
    @patch("games.endfield.gui.controls.enemy.qt_enemy_panel.resolve_enemy_resistance", return_value=20.0)
    def test_enemy_combo_change_updates_params(self, mock_res, mock_def) -> None:
        from games.endfield.gui.controls.enemy.qt_enemy_panel import list_plugin_enemy_choices

        choices = list_plugin_enemy_choices()
        if choices:
            self.panel._on_enemy_combo_changed(choices[0][0])
            params = self.panel.get_params()
            self.assertEqual(params["enemy_defense"], 300.0)
            self.assertEqual(params["enemy_resistance"], 20.0)

    def test_signal_on_params_change(self) -> None:
        received_params = []

        def _capture(params):
            received_params.append(params)

        self.panel.enemy_params_changed.connect(_capture)
        self.panel.set_params({"enemy_defense": 888.0})
        self.assertGreaterEqual(len(received_params), 1)


if __name__ == "__main__":
    unittest.main()
