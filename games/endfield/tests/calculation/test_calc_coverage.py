# SPDX-License-Identifier: AGPL-3.0
"""覆盖 character_stats、healing、execute、imbalance 等 calc 模块。"""

from __future__ import annotations

import pytest
from games.endfield.calc.character_stats import base_hp_at_level, strength_hp_bonus, total_max_hp
from games.endfield.calc.damage.break_defense import (
    clamp_break_defense_stacks,
    vulnerability_bonus_from_break_defense,
)
from games.endfield.calc.damage.combat_resources import (
    estimate_ultimate_after_actions,
    sp_after_natural_regen,
    ultimate_charge_from_sp_gain,
)
from games.endfield.calc.damage.execute import execute_damage_multiplier, execute_sp_restore
from games.endfield.calc.damage.healing import (
    HealingContext,
    calculate_healing,
    received_heal_efficiency_from_will,
)
from games.endfield.calc.damage.imbalance import (
    accumulation_multiplier_after_fast_break,
    imbalance_cap_for_tier,
    imbalance_duration_for_tier,
    imbalance_node_thresholds,
    imbalance_nodes_crossed,
    scaled_imbalance_gain,
)
from games.endfield.calc.damage.incoming import (
    enemy_incoming_damage_to_operator,
    operator_resistance_multiplier,
    operator_resistance_points,
)
from games.endfield.calc.damage.special_damage import effective_defense_multiplier, life_steal_heal

# ── character_stats.py ────────────────────────────────────────────────────


class TestCharacterStats:
    """base_hp_at_level / strength_hp_bonus / total_max_hp。"""

    def test_base_hp_lv1(self) -> None:
        assert base_hp_at_level(1) == 500.0

    def test_base_hp_lv90(self) -> None:
        assert base_hp_at_level(90) == 500.0 + round(5500.0 / 98.0 * 89, 0)

    def test_base_hp_lv0_clamped(self) -> None:
        assert base_hp_at_level(0) == 500.0

    def test_strength_hp_bonus_zero(self) -> None:
        assert strength_hp_bonus(0.0) == 0.0

    def test_strength_hp_bonus_positive(self) -> None:
        assert strength_hp_bonus(100.0) == 500.0

    def test_strength_hp_bonus_floor(self) -> None:
        assert strength_hp_bonus(100.7) == 500.0

    def test_total_max_hp(self) -> None:
        hp = total_max_hp(80.0, level=50)
        expected_base = base_hp_at_level(50)
        expected_bonus = strength_hp_bonus(80.0)
        assert hp == expected_base + expected_bonus

    def test_total_max_hp_default_level(self) -> None:
        hp = total_max_hp(0.0)
        assert hp == 500.0


# ── healing.py ────────────────────────────────────────────────────────────


class TestHealing:
    """HealingContext / calculate_healing / received_heal_efficiency_from_will。"""

    def test_received_heal_efficiency_from_will(self) -> None:
        assert received_heal_efficiency_from_will(100.0) == 0.1
        assert received_heal_efficiency_from_will(50.7) == 0.05
        assert received_heal_efficiency_from_will(0.0) == 0.0

    def test_calculate_healing_flat_only(self) -> None:
        ctx = HealingContext(base_heal_flat=1000.0)
        result = calculate_healing(ctx)
        assert result["基础治疗区"] == 1000.0
        assert result["治疗效率区"] == 1.0
        assert result["独立治疗效果区"] == 1.0
        assert result["治疗量"] == 1000.0

    def test_calculate_healing_all_zones(self) -> None:
        ctx = HealingContext(
            base_heal_flat=500.0,
            stat_per_point=0.47,
            stat_value=100.0,
            max_hp=10000.0,
            hp_heal_ratio=0.05,
            heal_efficiency=0.20,
            received_heal_efficiency=0.10,
            independent_heal_bonus=0.30,
        )
        result = calculate_healing(ctx)
        base = 500.0 + 0.47 * 100.0 + 10000.0 * 0.05
        eff = 1.0 + 0.20 + 0.10
        indep = 1.0 + 0.30
        assert result["基础治疗区"] == base
        assert result["治疗效率区"] == eff
        assert result["独立治疗效果区"] == indep
        assert result["治疗量"] == base * eff * indep

    def test_calculate_healing_zero(self) -> None:
        ctx = HealingContext()
        result = calculate_healing(ctx)
        assert result["治疗量"] == 0.0


