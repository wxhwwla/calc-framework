# SPDX-License-Identifier: AGPL-3.0
"""覆盖 multiplicative_zones 所有模块。"""

from __future__ import annotations

from typing import Any

import pytest
from games.endfield.calc.multiplicative_zones import (
    AbilityBonusZone,
    AttributeMultiplierZone,
    AttributeZoneManager,
    BaseZone,
    DefenseReductionZone,
    FinalAttackZone,
    ZoneManager,
    calculate_ability_bonus,
    calculate_ability_bonus_with_details,
    calculate_attribute_zones,
    calculate_attribute_zones_with_details,
    calculate_final_attack,
    calculate_final_attack_with_details,
)
from games.endfield.calc.multiplicative_zones._attribute_zone_bonus import compute_attr_weapon_bonus

# ── base_zone.py ─────────────────────────────────────────────────────────


class _ConcreteZone(BaseZone):
    """用于测试 BaseZone 抽象类的具体实现。"""

    def calculate(self) -> float:
        return 42.0


class TestBaseZone:
    """BaseZone 抽象类。"""

    def test_init(self) -> None:
        z = _ConcreteZone("测试", "测试乘区")
        assert z.name == "测试"
        assert z.description == "测试乘区"
        assert z.enabled is True

    def test_is_enabled(self) -> None:
        z = _ConcreteZone("测试")
        assert z.is_enabled() is True

    def test_enable_disable(self) -> None:
        z = _ConcreteZone("测试")
        z.disable()
        assert z.is_enabled() is False
        z.enable()
        assert z.is_enabled() is True

    def test_get_params(self) -> None:
        z = _ConcreteZone("测试")
        z.set_params(a=1, b=2)
        params = z.get_params()
        assert params == {"a": 1, "b": 2}

    def test_calculate(self) -> None:
        z = _ConcreteZone("测试")
        assert z.calculate() == 42.0


# ── DefenseReductionZone ─────────────────────────────────────────────────


class TestDefenseReductionZone:
    """DefenseReductionZone 基础功能。"""

    def test_init(self) -> None:
        z = DefenseReductionZone()
        assert z.name == "敌方防御减伤区"
        assert "防御" in z.description

    def test_calculate_default(self) -> None:
        z = DefenseReductionZone()
        result = z.calculate()
        assert result == 100.0 / (100.0 + 100.0)  # DEFAULT_DEFENSE=100

    def test_calculate_with_custom_defense(self) -> None:
        z = DefenseReductionZone()
        z.set_params(defense=200.0)
        result = z.calculate()
        assert result == 100.0 / (100.0 + 200.0)

    def test_calculate_zero(self) -> None:
        z = DefenseReductionZone()
        z.set_params(defense=0.0)
        result = z.calculate()
        assert result == 1.0


# ── AbilityBonusZone ─────────────────────────────────────────────────────


class TestAbilityBonusZone:
    """AbilityBonusZone。"""

    def test_init(self) -> None:
        z = AbilityBonusZone()
        assert z.name == "能力值加成"

    def test_calculate_default(self) -> None:
        z = AbilityBonusZone()
        assert z.calculate() == 0.0

    def test_calculate_with_values(self) -> None:
        z = AbilityBonusZone()
        z.set_params(main_value=100.0, sub_value=80.0)
        # main_effective = int(100 * 1.0) = 100, sub_effective = int(80 * 1.0) = 80
        # 100 * 0.005 + 80 * 0.002 = 0.5 + 0.16 = 0.66
        assert z.calculate() == 100 * 0.005 + 80 * 0.002


# ── AttributeMultiplierZone ──────────────────────────────────────────────


class TestAttributeMultiplierZone:
    """AttributeMultiplierZone。"""

    def test_init(self) -> None:
        z = AttributeMultiplierZone("力量", 100.0)
        assert z.attribute_name == "力量"
        assert z.name == "力量乘区"

    def test_calculate_default(self) -> None:
        z = AttributeMultiplierZone("敏捷")
        assert z.calculate() == 0.0

    def test_calculate_with_value(self) -> None:
        z = AttributeMultiplierZone("智识", 200.0)
        assert z.calculate() == 200.0


# ── FinalAttackZone ──────────────────────────────────────────────────────


