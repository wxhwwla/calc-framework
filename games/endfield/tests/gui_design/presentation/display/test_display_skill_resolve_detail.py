# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
from __future__ import annotations

from typing import Any

from calc_framework.ui.i18n import set_locale
from games.endfield.gui.presentation.display.skill_resolve import (
    resolve_selected_skill_for_damage,
)


def setup_module() -> None:
    set_locale("zh-CN")


def _make_char_data() -> dict[str, Any]:
    return {
        "战技倍率": [[100, 110, 120]],
        "连携技倍率": [[200, 220]],
        "终结技倍率": [[300]],
        "战技伤害类型": [{"段1": "物理"}],
    }


class TestResolveSelectedSkillForDamage:
    def test_skill_1_selected(self) -> None:
        result = resolve_selected_skill_for_damage(_make_char_data(), skill_1_level=1)

        assert result.label == "战技 等级1 第1段"

        assert result.skill_type == "战技"

    def test_skill_2_selected(self) -> None:
        result = resolve_selected_skill_for_damage(_make_char_data(), skill_2_level=1)

        assert result.label == "连携技 等级1 第1段"

    def test_skill_3_selected(self) -> None:
        result = resolve_selected_skill_for_damage(_make_char_data(), skill_3_level=1)

        assert result.label == "终结技 等级1 第1段"

    def test_no_skill_selected(self) -> None:
        result = resolve_selected_skill_for_damage(_make_char_data())

        assert "默认" in result.label

    def test_level_too_high_falls_through(self) -> None:
        result = resolve_selected_skill_for_damage(_make_char_data(), skill_1_level=99)

        assert "默认" in result.label

    def test_multiplier_conversion(self) -> None:
        result = resolve_selected_skill_for_damage(_make_char_data(), skill_1_level=1)

        assert result.multiplier == 1.0
