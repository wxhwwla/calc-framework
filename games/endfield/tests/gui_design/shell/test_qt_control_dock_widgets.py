#!/usr/bin/env python3
"""高级页控制栏小部件测试。"""

from __future__ import annotations

import unittest

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication, QLineEdit, QWidget

from gui_design.shell.qt_control_dock_widgets import (
    ComboRow,
    HintLabel,
    SectionHeader,
    SmallLabel,
    build_abnormal_matrix,
    read_abnormal_edits,
)


class TestControlDockWidgets(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not QApplication.instance():
            cls._app = QApplication([])
        cls._font = QFont()

    def test_section_header_renders_text(self) -> None:
        h = SectionHeader("测试标题", self._font)
        self.assertEqual(h.text(), "测试标题")

    def test_hint_label_has_word_wrap(self) -> None:
        h = HintLabel("提示文本", self._font)
        self.assertTrue(h.wordWrap())

    def test_small_label_renders_text(self) -> None:
        lbl = SmallLabel("标签", self._font)
        self.assertEqual(lbl.text(), "标签")

    def test_combo_row_current(self) -> None:
        row = ComboRow("模式", ["a", "b", "c"], "b", self._font)
        self.assertEqual(row.current(), "b")

    def test_combo_row_empty_items(self) -> None:
        row = ComboRow("空", [], "", self._font)
        self.assertEqual(row.current(), "")

    def test_combo_row_layout_setup(self) -> None:
        row = ComboRow("标签", ["x", "y"], "x", self._font)
        self.assertEqual(row.label.text(), "标签")
        self.assertEqual(row.combo.count(), 2)

    def test_build_abnormal_matrix_small(self) -> None:
        w, edits = build_abnormal_matrix(self._font, ["row1"], ["col1"])
        self.assertIsInstance(w, QWidget)
        self.assertIn("row1", edits)
        self.assertEqual(len(edits["row1"]), 1)

    def test_build_abnormal_matrix_multi(self) -> None:
        w, edits = build_abnormal_matrix(self._font, ["r1", "r2"], ["c1", "c2"])
        self.assertEqual(len(edits), 2)
        self.assertEqual(len(edits["r1"]), 2)
        self.assertEqual(len(edits["r2"]), 2)

    def test_read_abnormal_edits_empty(self) -> None:
        w, edits = build_abnormal_matrix(self._font, ["r1"], ["c1"])
        result = read_abnormal_edits(edits, ["key1"])
        self.assertEqual(result["key1"], 0)

    def test_read_abnormal_edits_with_values(self) -> None:
        w, edits = build_abnormal_matrix(self._font, ["r1"], ["c1", "c2"])
        edits["r1"][0].setText("3")
        edits["r1"][1].setText("4")
        result = read_abnormal_edits(edits, ["key1"])
        self.assertEqual(result["key1"], 7)

    def test_read_abnormal_edits_negative_values_clamped(self) -> None:
        w, edits = build_abnormal_matrix(self._font, ["r1"], ["c1"])
        edits["r1"][0].setText("-5")
        result = read_abnormal_edits(edits, ["key1"])
        self.assertEqual(result["key1"], 0)

    def test_read_abnormal_edits_non_numeric(self) -> None:
        w, edits = build_abnormal_matrix(self._font, ["r1"], ["c1"])
        edits["r1"][0].setText("abc")
        result = read_abnormal_edits(edits, ["key1"])
        self.assertEqual(result["key1"], 0)

    def test_build_abnormal_matrix_layout_setup(self) -> None:
        w, edits = build_abnormal_matrix(self._font, ["r1", "r2"], ["c1", "c2"])
        self.assertIsNotNone(w.layout())
        self.assertGreater(w.layout().count(), 0)


if __name__ == "__main__":
    unittest.main()