class TestFinalAttackZone:
    """FinalAttackZone / calculate_final_attack。"""

    def test_init(self) -> None:
        z = FinalAttackZone()
        assert z.name == "最终攻击力"

    def test_calculate_default(self) -> None:
        z = FinalAttackZone()
        assert z.calculate() == 0.0

    def test_calculate_with_params(self) -> None:
        z = FinalAttackZone()
        z.set_params(base_attack=1000.0, ability_bonus=0.5)
        assert z.calculate() == 1500.0

    def test_calculate_final_attack_function(self) -> None:
        assert calculate_final_attack(1000.0, 0.5) == 1500.0
        assert calculate_final_attack(500.0, 0.0) == 500.0
        assert calculate_final_attack(0.0, 1.0) == 0.0


# ── calculate_ability_bonus ──────────────────────────────────────────────


class TestCalculateAbilityBonus:
    """calculate_ability_bonus 快捷函数。"""

    _MINIMAL_CHAR: dict[str, Any] = {
        "力量": [100.0, 101.0, 102.0],
        "敏捷": [80.0, 81.0, 82.0],
        "主能力": "力量",
        "副能力": "敏捷",
    }

    def test_none_character(self) -> None:
        assert calculate_ability_bonus(None) == 0.0

    def test_no_weapon_basic(self) -> None:
        bonus = calculate_ability_bonus(self._MINIMAL_CHAR, level=1)
        # 主能力 100 * 0.005 + 副能力 80 * 0.002
        assert bonus == 100.0 * 0.005 + 80.0 * 0.002

    def test_with_trust_level(self) -> None:
        bonus = calculate_ability_bonus(self._MINIMAL_CHAR, level=1, trust_level=4)
        # 主能力 100 + 60 信赖 * 0.005 + 副能力 80 * 0.002
        assert bonus == (100.0 + 60.0) * 0.005 + 80.0 * 0.002


# ── calculate_ability_bonus_with_details ─────────────────────────────────


class TestCalculateAbilityBonusWithDetails:
    """calculate_ability_bonus_with_details。"""

    _CHAR: dict[str, Any] = {
        "力量": [100.0],
        "敏捷": [80.0],
        "主能力": "力量",
        "副能力": "敏捷",
    }

    def test_none_character(self) -> None:
        result = calculate_ability_bonus_with_details(None)
        assert result["bonus"] == 0.0
        assert result["main_attr"] == ""

    def test_basic(self) -> None:
        result = calculate_ability_bonus_with_details(self._CHAR, level=1)
        assert result["main_attr"] == "力量"
        assert result["sub_attr"] == "敏捷"
        assert result["main_base"] == 100.0
        assert result["sub_base"] == 80.0
        assert result["bonus"] == 100.0 * 0.005 + 80.0 * 0.002


# ── calculate_attribute_zones ───────────────────────────────────────────


class TestCalculateAttributeZones:
    """calculate_attribute_zones / calculate_attribute_zones_with_details。"""

    _CHAR: dict[str, Any] = {
        "力量": [100.0, 110.0],
        "敏捷": [80.0, 82.0],
        "智识": [60.0, 61.0],
        "意志": [40.0, 41.0],
        "主能力": "力量",
        "副能力": "敏捷",
    }

    def test_basic(self) -> None:
        result = calculate_attribute_zones(self._CHAR, None, level=1)
        assert "力量" in result
        assert "敏捷" in result
        assert "智识" in result
        assert "意志" in result
        assert result["力量"] == 100.0
        assert result["意志"] == 40.0

    def test_none_character(self) -> None:
        result = calculate_attribute_zones(None, None)
        for attr in ("力量", "敏捷", "智识", "意志"):
            assert result[attr] == 0.0

    def test_with_details(self) -> None:
        result = calculate_attribute_zones_with_details(self._CHAR, None, level=2)
        assert len(result) == 4
        assert result["力量"]["total"] == 110.0
        assert result["敏捷"]["total"] == 82.0


# ── calculate_final_attack_with_details ──────────────────────────────────