# ── execute.py ────────────────────────────────────────────────────────────


class TestExecute:
    """execute_damage_multiplier / execute_sp_restore。"""

    def test_execute_damage_multiplier_normal(self) -> None:
        assert execute_damage_multiplier("普通") == 1.0

    def test_execute_damage_multiplier_elite(self) -> None:
        assert execute_damage_multiplier("精英") == 1.5

    def test_execute_damage_multiplier_leader(self) -> None:
        assert execute_damage_multiplier("领袖") == 1.75

    def test_execute_damage_multiplier_unknown(self) -> None:
        assert execute_damage_multiplier("未知") == 1.0

    def test_execute_sp_restore_normal(self) -> None:
        assert execute_sp_restore("普通") == 25

    def test_execute_sp_restore_elite(self) -> None:
        assert execute_sp_restore("精英") == 50

    def test_execute_sp_restore_leader(self) -> None:
        assert execute_sp_restore("领袖") == 100

    def test_execute_sp_restore_unknown(self) -> None:
        assert execute_sp_restore("未知") == 25


# ── imbalance.py ─────────────────────────────────────────────────────────


class TestImbalance:
    """失衡系统函数。"""

    def test_cap_normal(self) -> None:
        assert imbalance_cap_for_tier("普通") == 75.0

    def test_cap_elite(self) -> None:
        assert imbalance_cap_for_tier("精英") == 280.0

    def test_cap_leader(self) -> None:
        assert imbalance_cap_for_tier("领袖") == 400.0

    def test_cap_unknown(self) -> None:
        assert imbalance_cap_for_tier("未知") == 75.0

    def test_duration_normal(self) -> None:
        assert imbalance_duration_for_tier("普通") == 6.0

    def test_duration_leader(self) -> None:
        assert imbalance_duration_for_tier("领袖") == 11.0

    def test_scaled_imbalance_gain_no_bonus(self) -> None:
        assert scaled_imbalance_gain(10.0) == 10.0

    def test_scaled_imbalance_gain_with_bonus(self) -> None:
        assert scaled_imbalance_gain(10.0, imbalance_efficiency_bonus=0.20) == 12.0

    def test_accumulation_multiplier_no_fast_break(self) -> None:
        assert (
            accumulation_multiplier_after_fast_break(
                tier="普通",
                seconds_since_combat_start=5.0,
                seconds_since_last_imbalance_end=10.0,
                was_fast_break=False,
            )
            == 1.0
        )

    def test_accumulation_multiplier_fast_break_within_window(self) -> None:
        assert (
            accumulation_multiplier_after_fast_break(
                tier="普通",
                seconds_since_combat_start=1.0,
                seconds_since_last_imbalance_end=0.0,
                was_fast_break=True,
            )
            == 0.5
        )

    def test_accumulation_multiplier_fast_break_past_window(self) -> None:
        assert (
            accumulation_multiplier_after_fast_break(
                tier="普通",
                seconds_since_combat_start=10.0,
                seconds_since_last_imbalance_end=0.0,
                was_fast_break=True,
            )
            == 1.0
        )

    def test_accumulation_multiplier_fast_break_past_penalty(self) -> None:
        assert (
            accumulation_multiplier_after_fast_break(
                tier="普通",
                seconds_since_combat_start=1.0,
                seconds_since_last_imbalance_end=5.0,
                was_fast_break=True,
            )
            == 1.0
        )

    def test_node_thresholds_single(self) -> None:
        thresholds = imbalance_node_thresholds(100.0, node_count=1)
        assert thresholds == (50.0,)

    def test_node_thresholds_double(self) -> None:
        thresholds = imbalance_node_thresholds(300.0, node_count=2)
        assert thresholds == (100.0, 200.0)

    def test_node_thresholds_high_clamped_to_two(self) -> None:
        thresholds = imbalance_node_thresholds(100.0, node_count=5)
        # node_count 超过 2 时 clamp 到 2 => (100/3, 200/3)
        assert thresholds[0] == pytest.approx(100.0 / 3.0)
        assert thresholds[1] == pytest.approx(200.0 / 3.0)

    def test_nodes_crossed_none(self) -> None:
        crossed = imbalance_nodes_crossed(10.0, 20.0, cap=100.0, node_count=1)
        assert crossed == ()

    def test_nodes_crossed_one(self) -> None:
        crossed = imbalance_nodes_crossed(10.0, 60.0, cap=100.0, node_count=1)
        assert crossed == (1,)

    def test_nodes_crossed_two(self) -> None:
        crossed = imbalance_nodes_crossed(10.0, 250.0, cap=300.0, node_count=2)
        assert crossed == (1, 2)


