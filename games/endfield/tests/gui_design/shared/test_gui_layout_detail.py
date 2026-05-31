# SPDX-License-Identifier: AGPL-3.0
from __future__ import annotations

from games.endfield.gui_design.layout.gui_layout import (
    control_dock_layout_needs_update,
    hint_text_box_height,
    multi_skill_segment_box_height,
    search_action_button_texts,
    should_use_compact_control_dock,
)


class TestHintTextBoxHeight:
    def test_positive_lines(self) -> None:
        assert hint_text_box_height(3) == 3 * 18 + 10

    def test_zero_lines(self) -> None:
        assert hint_text_box_height(0) == 1 * 18 + 10

    def test_negative_lines(self) -> None:
        assert hint_text_box_height(-1) == 1 * 18 + 10


class TestShouldUseCompactControlDock:
    def test_compact_below_breakpoint(self) -> None:
        assert should_use_compact_control_dock(1000) is True

    def test_not_compact_at_breakpoint(self) -> None:
        assert should_use_compact_control_dock(1480) is False

    def test_not_compact_above(self) -> None:
        assert should_use_compact_control_dock(2000) is False


class TestControlDockLayoutNeedsUpdate:
    def test_changed_width(self) -> None:
        assert control_dock_layout_needs_update(1000, last_width=500, last_compact=False) is True

    def test_changed_compact(self) -> None:
        assert control_dock_layout_needs_update(1000, last_width=1000, last_compact=False) is True

    def test_no_change(self) -> None:
        assert control_dock_layout_needs_update(1000, last_width=1000, last_compact=True) is False


class TestSearchActionButtonTexts:
    def test_compact(self) -> None:
        texts = search_action_button_texts(compact=True)
        assert texts[0] == "全量遍历"

    def test_not_compact(self) -> None:
        texts = search_action_button_texts(compact=False)
        assert "弹窗" in texts[0]


class TestMultiSkillSegmentBoxHeight:
    def test_positive_count(self) -> None:
        h = multi_skill_segment_box_height(5)
        assert h >= 36

    def test_zero_count(self) -> None:
        h = multi_skill_segment_box_height(0)
        assert h == 36

    def test_negative_count(self) -> None:
        h = multi_skill_segment_box_height(-1)
        assert h == 36
