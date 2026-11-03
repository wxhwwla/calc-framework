# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""生存估算的覆盖扩展测试（P2-07 从 test_coverage_expansion.py 拆分）。"""

from __future__ import annotations


class TestSurvivalEstimate:
    """build_survival_estimate with minimal inputs."""

    def test_build_survival_estimate_basic(self):
        from games.endfield.calc.survival.estimate import build_survival_estimate

        char_data = {
            "力量": [100.0] * 90,
            "意志": [100.0] * 90,
            "主能力": "力量",
            "副能力": "敏捷",
        }
        weapon_data = {"基础攻击": 200, "攻击成长": 10, "攻击除数": 1}

        result = build_survival_estimate(
            char_data=char_data,
            weapon_data=weapon_data,
            char_level=80,
            weapon_level=80,
        )
        assert "execute_damage" in result
        assert "imbalance_cap" in result
        assert "burn_tick_per_sec" in result
        assert "enemy_max_hp" in result
        assert "healing_amount" in result
        assert "character_max_hp" in result

    def test_build_survival_estimate_with_enemy_max_hp(self):
        from games.endfield.calc.survival.estimate import build_survival_estimate

        char_data = {
            "力量": [100.0] * 90,
            "意志": [100.0] * 90,
        }
        weapon_data = {"基础攻击": 200, "攻击成长": 10, "攻击除数": 1}

        result = build_survival_estimate(
            char_data=char_data,
            weapon_data=weapon_data,
            char_level=80,
            weapon_level=80,
            enemy_max_hp=50000.0,
        )
        assert result["enemy_max_hp"] == 50000.0

    def test_build_survival_estimate_with_sp(self):
        from games.endfield.calc.survival.estimate import build_survival_estimate

        char_data = {
            "力量": [100.0] * 90,
            "意志": [100.0] * 90,
        }
        weapon_data = {"基础攻击": 200, "攻击成长": 10, "攻击除数": 1}

        result = build_survival_estimate(
            char_data=char_data,
            weapon_data=weapon_data,
            char_level=80,
            weapon_level=80,
            sp_start=50.0,
            sp_seconds=5.0,
            ult_start=50.0,
        )
        assert result["sp_after_regen"] > 0
        assert result["ultimate_charge_after"] >= 0

    def test_build_survival_estimate_zero_hp(self):
        from games.endfield.calc.survival.estimate import build_survival_estimate

        char_data = {
            "力量": [100.0] * 90,
            "意志": [100.0] * 90,
        }
        weapon_data = {"基础攻击": 200, "攻击成长": 10, "攻击除数": 1}

        result = build_survival_estimate(
            char_data=char_data,
            weapon_data=weapon_data,
            char_level=80,
            weapon_level=80,
            enemy_max_hp=0.0,
        )
        assert result["burn_tick_per_sec"] == 0.0

    def test_build_survival_estimate_keys_present(self):
        from games.endfield.calc.survival.estimate import build_survival_estimate

        char_data = {
            "力量": [100.0] * 90,
            "意志": [100.0] * 90,
        }
        weapon_data = {"基础攻击": 200, "攻击成长": 10, "攻击除数": 1}

        result = build_survival_estimate(
            char_data=char_data,
            weapon_data=weapon_data,
            char_level=80,
            weapon_level=80,
        )
        required_keys = [
            "execute_damage",
            "execute_multiplier",
            "execute_sp_restore",
            "imbalance_cap",
            "imbalance_duration_sec",
            "imbalance_nodes_1",
            "imbalance_nodes_2",
            "imbalance_gain_effective",
            "imbalance_gain_percent",
            "fast_break_multiplier",
            "burn_tick_per_sec",
            "enemy_max_hp",
            "sp_after_regen",
            "sp_regen_per_sec",
            "ultimate_charge_after",
            "ultimate_charge_per_100_sp",
            "dodge_sp_gain",
            "life_steal_heal",
            "healing_amount",
            "character_max_hp",
        ]
        for key in required_keys:
            assert key in result, f"Missing key: {key}"