# ── incoming.py ──────────────────────────────────────────────────────────


class TestIncoming:
    """operator_resistance_multiplier / operator_resistance_points / enemy_incoming_damage_to_operator。"""

    def test_resistance_multiplier_zero(self) -> None:
        mult = operator_resistance_multiplier(0.0)
        assert mult == 1.0  # 1/(0+1) = 1

    def test_resistance_multiplier_high(self) -> None:
        mult = operator_resistance_multiplier(1000.0)
        expected = 1.0 / (0.001 * 1000 + 1.0)
        assert mult == expected

    def test_resistance_multiplier_minimum(self) -> None:
        mult = operator_resistance_multiplier(10000.0)
        assert mult == 0.1  # 下限

    def test_resistance_points(self) -> None:
        pts = operator_resistance_points(500.0)
        expected = 100.0 - 100.0 / (0.001 * 500 + 1.0)
        assert pts == expected

    def test_incoming_physical(self) -> None:
        dmg = enemy_incoming_damage_to_operator(1000.0, agility=200.0, damage_type="物理")
        mult = operator_resistance_multiplier(200.0)
        assert dmg == 1000.0 * mult

    def test_incoming_magical(self) -> None:
        dmg = enemy_incoming_damage_to_operator(1000.0, intellect=200.0, damage_type="法术")
        mult = operator_resistance_multiplier(200.0)
        assert dmg == 1000.0 * mult

    def test_incoming_unknown_type_defaults_physical(self) -> None:
        dmg = enemy_incoming_damage_to_operator(500.0, agility=100.0, damage_type="未知")
        mult = operator_resistance_multiplier(100.0)
        assert dmg == 500.0 * mult

    def test_incoming_burn_subtype(self) -> None:
        dmg = enemy_incoming_damage_to_operator(1000.0, intellect=150.0, damage_type="法术-灼热")
        mult = operator_resistance_multiplier(150.0)
        assert dmg == 1000.0 * mult


# ── special_damage.py ────────────────────────────────────────────────────


class TestSpecialDamage:
    """life_steal_heal / effective_defense_multiplier。"""

    def test_life_steal_heal_zero_rate(self) -> None:
        assert life_steal_heal(1000.0, life_steal_rate=0.0) == 0.0

    def test_life_steal_heal_positive(self) -> None:
        assert life_steal_heal(1000.0, life_steal_rate=0.10) == 100.0

    def test_life_steal_heal_negative_damage(self) -> None:
        assert life_steal_heal(-100.0, life_steal_rate=0.10) == 0.0

    def test_effective_defense_multiplier_true_damage(self) -> None:
        assert effective_defense_multiplier(enemy_defense=500.0, is_true_damage=True) == 1.0

    def test_effective_defense_multiplier_physical(self) -> None:
        mult = effective_defense_multiplier(enemy_defense=200.0, is_true_damage=False)
        assert mult == 100.0 / (100.0 + 200.0)

    def test_effective_defense_multiplier_zero_defense(self) -> None:
        assert effective_defense_multiplier(enemy_defense=0.0, is_true_damage=False) == 1.0

    def test_effective_defense_multiplier_negative_defense(self) -> None:
        mult = effective_defense_multiplier(enemy_defense=-50.0, is_true_damage=False)
        assert mult == 100.0 / 100.0  # 负数取 max(0) 后为 0


