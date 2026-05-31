#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""捐赠对话框测试。"""

from __future__ import annotationsimport unittestfrom games.endfield.gui_design.legal.donation_qt import open_donation_dialogfrom PySide6.QtWidgets import QApplicationclass TestDonationQt(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not QApplication.instance():
            cls._app = QApplication([])

    def test_open_donation_dialog_creates_dialog(self) -> None:
        dialog = open_donation_dialog()
        self.assertIsNotNone(dialog)
        self.assertEqual(dialog.windowTitle(), "自愿捐赠")
        dialog.accept()

    def test_open_donation_dialog_with_parent(self) -> None:
        from PySide6.QtWidgets import QWidget

        parent = QWidget()
        dialog = open_donation_dialog(parent)
        self.assertEqual(dialog.parent(), parent)
        dialog.accept()
        parent.close()


if __name__ == "__main__":
    unittest.main()