class TestCalculateFinalAttackWithDetails:
    """calculate_final_attack_with_details。"""

    _CHAR: dict[str, Any] = {
        "力量": [100.0],
        "攻击力": [500.0],
        "主能力": "力量",
        "副能力": "敏捷",
    }

    def test_none_character(self) -> None:
        result = calculate_final_attack_with_details(None)
        assert result["final_attack"] == 0.0

    def test_basic_no_weapon(self) -> None:
        result = calculate_final_attack_with_details(self._CHAR, char_level=1)
        assert "final_attack" in result
        assert "ability_bonus" in result
        assert "base_attack" in result


# ── ZoneManager ──────────────────────────────────────────────────────────


class TestZoneManager:
    """ZoneManager 增删查改。"""

    def test_empty(self) -> None:
        mgr = ZoneManager()
        assert len(mgr) == 0
        assert mgr.calculate_total() == 1.0

    def test_add_and_calculate(self) -> None:
        mgr = ZoneManager()
        z = _ConcreteZone("test")
        mgr.add_zone(z)
        assert len(mgr) == 1
        assert mgr.calculate_total() == 42.0

    def test_remove_zone(self) -> None:
        mgr = ZoneManager()
        mgr.add_zone(_ConcreteZone("a"))
        mgr.add_zone(_ConcreteZone("b"))
        assert mgr.remove_zone("a") is True
        assert mgr.remove_zone("nonexistent") is False

    def test_get_zone(self) -> None:
        mgr = ZoneManager()
        z = _ConcreteZone("target")
        mgr.add_zone(z)
        assert mgr.get_zone("target") is z
        assert mgr.get_zone("missing") is None

    def test_get_all_zones(self) -> None:
        mgr = ZoneManager()
        z1 = _ConcreteZone("a")
        z2 = _ConcreteZone("b")
        mgr.add_zone(z1)
        mgr.add_zone(z2)
        zones = mgr.get_all_zones()
        assert len(zones) == 2
        assert z1 in zones
        assert z2 in zones

    def test_enable_disable_zone(self) -> None:
        mgr = ZoneManager()
        z = _ConcreteZone("x")
        mgr.add_zone(z)
        assert mgr.disable_zone("x") is True
        assert z.is_enabled() is False
        assert mgr.disable_zone("nonexistent") is False

        assert mgr.enable_zone("x") is True
        assert z.is_enabled() is True
        assert mgr.enable_zone("nonexistent") is False

    def test_calculate_disabled_returns_1(self) -> None:
        mgr = ZoneManager()
        z = _ConcreteZone("x")
        mgr.add_zone(z)
        mgr.disable_zone("x")
        assert mgr.calculate_total() == 1.0

    def test_calculate_zone(self) -> None:
        mgr = ZoneManager()
        z = _ConcreteZone("x")
        mgr.add_zone(z)
        assert mgr.calculate_zone("x") == 42.0
        mgr.disable_zone("x")
        assert mgr.calculate_zone("x") is None
        assert mgr.calculate_zone("missing") is None

    def test_calculate_all(self) -> None:
        mgr = ZoneManager()
        z1 = _ConcreteZone("a")
        z2 = _ConcreteZone("b")
        mgr.add_zone(z1)
        mgr.add_zone(z2)
        mgr.disable_zone("b")
        results = mgr.calculate_all()
        assert results["a"] == 42.0
        assert results["b"] == 1.0

    def test_enable_disable_all(self) -> None:
        mgr = ZoneManager()
        mgr.add_zone(_ConcreteZone("a"))
        mgr.add_zone(_ConcreteZone("b"))
        mgr.disable_all()
        assert all(not z.is_enabled() for z in mgr.get_all_zones())
        mgr.enable_all()
        assert all(z.is_enabled() for z in mgr.get_all_zones())

    def test_clear(self) -> None:
        mgr = ZoneManager()
        mgr.add_zone(_ConcreteZone("a"))
        mgr.clear()
        assert len(mgr) == 0

    def test_repr(self) -> None:
        mgr = ZoneManager()
        mgr.add_zone(_ConcreteZone("a"))
        r = repr(mgr)
        assert "ZoneManager" in r
        assert "1 zones" in r


# ── AttributeZoneManager ─────────────────────────────────────────────────


