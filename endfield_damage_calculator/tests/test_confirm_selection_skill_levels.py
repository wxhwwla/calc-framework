#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""确认选择时角色属性列应传入技能等级。"""

import json
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from gui_design.property_display import confirm_selection


_CHARACTERS_JSON = (
    Path(__file__).resolve().parent.parent
    / "character_weapon_equipment"
    / "character_data"
    / "characters.json"
)


def _load_by_name(name: str) -> dict:
    with _CHARACTERS_JSON.open(encoding="utf-8") as f:
        data = json.load(f)
    for item in data:
        if item.get("名称") == name:
            return item
    raise KeyError(name)


class TestConfirmSelectionSkillLevels(unittest.TestCase):
    @patch("gui_design.property_display.build_character_attribute_lines")
    @patch("gui_design.property_display._render_placeholder")
    @patch("gui_design.property_display._render_lines")
    def test_confirm_passes_skill_levels_from_character_panel(
        self,
        _render_lines,
        _render_placeholder,
        build_lines,
    ):
        char = _load_by_name("秋栗")
        char_panel = MagicMock()
        char_panel.get_selected_data.return_value = char
        char_panel.get_level.return_value = 1
        char_panel.get_trust_level.return_value = 0
        char_panel.get_skill_1_level.return_value = 5
        char_panel.get_skill_2_level.return_value = 3
        char_panel.get_skill_3_level.return_value = 2

        weapon_panel = MagicMock()
        weapon_panel.get_selected_data.return_value = None

        char_scroll = MagicMock()
        char_scroll.winfo_children.return_value = []
        weapon_scroll = MagicMock()
        weapon_scroll.winfo_children.return_value = []
        right_scroll = MagicMock()
        right_scroll.winfo_children.return_value = []

        confirm_selection(
            char_scroll,
            weapon_scroll,
            right_scroll,
            char_panel,
            weapon_panel,
            MagicMock(),
            MagicMock(),
        )

        build_lines.assert_called_once_with(
            char,
            1,
            skill_1_level=5,
            skill_2_level=3,
            skill_3_level=2,
        )


if __name__ == "__main__":
    unittest.main()
