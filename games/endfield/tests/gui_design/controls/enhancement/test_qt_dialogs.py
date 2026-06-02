#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""增强工具弹窗模块导入测试。"""

from __future__ import annotations

import unittest
from unittest.mock import patch

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication


class TestEnhancementDialogsImport(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not QApplication.instance():
            cls._app = QApplication([])
        cls._font = QFont()

    def test_module_importable(self) -> None:
        with patch(
            "games.endfield.gui.controls.enhancement.qt_dialogs.get_characters",
            return_value=[],
        ):
            from games.endfield.gui.controls.enhancement.qt_dialogs import (
                _HINT_COLOR,
                _SEC_BTN_STYLE,
                _SMALL_LABEL,
                QtCalcHistoryDialog,
                QtComparePresetsDialog,
                QtDamageDashboardDialog,
            )

            self.assertIsNotNone(QtCalcHistoryDialog)
            self.assertIsNotNone(QtComparePresetsDialog)
            self.assertIsNotNone(QtDamageDashboardDialog)
            self.assertIsInstance(_HINT_COLOR, str)
            self.assertIsInstance(_SMALL_LABEL, str)
            self.assertIn("QPushButton", _SEC_BTN_STYLE)

    def test_qt_calc_history_dialog_creation(self) -> None:
        with patch(
            "games.endfield.gui.controls.enhancement.qt_dialogs.get_characters",
            return_value=[],
        ):
            from games.endfield.gui.controls.enhancement.qt_dialogs import (
                QtCalcHistoryDialog,
            )
            from games.endfield.gui.shared.calc_history import CalculationHistory

            history = CalculationHistory()
            dialog = QtCalcHistoryDialog(
                parent=None,
                big_font=self._font,
                small_font=self._font,
                history=history,
            )
            self.assertIsNotNone(dialog)
            dialog.deleteLater()

    def test_compare_presets_dialog_creation(self) -> None:
        with (
            patch(
                "games.endfield.gui.controls.enhancement.qt_dialogs.get_characters",
                return_value=[],
            ),
            patch(
                "games.endfield.gui.controls.enhancement.qt_dialogs.QFileDialog.getOpenFileNames",
                return_value=([], ""),
            ),
        ):
            from games.endfield.gui.controls.enhancement.qt_dialogs import (
                QtComparePresetsDialog,
            )

            def build_preset_fn():
                return None

            dialog = QtComparePresetsDialog(
                parent=None,
                big_font=self._font,
                small_font=self._font,
                build_preset_fn=build_preset_fn,
            )
            self.assertIsNotNone(dialog)
            self.assertTrue(dialog._no_data)
            dialog.deleteLater()


if __name__ == "__main__":
    unittest.main()
