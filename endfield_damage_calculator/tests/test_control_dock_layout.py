#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""底栏布局高度辅助测试。"""

import unittest

from gui_design.gui_layout import (
    CONTROL_DOCK_COMPACT_BREAKPOINT,
    CONTROL_DOCK_INNER_COLUMN_COUNT,
    MULTI_SKILL_SEGMENT_BOX_MAX_HEIGHT,
    MULTI_SKILL_SEGMENT_BOX_MIN_HEIGHT,
    PRIMARY_ACTION_BUTTON_HEIGHT,
    SEARCH_ESTIMATE_BOX_HEIGHT,
    SEARCH_STATUS_BOX_HEIGHT,
    SEARCH_WORKERS_HINT_BOX_HEIGHT,
    SECONDARY_ACTION_BUTTON_HEIGHT,
    search_action_button_texts,
    hint_text_box_height,
    multi_skill_segment_box_height,
    should_use_compact_control_dock,
)
from gui_design.search_settings import format_parallel_workers_help, get_cpu_parallel_info


class TestControlDockLayout(unittest.TestCase):
    def test_dock_inner_column_count_is_three(self) -> None:
        self.assertEqual(CONTROL_DOCK_INNER_COLUMN_COUNT, 3)

    def test_segment_box_height_grows_with_row_count(self) -> None:
        one = multi_skill_segment_box_height(1)
        five = multi_skill_segment_box_height(5)
        self.assertLess(one, five)
        self.assertGreaterEqual(one, MULTI_SKILL_SEGMENT_BOX_MIN_HEIGHT)

    def test_segment_box_height_caps_at_max(self) -> None:
        many = multi_skill_segment_box_height(20)
        self.assertEqual(many, MULTI_SKILL_SEGMENT_BOX_MAX_HEIGHT)

    def test_estimate_box_height_is_two_lines(self) -> None:
        self.assertEqual(SEARCH_ESTIMATE_BOX_HEIGHT, hint_text_box_height(2))

    def test_workers_hint_box_height_fits_help_text(self) -> None:
        info = get_cpu_parallel_info(cpu_count=24)
        help_text = format_parallel_workers_help(info, selected_workers=23)
        line_count = help_text.count("\n") + 1
        self.assertGreaterEqual(SEARCH_WORKERS_HINT_BOX_HEIGHT, hint_text_box_height(line_count))

    def test_status_box_height_fits_two_line_progress(self) -> None:
        self.assertGreaterEqual(SEARCH_STATUS_BOX_HEIGHT, hint_text_box_height(2))

    def test_button_height_contract(self) -> None:
        self.assertGreater(PRIMARY_ACTION_BUTTON_HEIGHT, SECONDARY_ACTION_BUTTON_HEIGHT)
        self.assertGreaterEqual(SECONDARY_ACTION_BUTTON_HEIGHT, 30)

    def test_compact_layout_breakpoint_rule(self) -> None:
        self.assertTrue(should_use_compact_control_dock(CONTROL_DOCK_COMPACT_BREAKPOINT - 1))
        self.assertFalse(should_use_compact_control_dock(CONTROL_DOCK_COMPACT_BREAKPOINT))

    def test_search_button_texts_adapt_to_compact_mode(self) -> None:
        self.assertEqual(search_action_button_texts(compact=True), ("全量遍历", "MVP导出"))
        self.assertEqual(
            search_action_button_texts(compact=False),
            ("全量遍历（弹窗）", "MVP搜索导出"),
        )

    def test_place_multi_skill_section_builds_without_grid_propagate_error(self) -> None:
        """CTkScrollableFrame 不支持 grid_propagate(False)，放置段列表区不得崩溃。"""
        import customtkinter as ctk

        from gui_design.multi_skill_controls import place_multi_skill_section
        from tests.gui_fixtures import build_mock_app

        root = ctk.CTk()
        root.withdraw()
        try:
            parent = ctk.CTkFrame(root)
            app = build_mock_app(root=root)
            app._multi_skill_counts_body = None
            place_multi_skill_section(
                app,  # type: ignore[arg-type]
                parent,
                wrap_label=lambda _label, _container: None,
                schedule_confirm=lambda **_kw: None,
            )
            self.assertIsNotNone(app._multi_skill_counts_body)
            self.assertIsNotNone(getattr(app, "_multi_skill_segment_box", None))
        finally:
            root.destroy()


if __name__ == "__main__":
    unittest.main()
