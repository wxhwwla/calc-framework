from __future__ import annotations

from unittest.mock import patch

from gui_design.shared.weapon_display_text import (
    extract_effect_display_name,
    format_weapon_skill_slider_value,
    format_weapon_skill_title,
    split_special_skill_display,
)


class TestFormatWeaponSkillTitle:
    def test_with_attr_name(self) -> None:
        assert "前缀：智识+" in format_weapon_skill_title("前缀", "智识+")

    def test_with_blank_attr(self) -> None:
        assert "前缀：无" in format_weapon_skill_title("前缀", "")
        assert "前缀：无" in format_weapon_skill_title("前缀", "  ")

    def test_with_empty(self) -> None:
        assert "：无" in format_weapon_skill_title("")


class TestFormatWeaponSkillSliderValue:
    def test_inactive(self) -> None:
        assert format_weapon_skill_slider_value(active=False) == "0"

    def test_active(self) -> None:
        assert format_weapon_skill_slider_value(active=True, level=5) == "5"

    def test_active_default_level(self) -> None:
        assert format_weapon_skill_slider_value(active=True) == "0"


class TestExtractEffectDisplayName:
    def test_empty_string(self) -> None:
        assert extract_effect_display_name("") == ""

    def test_received_pattern(self) -> None:
        name = "目标受到的 攻击力+"
        result = extract_effect_display_name(name)
        assert result == "攻击力+"

    def test_prefix_target_received(self) -> None:
        name = "目标受到的防御力+"
        result = extract_effect_display_name(name)
        assert result == "防御力+"

    def test_prefix_equipped(self) -> None:
        name = "装备者获得的攻击力+"
        result = extract_effect_display_name(name)
        assert result == "攻击力+"

    def test_prefix_equipped_no_plus(self) -> None:
        name = "装备者生命值+"
        result = extract_effect_display_name(name)
        assert result == "生命值+"

    def test_simple_effect_name(self) -> None:
        name = "攻击力+"
        result = extract_effect_display_name(name)
        assert result == "攻击力+"

    def test_simple_effect_too_long(self) -> None:
        name = "A" * 20 + "+"
        result = extract_effect_display_name(name)
        assert result == name

    def test_effect_name_match_fallback(self) -> None:
        name = "击败敌人提高暴击率+"
        result = extract_effect_display_name(name)
        assert "+" in result

    def test_no_match_returns_raw(self) -> None:
        name = "一些描述且不匹配"
        result = extract_effect_display_name(name)
        assert result == name

    def test_received_middle_marker(self) -> None:
        name = "获得时攻击力+"
        result = extract_effect_display_name(name)
        assert "+" in result

    def test_empty_after_strip(self) -> None:
        assert extract_effect_display_name("  ") == ""


class TestSplitSpecialSkillDisplay:
    def test_empty_name(self) -> None:
        assert split_special_skill_display("") == ("", "")

    def test_no_effect(self) -> None:
        result = split_special_skill_display("无效果描述")
        assert result[1] == "无效果描述"

    def test_name_equals_effect(self) -> None:
        name = "攻击力+"
        result = split_special_skill_display(name)
        assert result == ("", "攻击力+")

    def test_effect_not_in_name(self) -> None:
        name = "描述文字 攻击力+"
        with patch("gui_design.shared.weapon_display_text.extract_effect_display_name", return_value="防御力+"):
            result = split_special_skill_display(name)
            assert result == ("", "防御力+")

    def test_condition_extraction(self) -> None:
        name = "装备者获得攻击力+"
        result = split_special_skill_display(name)
        assert result[1] == "获得攻击力+"

    def test_marker_trimming(self) -> None:
        name = "受到致命伤害时获得攻击力+"
        result = split_special_skill_display(name)
        assert "攻击力+" in result[1]

    def test_known_prefix_condition_empty(self) -> None:
        name = "装备者攻击力+"
        result = split_special_skill_display(name)
        assert result == ("", "攻击力+")

