# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
from __future__ import annotations

from typing import Any

from games.endfield.gui.presentation.display.character import (
    build_character_attribute_lines,
    build_character_skill_damage_type_lines,
    build_weapon_attribute_lines,
)


def _make_char_data() -> dict[str, Any]:
    return {
        "力量": [10, 20, 30],
        "基础攻击力": 100,
        "战技倍率": [[100]],
        "战技伤害类型": [{"段1": "物理"}],
    }


def _make_weapon_data() -> dict[str, Any]:
    return {
        "基础攻击力": [100, 110, 120, 130, 140, 150, 160, 170, 180],
        "normal_skills": [
            {"zone": 1, "effect": "攻击力+", "curve": [10.0, 15.0, 20.0]},
        ],
        "special_skills": [],
    }


class TestBuildCharacterSkillDamageTypeLines:
    def test_with_char_data(self) -> None:
        lines = build_character_skill_damage_type_lines(_make_char_data(), skill_1_level=1)

        assert len(lines) > 0

    def test_no_data(self) -> None:
        lines = build_character_skill_damage_type_lines({}, skill_1_level=1)

        assert lines == []


class TestBuildCharacterAttributeLines:
    def test_with_level(self) -> None:
        lines = build_character_attribute_lines(_make_char_data(), level=1)

        assert len(lines) > 0

    def test_empty(self) -> None:
        lines = build_character_attribute_lines({}, level=1)

        assert lines == []


class TestBuildWeaponAttributeLines:
    def test_with_weapon_data(self) -> None:
        lines = build_weapon_attribute_lines(_make_weapon_data(), 1)

        assert len(lines) > 0

    def test_null_weapon(self) -> None:
        lines = build_weapon_attribute_lines(None, 1)

        assert lines == []