class TestAttributeZoneManager:
    """AttributeZoneManager。"""

    _CHAR: dict[str, Any] = {
        "力量": [100.0, 110.0],
        "敏捷": [80.0, 82.0],
        "智识": [60.0, 61.0],
        "意志": [40.0, 41.0],
        "主能力": "力量",
        "副能力": "敏捷",
    }

    def test_init(self) -> None:
        mgr = AttributeZoneManager()
        assert len(mgr._zones) == 4

    def test_setup_from_data_none(self) -> None:
        mgr = AttributeZoneManager()
        mgr.setup_from_data(None, None)
        for z in mgr._zones.values():
            assert z.calculate() == 0.0

    def test_setup_from_data_with_character(self) -> None:
        mgr = AttributeZoneManager()
        mgr.setup_from_data(self._CHAR, None, level=1)
        assert mgr._zones["力量"].calculate() == 100.0
        assert mgr._zones["敏捷"].calculate() == 80.0

    def test_calculate_all(self) -> None:
        mgr = AttributeZoneManager()
        mgr.setup_from_data(self._CHAR, None, level=1)
        results = mgr.calculate_all()
        assert results["力量"] == 100.0
        assert results["敏捷"] == 80.0


# ── _attribute_zone_bonus.py ───────────────────────────────────────────


class TestComputeAttrWeaponBonus:
    """compute_attr_weapon_bonus。"""

    def test_no_weapon(self) -> None:
        mgr = AttributeZoneManager()
        flat, pct = compute_attr_weapon_bonus(
            attr="力量",
            attr_is_main=True,
            attr_is_sub=False,
            weapon=None,
            manager=mgr,
            sa1_name="",
            sa1_level=1,
            sa2_name="",
            sa2_level=1,
            sa3_name="",
            sa3_level=0,
            ws_name="",
            ws_level=1,
            ws_stack=1,
            ws2_name="",
            ws2_level=1,
            ws2_stack=1,
            main_attr="力量",
            sub_attr="敏捷",
            trust_level=0,
        )
        assert flat == 0.0
        assert pct == 0.0


# ── ability_bonus_calc 内部函数 ──────────────────────────────────────────


class TestAbilityBonusInternal:
    """_get_weapon_bonus / _get_bonus_from_normal_skills / _warn_if_legacy_skill_kwargs_used。"""

    def test_get_weapon_bonus_list_out_of_range(self) -> None:
        from games.endfield.calc.multiplicative_zones.ability_bonus_calc import _get_weapon_bonus

        # level 超出列表范围
        assert _get_weapon_bonus([10.0, 20.0], level=99) == 0.0

    def test_get_weapon_bonus_non_numeric_in_list(self) -> None:
        from games.endfield.calc.multiplicative_zones.ability_bonus_calc import _get_weapon_bonus

        # list 中包含非数值元素
        assert _get_weapon_bonus(["abc", 10.0]) == 0.0

    def test_get_weapon_bonus_none(self) -> None:
        from games.endfield.calc.multiplicative_zones.ability_bonus_calc import _get_weapon_bonus

        assert _get_weapon_bonus(None) == 0.0

    def test_get_weapon_bonus_string(self) -> None:
        from games.endfield.calc.multiplicative_zones.ability_bonus_calc import _get_weapon_bonus

        assert _get_weapon_bonus("10.0") == 0.0

    def test_get_bonus_from_normal_skills_found(self) -> None:
        from games.endfield.calc.multiplicative_zones.ability_bonus_calc import _get_bonus_from_normal_skills

        weapon = {"normal_skills": [{"effect": "攻击力+", "curve": [5.0, 10.0]}]}
        assert _get_bonus_from_normal_skills(weapon, "攻击力+") == 5.0
        assert _get_bonus_from_normal_skills(weapon, "攻击力+", level=2) == 10.0

    def test_get_bonus_from_normal_skills_not_found(self) -> None:
        from games.endfield.calc.multiplicative_zones.ability_bonus_calc import _get_bonus_from_normal_skills

        weapon = {"normal_skills": [{"effect": "敏捷+", "curve": [5.0]}]}
        assert _get_bonus_from_normal_skills(weapon, "攻击力+") == 0.0

    def test_get_bonus_from_normal_skills_empty(self) -> None:
        from games.endfield.calc.multiplicative_zones.ability_bonus_calc import _get_bonus_from_normal_skills

        assert _get_bonus_from_normal_skills({}, "攻击力+") == 0.0

    def test_legacy_warning(self) -> None:
        """仅使用旧参数名 sa* 应触发 DeprecationWarning。"""
        import warnings

        from games.endfield.calc.multiplicative_zones.ability_bonus_calc import (
            _warn_if_legacy_skill_kwargs_used,
        )

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            _warn_if_legacy_skill_kwargs_used(
                sa1_name="敏捷+",
                sa2_name="",
                sa3_name="",
                ws_name="",
                ws2_name="",
                normal_skill_1_name="",
                normal_skill_2_name="",
                normal_skill_3_name="",
                special_skill_1_name="",
                special_skill_2_name="",
            )
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "sa*/ws* 已弃用" in str(w[0].message)

    def test_legacy_no_warning_when_new_used(self) -> None:
        """新旧参数同时使用时不触发告警。"""
        import warnings

        from games.endfield.calc.multiplicative_zones.ability_bonus_calc import (
            _warn_if_legacy_skill_kwargs_used,
        )

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            _warn_if_legacy_skill_kwargs_used(
                sa1_name="敏捷+",
                sa2_name="",
                sa3_name="",
                ws_name="",
                ws2_name="",
                normal_skill_1_name="敏捷+",
                normal_skill_2_name="",
                normal_skill_3_name="",
                special_skill_1_name="",
                special_skill_2_name="",
            )
            assert len(w) == 0

    def test_legacy_no_warning_no_legacy(self) -> None:
        """仅使用新参数名时不触发告警。"""
        import warnings

        from games.endfield.calc.multiplicative_zones.ability_bonus_calc import (
            _warn_if_legacy_skill_kwargs_used,
        )

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            _warn_if_legacy_skill_kwargs_used(
                sa1_name="",
                sa2_name="",
                sa3_name="",
                ws_name="",
                ws2_name="",
                normal_skill_1_name="敏捷+",
                normal_skill_2_name="",
                normal_skill_3_name="",
                special_skill_1_name="",
                special_skill_2_name="",
            )
            assert len(w) == 0


