# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""覆盖 corrosion / enemy_growth / combo_bonus / abnormal_attached / originium_arts / physical_abnormal_state。"""

from __future__ import annotations

from games.endfield.calc.damage.abnormal_attached import (
    armor_break_physical_vulnerability,
    build_physical_attached_effects,
    conductive_spell_vulnerability,
    corrosion_initial_resistance_shred,
)
from games.endfield.calc.damage.combo_bonus import combo_bonus_rate, combo_zone_multiplier
from games.endfield.calc.damage.corrosion import corrosion_total_resistance_shred
from games.endfield.calc.damage.enemy_growth import (
    enemy_growth_note,
    plugin_enemy_survival_fields,
    resolve_enemy_max_hp,
)
from games.endfield.calc.damage.originium_arts import (
    attached_effect_enhancement,
    enhance_attached_effect,
    strength_zone_multiplier,
    sum_originium_arts_strength,
)
from games.endfield.calc.damage.physical_abnormal_state import (
    break_defense_after_rotation_hits,
    break_defense_stacks_at_hit,
    consume_break_defense_stacks,
    format_break_defense_rotation_note,
    is_physical_abnormal_key,
    parse_abnormal_base_name,
)

# ── combo_bonus.py ───────────────────────────────────────────────────────


class TestComboBonus:
    """combo_bonus_rate / combo_zone_multiplier。"""

    def test_zero_stacks(self) -> None:
        assert combo_bonus_rate("战技", 0) == 0.0

    def test_negative_stacks(self) -> None:
        assert combo_bonus_rate("战技", -1) == 0.0

    def test_skill_stacks_1_through_4(self) -> None:
        assert combo_bonus_rate("战技", 1) == 0.30
        assert combo_bonus_rate("战技", 2) == 0.45
        assert combo_bonus_rate("战技", 3) == 0.60
        assert combo_bonus_rate("战技", 4) == 0.75

    def test_ultimate_stacks(self) -> None:
        assert combo_bonus_rate("终结技", 1) == 0.20
        assert combo_bonus_rate("终结技", 4) == 0.50

    def test_overflow_stacks(self) -> None:
        assert combo_bonus_rate("战技", 10) == 0.75

    def test_unknown_skill_type_uses_skill_table(self) -> None:
        assert combo_bonus_rate("未知", 1) == 0.30

    def test_zone_multiplier_positive_stacks(self) -> None:
        assert combo_zone_multiplier("战技", 2) == 1.45

    def test_zone_multiplier_zero_stacks_with_legacy(self) -> None:
        assert combo_zone_multiplier("战技", 0, flat_legacy_bonus=0.10) == 1.10

    def test_zone_multiplier_zero_all(self) -> None:
        assert combo_zone_multiplier("战技", 0) == 1.0


# ── originium_arts.py ────────────────────────────────────────────────────


class TestOriginiumArts:
    """originium_arts：strength 汇总、乘区倍率、附着效果增强。"""

    def test_sum_empty(self) -> None:
        assert sum_originium_arts_strength(None) == 0.0
        assert sum_originium_arts_strength({}) == 0.0

    def test_sum_positive(self) -> None:
        assert sum_originium_arts_strength({"源石技艺强度": 50.0}) == 50.0

    def test_sum_ignores_other_keys(self) -> None:
        assert sum_originium_arts_strength({"攻击力%": 10.0, "源石技艺强度": 30.0}) == 30.0

    def test_strength_zone_multiplier_zero(self) -> None:
        assert strength_zone_multiplier(0.0) == 1.0

    def test_strength_zone_multiplier_positive(self) -> None:
        assert strength_zone_multiplier(50.0) == 1.5

    def test_strength_zone_multiplier_negative(self) -> None:
        assert strength_zone_multiplier(-10.0) == 1.0

    def test_attached_effect_enhancement_zero(self) -> None:
        assert attached_effect_enhancement(0.0) == 0.0

    def test_attached_effect_enhancement_positive(self) -> None:
        result = attached_effect_enhancement(300.0)
        assert result == 2.0 * 300.0 / 600.0

    def test_enhance_attached_effect_no_strength(self) -> None:
        assert enhance_attached_effect(0.12, 0.0) == 0.12

    def test_enhance_attached_effect_with_strength(self) -> None:
        enhanced = enhance_attached_effect(0.12, 300.0)
        assert enhanced == 0.12 * (1.0 + 2.0 * 300.0 / 600.0)


# ── abnormal_attached.py ────────────────────────────────────────────────


class TestAbnormalAttached:
    """导电 / 碎甲 / 腐蚀初始降抗 / build_physical_attached_effects。"""

    def test_conductive_vulnerability_level_1(self) -> None:
        result = conductive_spell_vulnerability(1)
        assert result == 0.12

    def test_conductive_vulnerability_level_4(self) -> None:
        assert conductive_spell_vulnerability(4) == 0.24

    def test_conductive_vulnerability_with_effect_multiplier(self) -> None:
        result = conductive_spell_vulnerability(2, effect_multiplier=0.5)
        assert result == 0.16 * 0.5

    def test_armor_break_vulnerability(self) -> None:
        assert armor_break_physical_vulnerability(1) == 0.12

    def test_armor_break_vulnerability_with_strength(self) -> None:
        result = armor_break_physical_vulnerability(1, originium_arts_strength=300.0)
        assert result > 0.12

    def test_corrosion_initial_shred(self) -> None:
        assert corrosion_initial_resistance_shred(1) == 3.6
        assert corrosion_initial_resistance_shred(4) == 7.2

    def test_corrosion_initial_shred_out_of_range(self) -> None:
        assert corrosion_initial_resistance_shred(10) == 7.2  # clamped to 4
        assert corrosion_initial_resistance_shred(0) == 3.6  # clamped to 1

    def test_build_physical_attached_effects_invalid(self) -> None:
        result = build_physical_attached_effects("未知", 1)
        assert result == []

    def test_build_physical_attached_effects_armor_break(self) -> None:
        result = build_physical_attached_effects("碎甲", 1)
        assert len(result) == 1
        assert "碎甲" in str(result[0].source)


