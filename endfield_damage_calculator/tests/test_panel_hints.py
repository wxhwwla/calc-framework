#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""控制面板说明文案。"""

import unittest

from gui_design.panel_hints import MULTI_SKILL_COUNTS_HINT


class TestPanelHints(unittest.TestCase):
    def test_multi_skill_hint_explains_manual_switch_and_full_search(self):
        hint = MULTI_SKILL_COUNTS_HINT
        self.assertIn("使用手动次数", hint)
        self.assertIn("全量遍历", hint)
        self.assertIn("各段", hint)


if __name__ == "__main__":
    unittest.main()
