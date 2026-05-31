#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""信赖等级 / 技能等级面板测试。"""

from __future__ import annotations

import unittest

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

from games.endfield.gui_design.panels.selection.qt_subpanels import QtSkillLevelPanel, QtTrustPanel


class TestQtTrustPanel(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not QApplication.instance():
            cls._app = QApplication([])
        cls._font = QFont()

    def setUp(self) -> None:
        self.panel = QtTrustPanel(self._font)

    def test_initial_trust_level_zero(self) -> None:
        self.assertEqual(self.panel.trust_level, 0)

    def test_set_level(self) -> None:
        self.panel.set_level(3)
        self.assertEqual(self.panel.trust_level, 3)

    def test_set_level_clamped_high(self) -> None:
        self.panel.set_level(10)
        self.assertEqual(self.panel.trust_level, 4)

    def test_set_level_clamped_low(self) -> None:
        self.panel.set_level(-1)
        self.assertEqual(self.panel.trust_level, 0)

    def test_reset(self) -> None:
        self.panel.set_level(3)
        self.panel.reset()
        self.assertEqual(self.panel.trust_level, 0)

    def test_slider_change_updates_value(self) -> None:
        self.panel._slider.setValue(2)
        self.assertEqual(self.panel.trust_level, 2)

    def test_value_label_updates_on_change(self) -> None:
        self.panel._slider.setValue(4)
        self.assertEqual(self.panel._val_lbl.text(), "4")


class TestQtSkillLevelPanel(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not QApplication.instance():
            cls._app = QApplication([])
        cls._font = QFont()

    def setUp(self) -> None:
        self.panel = QtSkillLevelPanel(self._font)

    def test_initial_levels_all_one(self) -> None:
        self.assertEqual(self.panel.skill_1_level, 1)
        self.assertEqual(self.panel.skill_2_level, 1)
        self.assertEqual(self.panel.skill_3_level, 1)

    def test_apply_preset(self) -> None:
        self.panel.apply_preset(8)
        self.assertEqual(self.panel.skill_1_level, 8)
        self.assertEqual(self.panel.skill_2_level, 8)
        self.assertEqual(self.panel.skill_3_level, 8)

    def test_apply_preset_clamped(self) -> None:
        self.panel.apply_preset(20)
        self.assertEqual(self.panel.skill_1_level, 12)
        self.assertEqual(self.panel.skill_2_level, 12)
        self.assertEqual(self.panel.skill_3_level, 12)

    def test_apply_levels(self) -> None:
        self.panel.apply_levels(3, 6, 9)
        self.assertEqual(self.panel.skill_1_level, 3)
        self.assertEqual(self.panel.skill_2_level, 6)
        self.assertEqual(self.panel.skill_3_level, 9)

    def test_refresh_with_skills(self) -> None:
        data = {"战技倍率": [[100]], "连携技倍率": [[200]], "终结技倍率": [[300]]}
        self.panel.refresh(data)
        self.assertEqual(self.panel.skill_1_level, 1)

    def test_refresh_with_missing_skills(self) -> None:
        data = {"战技倍率": [[100]]}
        self.panel.refresh(data)
        self.assertTrue(self.panel._has_data[0])
        self.assertFalse(self.panel._has_data[1])
        self.assertFalse(self.panel._has_data[2])

    def test_slider_change_updates_level(self) -> None:
        self.panel._sliders[0].setValue(7)
        self.assertEqual(self.panel.skill_1_level, 7)

    def test_skill_level_names_init(self) -> None:
        self.assertEqual(self.panel._names, ["战技", "连携技", "终结技"])


if __name__ == "__main__":
    unittest.main()
