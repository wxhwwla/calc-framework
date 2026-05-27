#!/usr/bin/env python3
"""控制面板说明文案。"""

import unittest

from gui_design.layout.panel_hints import (
    MULTI_SKILL_COUNTS_HINT,
    PHYSICAL_ABNORMAL_HINT,
    SPELL_ABNORMAL_HINT,
)


class TestPanelHints(unittest.TestCase):
    def test_multi_skill_hint_explains_manual_switch_and_full_search(self):
        hint = MULTI_SKILL_COUNTS_HINT
        self.assertIn("使用手动次数", hint)
        self.assertIn("全量遍历", hint)
        self.assertIn("各段", hint)

    def test_physical_abnormal_hint_explains_matrix_and_damage_mode(self):
        hint = PHYSICAL_ABNORMAL_HINT
        self.assertIn("L0", hint)
        self.assertIn("伤害口径", hint)
        self.assertIn("倒地", hint)
        self.assertIn("120%", hint)

    def test_spell_abnormal_hint_documents_official_formulas(self):
        hint = SPELL_ABNORMAL_HINT
        self.assertIn("80%", hint)
        self.assertIn("160%", hint)
        self.assertIn("196", hint)
        self.assertIn("碎冰", hint)


if __name__ == "__main__":
    unittest.main()