# ── corrosion.py ─────────────────────────────────────────────────────────


class TestCorrosion:
    """corrosion_total_resistance_shred。"""

    def test_shred_level_1_full_duration(self) -> None:
        shred = corrosion_total_resistance_shred(1)
        assert shred > 3.6  # initial + drip
        assert shred <= 12.0  # cap

    def test_shred_level_1_zero_elapsed(self) -> None:
        shred = corrosion_total_resistance_shred(1, elapsed_seconds=0.0)
        assert shred == 3.6

    def test_shred_level_4_with_strength(self) -> None:
        shred = corrosion_total_resistance_shred(4, originium_arts_strength=300.0)
        assert shred > 7.2

    def test_shred_with_effect_multiplier(self) -> None:
        shred = corrosion_total_resistance_shred(2, effect_multiplier=0.5)
        assert shred < corrosion_total_resistance_shred(2)


# ── enemy_growth.py ──────────────────────────────────────────────────────


class TestEnemyGrowth:
    """resolve_enemy_max_hp / enemy_growth_note / plugin_enemy_survival_fields。"""

    def test_resolve_empty_id_returns_default(self) -> None:
        assert resolve_enemy_max_hp("", default=1000.0) == 1000.0

    def test_resolve_unknown_id(self) -> None:
        # 无插件注册时，未知 id 返回 default
        result = resolve_enemy_max_hp("missing", default=5000.0)
        assert result == 5000.0

    def test_growth_note_returns_string(self) -> None:
        note = enemy_growth_note()
        assert isinstance(note, str)
        assert len(note) > 10

    def test_plugin_enemy_fields_empty(self) -> None:
        assert plugin_enemy_survival_fields("") == {}

    def test_plugin_enemy_fields_unknown(self) -> None:
        fields = plugin_enemy_survival_fields("nonexistent")
        assert fields == {}


# ── physical_abnormal_state.py ───────────────────────────────────────────


class TestPhysicalAbnormalState:
    """parse_abnormal_base_name / is_physical_abnormal_key / consume_break_defense_stacks 等。"""

    def test_parse_basic(self) -> None:
        assert parse_abnormal_base_name("碎甲") == "碎甲"
        assert parse_abnormal_base_name("猛击:2") == "猛击"

    def test_parse_forced_prefix(self) -> None:
        assert parse_abnormal_base_name("强制:灼热异常:1") == "强制:灼热异常"

    def test_parse_empty(self) -> None:
        assert parse_abnormal_base_name("") == ""

    def test_is_physical_abnormal_key_true(self) -> None:
        assert is_physical_abnormal_key("倒地") is True
        assert is_physical_abnormal_key("碎甲") is True
        assert is_physical_abnormal_key("击飞") is True
        assert is_physical_abnormal_key("猛击") is True

    def test_is_physical_abnormal_key_false(self) -> None:
        assert is_physical_abnormal_key("破防") is False
        assert is_physical_abnormal_key("腐蚀") is False
        assert is_physical_abnormal_key("") is False

    def test_consume_break_defense_stacks_basic(self) -> None:
        assert consume_break_defense_stacks(4, consuming_hits=2, layers_per_hit=1) == 2

    def test_consume_break_defense_stacks_all_consumed(self) -> None:
        assert consume_break_defense_stacks(2, consuming_hits=10) == 0

    def test_consume_break_defense_stacks_zero_initial(self) -> None:
        assert consume_break_defense_stacks(0, consuming_hits=1) == 0

    def test_break_defense_after_rotation_hits(self) -> None:
        counts = {"战技": 2, "普攻": 1, "碎甲": 1}  # 碎甲不计入
        remaining = break_defense_after_rotation_hits(4, counts)
        assert remaining == 1  # 4 - 3 = 1

    def test_break_defense_after_rotation_hits_empty(self) -> None:
        assert break_defense_after_rotation_hits(3, {}) == 3

    def test_format_rotation_note_returns_note(self) -> None:
        note = format_break_defense_rotation_note(4, {"战技": 2})
        assert note is not None
        assert "破防" in note

    def test_format_rotation_note_none(self) -> None:
        assert format_break_defense_rotation_note(0, {}) is None

    def test_stacks_at_hit_first_hit(self) -> None:
        assert break_defense_stacks_at_hit(4, 1) == 4

    def test_stacks_at_hit_after_consumption(self) -> None:
        assert break_defense_stacks_at_hit(4, 3, layers_per_hit=1) == 2

    def test_stacks_at_hit_zero_hit_index(self) -> None:
        assert break_defense_stacks_at_hit(4, 0) == 4
