#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""手动次数开关：待确认行为测试。"""

import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock

from gui_design.multi_skill_controls import on_manual_skill_counts_switch_changed


class TestManualSkillCountsSwitch(unittest.TestCase):
    def test_switch_change_marks_loadout_pending(self) -> None:
        mark_calls: list[object] = []
        app = SimpleNamespace(
            _mark_loadout_pending=lambda: mark_calls.append(True),
        )
        on_manual_skill_counts_switch_changed(app)  # type: ignore[arg-type]
        self.assertEqual(len(mark_calls), 1)

    def test_switch_change_no_op_without_mark_hook(self) -> None:
        """无 _mark_loadout_pending 时不抛错（兼容旧 stub）。"""
        on_manual_skill_counts_switch_changed(SimpleNamespace())  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