# ── calculate_ability_bonus 武器加成全覆盖 ─────────────────────────────


class TestCalculateAbilityBonusWeapon:
    """calculate_ability_bonus 武器各种 effect 分类测试。"""

    _CHAR: dict[str, Any] = {
        "力量": [100.0],
        "敏捷": [80.0],
        "主能力": "力量",
        "副能力": "敏捷",
    }

    def test_weapon_main_flat_via_normal_skill(self) -> None:
        """武器 normal_skills 携带 主能力值+。"""
        weapon = {"normal_skills": [{"effect": "主能力值+", "curve": [20.0]}]}
        bonus = calculate_ability_bonus(self._CHAR, weapon, level=1)
        expected = int(100.0 + 20.0) * 0.005 + int(80.0) * 0.002
        assert bonus == expected

    def test_weapon_sub_flat_via_normal_skill(self) -> None:
        """武器 normal_skills 携带 副能力值+。"""
        weapon = {"normal_skills": [{"effect": "副能力值+", "curve": [10.0]}]}
        bonus = calculate_ability_bonus(self._CHAR, weapon, level=1)
        expected = int(100.0) * 0.005 + int(80.0 + 10.0) * 0.002
        assert bonus == expected

    def test_weapon_main_pct_via_normal_skill(self) -> None:
        """武器 normal_skills 携带 主能力+（百分比）。"""
        weapon = {"normal_skills": [{"effect": "主能力+", "curve": [10.0]}]}
        bonus = calculate_ability_bonus(self._CHAR, weapon, level=1)
        # main_effective = int(100 * (1 + 10/100)) = 110
        expected = int(100.0 * 1.1) * 0.005 + int(80.0) * 0.002
        assert bonus == expected

    def test_weapon_sub_pct_via_normal_skill(self) -> None:
        """武器 normal_skills 携带 副能力+（百分比）。"""
        weapon = {"normal_skills": [{"effect": "副能力+", "curve": [5.0]}]}
        bonus = calculate_ability_bonus(self._CHAR, weapon, level=1)
        expected = int(100.0) * 0.005 + int(80.0 * 1.05) * 0.002
        assert bonus == expected

    def test_weapon_both_pct_via_normal_skill(self) -> None:
        """武器 normal_skills 携带 全能力+（百分比）。"""
        weapon = {"normal_skills": [{"effect": "全能力+", "curve": [10.0]}]}
        bonus = calculate_ability_bonus(self._CHAR, weapon, level=1)
        expected = int(100.0 * 1.1) * 0.005 + int(80.0 * 1.1) * 0.002
        assert bonus == expected

    def test_weapon_direct_attr_key(self) -> None:
        """武器直接属性键（向后兼容）。"""
        weapon = {"力量+": [15.0]}
        bonus = calculate_ability_bonus(self._CHAR, weapon, level=1)
        expected = int(100.0 + 15.0) * 0.005 + int(80.0) * 0.002
        assert bonus == expected

    def test_weapon_non_dict_skill_skipped(self) -> None:
        """normal_skills 中的非 dict 项应跳过。"""
        weapon = {"normal_skills": ["not_a_dict", {"effect": "主能力值+", "curve": [10.0]}]}
        bonus = calculate_ability_bonus(self._CHAR, weapon, level=1)
        expected = int(100.0 + 10.0) * 0.005 + int(80.0) * 0.002
        assert bonus == expected

    def test_weapon_unknown_category_skipped(self) -> None:
        """未知 effect 分类应跳过。"""
        weapon = {"normal_skills": [{"effect": "未知效果+", "curve": [99.0]}]}
        bonus = calculate_ability_bonus(self._CHAR, weapon, level=1)
        expected = int(100.0) * 0.005 + int(80.0) * 0.002
        assert bonus == expected

    def test_weapon_sa3_skipped_when_level_zero(self) -> None:
        """sa3 且 sa3_level==0 时应跳过。"""
        weapon = {"normal_skills": [{"effect": "主能力值+", "curve": [99.0]}]}
        bonus = calculate_ability_bonus(
            self._CHAR,
            weapon,
            level=1,
            sa1_name="",
            sa2_name="",
            sa3_name="主能力值+",
            sa3_level=0,
        )
        # 因 sa3_name=="主能力值+" 且 sa3_level==0，应跳过
        expected = int(100.0) * 0.005 + int(80.0) * 0.002
        assert bonus == expected

    def test_weapon_sa3_not_skipped_when_level_nonzero(self) -> None:
        """sa3 且 sa3_level>0 时不跳过。"""
        weapon = {"normal_skills": [{"effect": "主能力值+", "curve": [30.0]}]}
        bonus = calculate_ability_bonus(
            self._CHAR,
            weapon,
            level=1,
            sa1_name="",
            sa2_name="",
            sa3_name="主能力值+",
            sa3_level=3,
        )
        # 使用 sa3_level=3，curve 只有 [30.0]，level_index=2，超出范围
        expected = int(100.0 + 0.0) * 0.005 + int(80.0) * 0.002
        assert bonus == expected

    def test_equipment_stat_bonus(self) -> None:
        """equipment_stat_bonus 应累加。"""
        bonus = calculate_ability_bonus(
            self._CHAR,
            level=1,
            equipment_stat_bonus={"力量": 50.0, "敏捷": 30.0},
        )
        expected = int(100.0 + 50.0) * 0.005 + int(80.0 + 30.0) * 0.002
        assert bonus == expected

    def test_equipment_stat_bonus_partial(self) -> None:
        """equipment_stat_bonus 只包含主能力。"""
        bonus = calculate_ability_bonus(
            self._CHAR,
            level=1,
            equipment_stat_bonus={"力量": 50.0},
        )
        expected = int(100.0 + 50.0) * 0.005 + int(80.0) * 0.002
        assert bonus == expected

    def test_character_no_main_attr(self) -> None:
        """角色无主能力定义时返回 0。"""
        char: dict[str, Any] = {"力量": [100.0], "主能力": "", "副能力": ""}
        bonus = calculate_ability_bonus(char, level=1)
        assert bonus == 0.0

    def test_character_attr_out_of_range(self) -> None:
        """等级超出属性列表范围。"""
        char: dict[str, Any] = {
            "力量": [100.0],
            "敏捷": [80.0],
            "主能力": "力量",
            "副能力": "敏捷",
        }
        bonus = calculate_ability_bonus(char, level=99)
        assert bonus == 0.0

    def test_direct_attr_key_bonus_attrs_empty(self) -> None:
        """武器没有以+结尾的属性键。"""
        weapon: dict[str, Any] = {"基础攻击力": [100.0]}
        bonus = calculate_ability_bonus(self._CHAR, weapon, level=1)
        expected = int(100.0) * 0.005 + int(80.0) * 0.002
        assert bonus == expected

    def test_trust_level_out_of_range(self) -> None:
        """trust_level 超出范围时不应出错。"""
        bonus = calculate_ability_bonus(self._CHAR, level=1, trust_level=99)
        expected = int(100.0) * 0.005 + int(80.0) * 0.002
        assert bonus == expected


