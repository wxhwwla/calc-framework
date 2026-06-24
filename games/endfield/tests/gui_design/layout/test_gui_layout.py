#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""GUI 布局常量与工具函数测试。"""

from __future__ import annotations

import unittest

from games.endfield.gui.layout.gui_layout import (
    CONTROL_DOCK_COMPACT_BREAKPOINT,
    HINT_BOX_VERTICAL_PADDING,
    HINT_LINE_HEIGHT,
    MULTI_SKILL_SEGMENT_BOX_MIN_HEIGHT,
    MULTI_SKILL_SEGMENT_ROW_HEIGHT,
    control_dock_layout_needs_update,
    hint_text_box_height,
    multi_skill_segment_box_height,
    search_action_button_texts,
    should_use_compact_control_dock,
)


class TestHintTextBoxHeight(unittest.TestCase):
    def test_zero_lines_falls_back_to_min(self):
        self.assertEqual(hint_text_box_height(0), HINT_LINE_HEIGHT + HINT_BOX_VERTICAL_PADDING)

    def test_single_line(self):
        self.assertEqual(hint_text_box_height(1), 1 * HINT_LINE_HEIGHT + HINT_BOX_VERTICAL_PADDING)

    def test_multi_line(self):
        self.assertEqual(hint_text_box_height(5), 5 * HINT_LINE_HEIGHT + HINT_BOX_VERTICAL_PADDING)

    def test_negative_input_clamped(self):
        self.assertEqual(hint_text_box_height(-3), HINT_LINE_HEIGHT + HINT_BOX_VERTICAL_PADDING)


class TestShouldUseCompactControlDock(unittest.TestCase):
    def test_compact_when_below_breakpoint(self):
        self.assertTrue(should_use_compact_control_dock(CONTROL_DOCK_COMPACT_BREAKPOINT - 1))

    def test_not_compact_at_breakpoint(self):
        self.assertFalse(should_use_compact_control_dock(CONTROL_DOCK_COMPACT_BREAKPOINT))

    def test_not_compact_above_breakpoint(self):
        self.assertFalse(should_use_compact_control_dock(CONTROL_DOCK_COMPACT_BREAKPOINT + 100))


class TestControlDockLayoutNeedsUpdate(unittest.TestCase):
    def test_no_change_returns_false(self):
        result = control_dock_layout_needs_update(
            1200,
            last_width=1200,
            last_compact=True,
        )
        self.assertFalse(result)

    def test_width_change_triggers_update(self):
        result = control_dock_layout_needs_update(
            1300,
            last_width=1200,
            last_compact=False,
        )
        self.assertTrue(result)

    def test_compact_change_triggers_update(self):
        result = control_dock_layout_needs_update(
            1400,
            last_width=1200,
            last_compact=False,
        )
        # 1400 < 1480 → compact=True
        self.assertTrue(result)

    def test_none_last_width_triggers_update(self):
        result = control_dock_layout_needs_update(1200, last_width=None, last_compact=None)
        self.assertTrue(result)


class TestSearchActionButtonTexts(unittest.TestCase):
    def test_compact_labels(self):
        labels = search_action_button_texts(compact=True)
        self.assertEqual(labels, ("全量遍历", "最优导出"))

    def test_full_labels(self):
        labels = search_action_button_texts(compact=False)
        self.assertEqual(labels, ("全量遍历（弹窗）", "最优搜索导出"))


class TestMultiSkillSegmentBoxHeight(unittest.TestCase):
    def test_zero_or_negative_returns_min(self):
        self.assertEqual(multi_skill_segment_box_height(0), MULTI_SKILL_SEGMENT_BOX_MIN_HEIGHT)
        self.assertEqual(multi_skill_segment_box_height(-5), MULTI_SKILL_SEGMENT_BOX_MIN_HEIGHT)

    def test_single_segment(self):
        expected = max(MULTI_SKILL_SEGMENT_BOX_MIN_HEIGHT, 1 * MULTI_SKILL_SEGMENT_ROW_HEIGHT + 8)
        self.assertEqual(multi_skill_segment_box_height(1), expected)

    def test_multi_segment_no_lower_limit(self):
        h = multi_skill_segment_box_height(10)
        self.assertGreaterEqual(h, MULTI_SKILL_SEGMENT_BOX_MIN_HEIGHT)
        self.assertEqual(h, 10 * MULTI_SKILL_SEGMENT_ROW_HEIGHT + 8)


if __name__ == "__main__":
    unittest.main()
