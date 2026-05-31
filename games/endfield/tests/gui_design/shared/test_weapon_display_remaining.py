# SPDX-License-Identifier: AGPL-3.0
from __future__ import annotations

from unittest.mock import patch

from games.endfield.gui_design.shared.weapon_display_text import (
    split_special_skill_display,
)


class TestSplitSpecialSkillDisplayRemaining:
    def test_effect_not_found_returns_effect(self) -> None:
        with patch("games.endfield.gui_design.shared.weapon_display_text.extract_effect_display_name", return_value="攻击力+"):
            result = split_special_skill_display("一些描述攻击力+")
            assert result[1] == "攻击力+"

    def test_condition_trimmed_with_marker(self) -> None:
        result = split_special_skill_display("使用战技时增加攻击力+")
        assert "攻击力+" in result[1]
