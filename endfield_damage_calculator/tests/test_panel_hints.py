#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""控制面板说明文案。"""

import unittest

from gui_design.panel_hints import MULTI_SKILL_COUNTS_HINT


class TestPanelHints(unittest.TestCase):
    def test_multi_skill_hint_explains_mode_confirm_and_manual_switch(self):
        hint = MULTI_SKILL_COUNTS_HINT
        self.assertIn("多技能遍历(快速预览)", hint)
        self.assertIn("确认选择", hint)
        self.assertIn("使用手动次数", hint)
        self.assertIn("技能等级", hint)
        self.assertNotIn("左侧等级", hint)


if __name__ == "__main__":
    unittest.main()
