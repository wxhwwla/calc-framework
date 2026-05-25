#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""确认选择状态判定测试。"""

import unittest

from gui_design.presentation.display_lines import evaluate_display_state


class TestConfirmSelectionState(unittest.TestCase):
    def test_both_valid_updates_zone(self):
        state = evaluate_display_state({"名称": "秋栗"}, {"名称": "坚城铸造者"})
        self.assertTrue(state["can_update_zone"])
        self.assertEqual(state["char_message"], "")
        self.assertEqual(state["weapon_message"], "")

    def test_invalid_character_blocks_zone(self):
        state = evaluate_display_state(None, {"名称": "坚城铸造者"})
        self.assertFalse(state["can_update_zone"])
        self.assertEqual(state["char_message"], "请选择有效角色")
        self.assertEqual(state["weapon_message"], "")

    def test_invalid_weapon_blocks_zone(self):
        state = evaluate_display_state({"名称": "秋栗"}, None)
        self.assertFalse(state["can_update_zone"])
        self.assertEqual(state["char_message"], "")
        self.assertEqual(state["weapon_message"], "请选择有效武器")


if __name__ == "__main__":
    unittest.main()
