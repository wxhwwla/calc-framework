#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""异常矩阵键与 GUI 对齐测试。"""

from __future__ import annotations

import unittest

from games.endfield.calc.manual_buff.abnormal_matrix import (
    apply_abnormal_matrix_counts,
    physical_abnormal_matrix_specs,
    read_abnormal_matrix_counts,
    ui_level_column_label,
)


class _FakeEdit:
    def __init__(self, text: str = "0", *, enabled: bool = True) -> None:
        self._text = text
        self._enabled = enabled

    def text(self) -> str:
        return self._text

    def setText(self, value: str) -> None:
        self._text = value

    def isEnabled(self) -> bool:
        return self._enabled


class TestAbnormalMatrix(unittest.TestCase):
    def test_ui_level_column_label(self) -> None:
        self.assertIn("L2", ui_level_column_label(2))
        self.assertIn("3层", ui_level_column_label(2))

    def test_read_physical_counts_by_level(self) -> None:
        specs = physical_abnormal_matrix_specs()
        edits = {
            "猛击": [_FakeEdit("0"), _FakeEdit("0"), _FakeEdit("2"), _FakeEdit("0"), _FakeEdit("0")],
        }
        counts = read_abnormal_matrix_counts(edits, specs)
        self.assertEqual(counts.get("猛击:2"), 2)
        self.assertNotIn("erosion", counts)

    def test_apply_roundtrip(self) -> None:
        specs = physical_abnormal_matrix_specs()
        edits = {
            "碎甲": [_FakeEdit() for _ in range(5)],
        }
        source = {"碎甲:1": 4}
        apply_abnormal_matrix_counts(edits, specs, source)
        restored = read_abnormal_matrix_counts(edits, specs)
        self.assertEqual(restored, source)


if __name__ == "__main__":
    unittest.main()