# ── calculate_final_attack_with_details 全覆盖 ─────────────────────────


class TestCalculateFinalAttackWithDetailsFull:
    """calculate_final_attack_with_details 武器加成的各分支。"""

    _CHAR: dict[str, Any] = {
        "基础攻击力": [500.0, 510.0],
        "力量": [100.0],
        "敏捷": [80.0],
        "主能力": "力量",
        "副能力": "敏捷",
    }

    def test_with_weapon_normal_skill_attack_bonus(self) -> None:
        """武器 normal_skills 携带攻击力+。"""
        weapon: dict[str, Any] = {
            "基础攻击力": [200.0],
            "normal_skills": [{"effect": "攻击力+", "curve": [15.0]}],
        }
        result = calculate_final_attack_with_details(
            self._CHAR,
            weapon,
            char_level=1,
            weapon_level=1,
        )
        # attack_bonus_multiplier = 1 + 15/100 = 1.15
        assert result["attack_bonus_multiplier"] == pytest.approx(1.15)
        assert result["final_attack"] > 0

    def test_with_weapon_direct_attack_attr(self) -> None:
        """武器直接携带攻击力+属性键。"""
        weapon: dict[str, Any] = {
            "基础攻击力": [200.0],
            "攻击力+": [10.0],
        }
        result = calculate_final_attack_with_details(
            self._CHAR,
            weapon,
            char_level=1,
            weapon_level=1,
        )
        assert result["attack_bonus_multiplier"] == pytest.approx(1.10)
        assert result["final_attack"] > 0

    def test_with_weapon_additional_attack(self) -> None:
        """武器 normal_skills 携带附加攻击力+。"""
        weapon: dict[str, Any] = {
            "基础攻击力": [200.0],
            "normal_skills": [{"effect": "附加攻击力+", "curve": [50.0]}],
        }
        result = calculate_final_attack_with_details(
            self._CHAR,
            weapon,
            char_level=1,
            weapon_level=1,
        )
        assert result["additional_attack"] == 50.0

    def test_with_weapon_additional_attack_direct_key(self) -> None:
        """武器直接携带附加攻击力+属性键。"""
        weapon: dict[str, Any] = {
            "基础攻击力": [200.0],
            "附加攻击力+": [30.0],
        }
        result = calculate_final_attack_with_details(
            self._CHAR,
            weapon,
            char_level=1,
            weapon_level=1,
            sa1_name="附加攻击力+",
            sa1_level=1,
        )
        assert result["additional_attack"] == 30.0

    def test_with_equipment_stat_bonus(self) -> None:
        """equipment_stat_bonus 含攻击力时应排除。"""
        result = calculate_final_attack_with_details(
            self._CHAR,
            char_level=1,
            equipment_stat_bonus={"攻击力": 100.0, "力量": 20.0},
        )
        assert result["final_attack"] > 0
        # 攻击力应从 stat_bonus 中排除
        assert result["ability_bonus"] > 0

    def test_with_weapon_sa3_attack_skipped(self) -> None:
        """sa3==攻击力+ 且 sa3_level==0 时应跳过。"""
        weapon: dict[str, Any] = {
            "基础攻击力": [200.0],
            "normal_skills": [{"effect": "攻击力+", "curve": [99.0]}],
            "攻击力+": [99.0],
        }
        result = calculate_final_attack_with_details(
            self._CHAR,
            weapon,
            char_level=1,
            weapon_level=1,
            sa1_name="",
            sa2_name="",
            sa3_name="攻击力+",
            sa3_level=0,
        )
        # attack_bonus_multiplier 应为默认 1.0（因攻击力+被跳过）
        assert result["attack_bonus_multiplier"] == pytest.approx(1.0)

    def test_with_weapon_non_dict_skill_skipped(self) -> None:
        """normal_skills 中的非 dict 项应跳过。"""
        weapon: dict[str, Any] = {
            "基础攻击力": [200.0],
            "normal_skills": ["not_dict", {"effect": "攻击力+", "curve": [10.0]}],
        }
        result = calculate_final_attack_with_details(
            self._CHAR,
            weapon,
            char_level=1,
            weapon_level=1,
        )
        # attack_bonus_multiplier = 1 + 10/100 = 1.10
        assert result["attack_bonus_multiplier"] == pytest.approx(1.10)

    def test_with_legacy_kwargs_warning(self) -> None:
        """仅使用旧参数名 sa* 应触发告警。"""
        import warnings

        weapon: dict[str, Any] = {"基础攻击力": [200.0]}
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            calculate_final_attack_with_details(
                self._CHAR,
                weapon,
                char_level=1,
                weapon_level=1,
                sa1_name="敏捷+",
                sa1_level=1,
            )
            assert len(w) >= 1

    def test_with_weapon_bonus_data_float(self) -> None:
        """武器 bonus_data 为 float 类型。"""
        weapon: dict[str, Any] = {
            "基础攻击力": [200.0],
            "攻击力+": 15.0,  # float 而非 list
        }
        result = calculate_final_attack_with_details(
            self._CHAR,
            weapon,
            char_level=1,
            weapon_level=1,
        )
        # attack_bonus_multiplier = 1 + 15/100 = 1.15
        assert result["attack_bonus_multiplier"] == pytest.approx(1.15)

    def test_with_weapon_additional_attack_float(self) -> None:
        """武器附加攻击力+为 float 类型。"""
        weapon: dict[str, Any] = {
            "基础攻击力": [200.0],
            "附加攻击力+": 25.0,  # float 而非 list
        }
        result = calculate_final_attack_with_details(
            self._CHAR,
            weapon,
            char_level=1,
            weapon_level=1,
            sa1_name="附加攻击力+",
            sa1_level=1,
        )
        assert result["additional_attack"] == 25.0

    def test_char_no_base_attack_key(self) -> None:
        """角色没有基础攻击力键。"""
        char: dict[str, Any] = {"力量": [100.0], "主能力": "力量", "副能力": ""}
        result = calculate_final_attack_with_details(char, char_level=1)
        assert result["char_base_attack"] == 0.0

    def test_weapon_no_base_attack_key(self) -> None:
        """武器没有基础攻击力键。"""
        weapon: dict[str, Any] = {"normal_skills": []}
        result = calculate_final_attack_with_details(
            self._CHAR,
            weapon,
            char_level=1,
            weapon_level=1,
        )
        assert result["weapon_base_attack"] == 0.0

    def test_with_normal_skill_names(self) -> None:
        """使用新的 normal_skill_* 参数名。"""
        weapon: dict[str, Any] = {
            "基础攻击力": [200.0],
            "normal_skills": [{"effect": "攻击力+", "curve": [12.0]}],
        }
        result = calculate_final_attack_with_details(
            self._CHAR,
            weapon,
            char_level=1,
            weapon_level=1,
            normal_skill_1_name="攻击力+",
            normal_skill_1_level=1,
        )
        assert result["attack_bonus_multiplier"] == pytest.approx(1.12)

    def test_with_weapon_no_bonus(self) -> None:
        mgr = AttributeZoneManager()
        flat, pct = compute_attr_weapon_bonus(
            attr="力量",
            attr_is_main=True,
            attr_is_sub=False,
            weapon={"normal_skills": []},
            manager=mgr,
            sa1_name="",
            sa1_level=1,
            sa2_name="",
            sa2_level=1,
            sa3_name="",
            sa3_level=0,
            ws_name="",
            ws_level=1,
            ws_stack=1,
            ws2_name="",
            ws2_level=1,
            ws2_stack=1,
            main_attr="力量",
            sub_attr="敏捷",
            trust_level=0,
        )
        assert flat == 0.0
        assert pct == 0.0
