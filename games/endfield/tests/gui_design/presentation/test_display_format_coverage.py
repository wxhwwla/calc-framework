from __future__ import annotations

from gui_design.presentation.display.format import (
    evaluate_display_state,
    format_skill_multiplier_display_value,
    format_weapon_bonus_display_value,
    weapon_bonus_display_uses_percent,
)


class TestWeaponBonusDisplayUsesPercent:
    def test_flat_bonus_attr(self) -> None:
        assert weapon_bonus_display_uses_percent("附加攻击力+") is False

    def test_stat_attr(self) -> None:
        assert weapon_bonus_display_uses_percent("力量+") is False

    def test_integer_bonus(self) -> None:
        assert weapon_bonus_display_uses_percent("源石技艺") is False

    def test_attack_percent(self) -> None:
        assert weapon_bonus_display_uses_percent("攻击力+") is True

    def test_damage_percent(self) -> None:
        assert weapon_bonus_display_uses_percent("物理伤害+") is True
        assert weapon_bonus_display_uses_percent("属性伤害+") is True

    def test_charge_efficiency(self) -> None:
        assert weapon_bonus_display_uses_percent("充能效率+") is True

    def test_rate_percent(self) -> None:
        assert weapon_bonus_display_uses_percent("暴击率+") is True

    def test_unknown_fallback(self) -> None:
        assert weapon_bonus_display_uses_percent("未知属性+") is True


class TestFormatWeaponBonusDisplayValue:
    def test_integer_display(self) -> None:
        result = format_weapon_bonus_display_value(27.6, attr_name="附加攻击力+")
        assert result == "27"

    def test_percent_display_int(self) -> None:
        result = format_weapon_bonus_display_value(30, attr_name="攻击力+")
        assert result == "30%"

    def test_percent_display_float(self) -> None:
        result = format_weapon_bonus_display_value(27.6, attr_name="暴击率+")
        assert result == "27.6%"

    def test_non_numeric_raw(self) -> None:
        result = format_weapon_bonus_display_value("无", attr_name="攻击力+")
        assert result == "无"

    def test_is_first_skill_fallback(self) -> None:
        result = format_weapon_bonus_display_value(15, attr_name="附加攻击力+", is_first_skill=True)
        assert result == "15"


class TestFormatSkillMultiplierDisplayValue:
    def test_int(self) -> None:
        assert format_skill_multiplier_display_value(100) == "100%"

    def test_float(self) -> None:
        assert format_skill_multiplier_display_value(150.5) == "150.5%"

    def test_non_numeric(self) -> None:
        assert format_skill_multiplier_display_value("无") == "无"


class TestEvaluateDisplayState:
    def test_both_missing(self) -> None:
        state = evaluate_display_state(None, None)
        assert "请选择有效角色" in state["char_message"]
        assert "请选择有效武器" in state["weapon_message"]
        assert state["can_update_zone"] is False

    def test_char_missing(self) -> None:
        state = evaluate_display_state(None, {"名称": "剑"})
        assert "请选择有效角色" in state["char_message"]
        assert "请选择有效武器" not in state["weapon_message"]
        assert state["can_update_zone"] is False

    def test_weapon_missing(self) -> None:
        state = evaluate_display_state({"名称": "角色"}, None)
        assert "请选择有效武器" in state["weapon_message"]

    def test_both_present(self) -> None:
        state = evaluate_display_state({"名称": "角色"}, {"名称": "剑"})
        assert state["can_update_zone"] is True
