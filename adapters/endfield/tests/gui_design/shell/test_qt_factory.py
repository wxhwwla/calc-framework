#!/usr/bin/env python3
"""PySide6 widget adapter 别名测试。"""

from __future__ import annotations

import unittest

from PySide6.QtWidgets import QApplication

from games.endfield.gui_design.shell.qt_factory import (
    CTkButton,
    CTkCheckBox,
    CTkComboBox,
    CTkEntry,
    CTkFont,
    CTkFrame,
    CTkLabel,
    CTkOptionMenu,
    CTkScrollableFrame,
    CTkSlider,
    CTkSwitch,
    CTkTabview,
    CTkTextbox,
    CTkToplevel,
)


class TestQtFactoryAliases(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not QApplication.instance():
            cls._app = QApplication([])

    def test_ctk_frame_instantiation(self) -> None:
        w = CTkFrame()
        self.assertIsNotNone(w)

    def test_ctk_label_instantiation(self) -> None:
        lbl = CTkLabel(text="test")
        self.assertEqual(lbl.text(), "test")

    def test_ctk_button_instantiation(self) -> None:
        btn = CTkButton(text="go")
        self.assertEqual(btn.text(), "go")

    def test_ctk_option_menu_instantiation(self) -> None:
        menu = CTkOptionMenu()
        menu.addItems(["a", "b"])
        self.assertEqual(menu.count(), 2)

    def test_ctk_slider_instantiation(self) -> None:
        s = CTkSlider()
        s.setRange(0, 100)
        s.setValue(50)
        self.assertEqual(s.value(), 50)

    def test_ctk_entry_instantiation(self) -> None:
        e = CTkEntry()
        e.setText("hello")
        self.assertEqual(e.text(), "hello")

    def test_ctk_checkbox_instantiation(self) -> None:
        cb = CTkCheckBox()
        cb.setChecked(True)
        self.assertTrue(cb.isChecked())

    def test_ctk_switch_same_as_checkbox(self) -> None:
        self.assertIs(CTkSwitch, CTkCheckBox)

    def test_ctk_tabview_instantiation(self) -> None:
        tv = CTkTabview()
        from PySide6.QtWidgets import QWidget
        tv.addTab(QWidget(), "tab1")
        self.assertEqual(tv.count(), 1)

    def test_ctk_scrollable_frame_instantiation(self) -> None:
        sf = CTkScrollableFrame()
        self.assertIsNotNone(sf)

    def test_ctk_textbox_instantiation(self) -> None:
        tb = CTkTextbox()
        tb.setPlainText("hello")
        self.assertEqual(tb.toPlainText(), "hello")

    def test_ctk_toplevel_instantiation(self) -> None:
        tl = CTkToplevel()
        self.assertIsNotNone(tl)
        tl.close()

    def test_ctk_font_instantiation(self) -> None:
        f = CTkFont()
        self.assertIsNotNone(f)

    def test_ctk_combo_box_same_as_option_menu(self) -> None:
        self.assertIs(CTkComboBox, CTkOptionMenu)


if __name__ == "__main__":
    unittest.main()
