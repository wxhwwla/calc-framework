#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""多技能段列表：确认后倍率标签同步。"""

from __future__ import annotations

import unittest

from gui_design.multi_skill_controls import segment_rows_signature


class TestMultiSkillSegmentSync(unittest.TestCase):
    def test_signature_includes_label_with_multiplier(self) -> None:
        specs = [
            {"key": "战技:1", "label": "战技 第1段 (142%)"},
            {"key": "连携技:1", "label": "连携技 第1段 (80%)"},
        ]
        sig_a = segment_rows_signature(specs)
        specs[0] = {"key": "战技:1", "label": "战技 第1段 (150%)"}
        sig_b = segment_rows_signature(specs)
        self.assertNotEqual(sig_a, sig_b)

    def test_signature_unchanged_when_only_key_order_same(self) -> None:
        specs = [{"key": "战技:1", "label": "战技 第1段 (100%)"}]
        self.assertEqual(segment_rows_signature(specs), segment_rows_signature(list(specs)))


if __name__ == "__main__":
    unittest.main()
