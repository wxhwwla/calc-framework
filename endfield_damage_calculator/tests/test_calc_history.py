#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""计算历史记录测试。"""

import unittest

from gui_design.calc_history import CalculationHistory, HistoryEntry


class TestCalculationHistory(unittest.TestCase):
    def test_keeps_at_most_max_entries(self) -> None:
        history = CalculationHistory(max_entries=3)
        for i in range(5):
            history.push(
                HistoryEntry(
                    label=f"run{i}",
                    summary=f"伤害 {100 + i}",
                    preset_snapshot={"i": i},
                )
            )
        entries = history.list_entries()
        self.assertEqual(len(entries), 3)
        self.assertEqual(entries[0].label, "run4")

    def test_restore_returns_snapshot_by_index(self) -> None:
        history = CalculationHistory(max_entries=10)
        history.push(
            HistoryEntry(label="a", summary="s", preset_snapshot={"char": "X"})
        )
        restored = history.get_snapshot(0)
        self.assertEqual(restored["char"], "X")


if __name__ == "__main__":
    unittest.main()
