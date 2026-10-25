#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""捐赠对话框测试。"""

from __future__ import annotations

import unittest
from unittest.mock import patch

from games.endfield.gui.legal.donation_qt import open_donation_dialog
from PySide6.QtWidgets import QApplication, QDialog


class TestDonationQt(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not QApplication.instance():
            cls._app = QApplication([])

    @patch.object(QDialog, "exec", return_value=QDialog.DialogCode.Accepted)
    def test_open_donation_dialog_creates_dialog(self, mock_exec) -> None:
        dialog = open_donation_dialog()
        self.assertIsNotNone(dialog)
        self.assertEqual(dialog.windowTitle(), "自愿捐赠")
        dialog.accept()

    @patch.object(QDialog, "exec", return_value=QDialog.DialogCode.Accepted)
    def test_open_donation_dialog_with_parent(self, mock_exec) -> None:
        from PySide6.QtWidgets import QWidget

        parent = QWidget()
        dialog = open_donation_dialog(parent)
        self.assertEqual(dialog.parent(), parent)
        dialog.accept()
        parent.close()


if __name__ == "__main__":
    unittest.main()