# ── break_defense.py ─────────────────────────────────────────────────────


class TestBreakDefense:
    """clamp_break_defense_stacks / vulnerability_bonus_from_break_defense。"""

    def test_clamp_zero(self) -> None:
        assert clamp_break_defense_stacks(0) == 0

    def test_clamp_normal(self) -> None:
        assert clamp_break_defense_stacks(2) == 2

    def test_clamp_max(self) -> None:
        assert clamp_break_defense_stacks(4) == 4

    def test_clamp_overflow(self) -> None:
        assert clamp_break_defense_stacks(10) == 4

    def test_clamp_negative(self) -> None:
        assert clamp_break_defense_stacks(-1) == 0

    def test_vulnerability_bonus_zero(self) -> None:
        assert vulnerability_bonus_from_break_defense(0) == 0.0

    def test_vulnerability_bonus_2stacks(self) -> None:
        assert vulnerability_bonus_from_break_defense(2) == 0.16

    def test_vulnerability_bonus_4stacks(self) -> None:
        assert vulnerability_bonus_from_break_defense(4) == 0.32

    def test_vulnerability_bonus_custom_per_stack(self) -> None:
        assert vulnerability_bonus_from_break_defense(2, per_stack=0.10) == 0.20

    def test_vulnerability_bonus_overflow(self) -> None:
        assert vulnerability_bonus_from_break_defense(10) == 0.32  # clamped to 4


# ── combat_resources.py ──────────────────────────────────────────────────


class TestCombatResources:
    """sp_after_natural_regen / ultimate_charge_from_sp_gain / estimate_ultimate_after_actions。"""

    def test_sp_after_regen_zero_seconds(self) -> None:
        assert sp_after_natural_regen(50.0, 0.0) == 50.0

    def test_sp_after_regen_positive(self) -> None:
        result = sp_after_natural_regen(50.0, 2.0)
        assert result == min(100.0, 50.0 + 8.0 * 2.0)

    def test_sp_after_regen_capped(self) -> None:
        assert sp_after_natural_regen(95.0, 10.0) == 100.0

    def test_sp_after_regen_custom_max(self) -> None:
        result = sp_after_natural_regen(50.0, 5.0, max_sp=80.0)
        assert result == min(80.0, 50.0 + 8.0 * 5.0)

    def test_ultimate_charge_from_sp_gain_zero(self) -> None:
        assert ultimate_charge_from_sp_gain(0.0) == 0.0

    def test_ultimate_charge_from_sp_gain_positive(self) -> None:
        charge = ultimate_charge_from_sp_gain(50.0)
        assert charge == 50.0 * 6.5 / 100.0

    def test_ultimate_charge_from_sp_gain_refund(self) -> None:
        assert ultimate_charge_from_sp_gain(50.0, is_refund=True) == 0.0

    def test_ultimate_charge_from_sp_gain_negative(self) -> None:
        assert ultimate_charge_from_sp_gain(-10.0) == 0.0

    def test_estimate_ultimate_empty(self) -> None:
        assert estimate_ultimate_after_actions(0.0) == 0.0

    def test_estimate_ultimate_with_gains(self) -> None:
        result = estimate_ultimate_after_actions(10.0, sp_gains=(50.0, 30.0))
        expected = 10.0 + 50.0 * 6.5 / 100.0 + 30.0 * 6.5 / 100.0
        assert result == expected

    def test_estimate_ultimate_with_link_skill(self) -> None:
        result = estimate_ultimate_after_actions(0.0, link_skill_count=2)
        assert result == 20.0

    def test_estimate_ultimate_capped(self) -> None:
        result = estimate_ultimate_after_actions(95.0, sp_gains=(100.0,), max_charge=100.0)
        assert result == 100.0
