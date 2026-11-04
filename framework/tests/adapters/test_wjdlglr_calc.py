#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# SPDX-License-Identifier: AGPL-3.0
# ruff: noqa: E402

"""无尽的拉格朗日适配器求值测试 — 八乘区与按目标舰种的命中率修正。"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

_FRAMEWORK_SRC = Path(__file__).resolve().parents[2] / "src"

if str(_FRAMEWORK_SRC) not in sys.path:
    sys.path.insert(0, str(_FRAMEWORK_SRC))

from wjdlglr_test_helpers import _ADAPTER_DIR, _TARGETS, _context

from calc_framework.config.adapter import AdapterPackage


class TestShotsAndTiming:
    """乘区 1–4：发射数、飞行时间、冷却与持续时间、每分钟平均发射数。"""

    def test_shots_per_volley(self, adapter_pkg: AdapterPackage) -> None:
        result = adapter_pkg.dag_service.evaluate(_context())
        assert result.outputs["发射数"] == pytest.approx(2.0 * 3.0 * 4.0 * 5.0)

    def test_flight_time_with_mothership(self, adapter_pkg: AdapterPackage) -> None:
        result = adapter_pkg.dag_service.evaluate(_context())
        assert result.outputs["飞行时间(秒)"] == pytest.approx((3.0 + 2.0) * (1.0 - 0.1 - 0.2))

    def test_flight_time_zero_without_mothership(self, adapter_pkg: AdapterPackage) -> None:
        result = adapter_pkg.dag_service.evaluate(_context(weapon={"needs_mothership": 0.0}))
        assert result.outputs["飞行时间(秒)"] == pytest.approx(0.0)

    def test_flight_time_zero_without_outbound_inbound(self, adapter_pkg: AdapterPackage) -> None:
        result = adapter_pkg.dag_service.evaluate(_context(weapon={"outbound": 0.0, "inbound": 0.0}))
        assert result.outputs["飞行时间(秒)"] == pytest.approx(0.0)

    def test_cooldown_and_duration_with_mothership(self, adapter_pkg: AdapterPackage) -> None:
        result = adapter_pkg.dag_service.evaluate(_context())
        expected = 10.0 * (1.0 - 0.1 - 0.2) + 20.0 * (1.0 - 0.05 - 0.15)
        assert result.outputs["冷却与持续时间(秒)"] == pytest.approx(expected)

    def test_mothership_bonuses_ignored_without_mothership(self, adapter_pkg: AdapterPackage) -> None:
        result = adapter_pkg.dag_service.evaluate(_context(weapon={"needs_mothership": 0.0}))
        expected = 10.0 * (1.0 - 0.1) + 20.0 * (1.0 - 0.05)
        assert result.outputs["冷却与持续时间(秒)"] == pytest.approx(expected)

    def test_rate_per_minute(self, adapter_pkg: AdapterPackage) -> None:
        result = adapter_pkg.dag_service.evaluate(_context())
        cycle = 23.0 + 3.5
        assert result.outputs["每分钟平均发射数"] == pytest.approx(120.0 / cycle * 60.0)

    def test_zero_cycle_does_not_crash(self, adapter_pkg: AdapterPackage) -> None:
        result = adapter_pkg.dag_service.evaluate(
            _context(
                weapon={
                    "needs_mothership": 0.0,
                    "outbound": 0.0,
                    "inbound": 0.0,
                    "base_cooldown": 0.0,
                    "base_duration": 0.0,
                }
            )
        )
        assert result.outputs["每分钟平均发射数"] == pytest.approx(120.0 / 0.001 * 60.0)


class TestCritAndDamage:
    """乘区 5–8：暴击增伤倍率、甲后单发、最终单发、满命中伤害。"""

    def test_crit_multiplier_uses_weapon_base_values(self, adapter_pkg: AdapterPackage) -> None:
        result = adapter_pkg.dag_service.evaluate(_context())
        assert result.outputs["暴击增伤倍率"] == pytest.approx(0.5 * 2.0 * 1.1)
        assert result.outputs["暴击增伤倍率(对空)"] == pytest.approx(0.5 * 2.0 * 1.1)

    def test_crit_multiplier_falls_back_to_bonus_crit_rate(self, adapter_pkg: AdapterPackage) -> None:
        result = adapter_pkg.dag_service.evaluate(_context(weapon={"crit_rate": 0.0}, user={"bonus_crit_rate": 25.0}))
        assert result.outputs["暴击增伤倍率"] == pytest.approx(0.25 * 2.0 * 1.1)

    def test_missing_crit_fields_default_to_zero(self, adapter_pkg: AdapterPackage) -> None:
        result = adapter_pkg.dag_service.evaluate(
            _context(
                weapon={"crit_rate": 0.0, "crit_damage": 0.0},
                user={
                    "bonus_crit_rate": 0.0,
                    "crit_multiplier_bonus": 0.0,
                },
            )
        )
        assert result.outputs["暴击增伤倍率"] == pytest.approx(0.0)
        assert result.outputs["暴击增伤倍率(对空)"] == pytest.approx(0.0)
        assert result.outputs["最终单发"] == pytest.approx(90.0)
        assert result.outputs["最终单发(对空)"] == pytest.approx(90.0)

    def test_anti_air_crit_only_applies_to_air_targets(self, adapter_pkg: AdapterPackage) -> None:
        result = adapter_pkg.dag_service.evaluate(
            _context(
                weapon={"crit_rate": 25.0, "crit_damage": 100.0, "crit_vs_air": 1.0},
                user={"bonus_crit_rate": 0.0, "crit_multiplier_bonus": 0.0},
            )
        )
        assert result.outputs["暴击增伤倍率"] == pytest.approx(0.0)
        assert result.outputs["暴击增伤倍率(对空)"] == pytest.approx(0.25)
        assert result.outputs["甲后单发"] == pytest.approx(90.0)
        assert result.outputs["最终单发"] == pytest.approx(90.0)
        assert result.outputs["最终单发(对空)"] == pytest.approx(90.0 * 1.25)
        rate = result.outputs["每分钟平均发射数"]
        assert result.outputs["最终每分钟伤害_战机"] == pytest.approx(90.0 * 1.25 * rate * 0.22)
        assert result.outputs["最终每分钟伤害_护卫舰"] == pytest.approx(90.0 * rate * 0.85)

    def test_armor_adjusted_shot(self, adapter_pkg: AdapterPackage) -> None:
        result = adapter_pkg.dag_service.evaluate(_context())
        assert result.outputs["甲后单发"] == pytest.approx(100.0 * 1.2 - 30.0)

    def test_energy_weapon_uses_energy_armor(self, adapter_pkg: AdapterPackage) -> None:
        result = adapter_pkg.dag_service.evaluate(_context(weapon={"is_energy": 1.0}))
        assert result.outputs["甲后单发"] == pytest.approx(100.0 * 1.2 - 50.0)

    def test_physical_weapon_ignores_energy_armor(self, adapter_pkg: AdapterPackage) -> None:
        result = adapter_pkg.dag_service.evaluate(_context(weapon={"is_energy": 0.0}, user={"energy_armor": 999.0}))
        assert result.outputs["甲后单发"] == pytest.approx(100.0 * 1.2 - 30.0)

    def test_final_shot(self, adapter_pkg: AdapterPackage) -> None:
        result = adapter_pkg.dag_service.evaluate(_context())
        assert result.outputs["最终单发"] == pytest.approx(90.0 * (1.0 + 1.1))

    def test_full_hit_damage_per_minute(self, adapter_pkg: AdapterPackage) -> None:
        result = adapter_pkg.dag_service.evaluate(_context())
        cycle = 23.0 + 3.5
        expected = 120.0 / cycle * 60.0 * 189.0
        assert result.outputs["满命中每分钟伤害"] == pytest.approx(expected)


class TestPerTargetDamage:
    """按目标舰种命中率修正的最终每分钟伤害。"""

    def test_hit_rate_scales_damage(self, adapter_pkg: AdapterPackage) -> None:
        result = adapter_pkg.dag_service.evaluate(_context())
        cycle = 23.0 + 3.5
        full = 120.0 / cycle * 60.0 * 189.0
        assert result.outputs["最终每分钟伤害_战机"] == pytest.approx(full * 0.22)
        assert result.outputs["最终每分钟伤害_护卫舰"] == pytest.approx(full * 0.85)
        assert result.outputs["最终每分钟伤害_巡洋舰"] == pytest.approx(0.0)

    def test_friendly_weapon_ignores_hit_table(self, adapter_pkg: AdapterPackage) -> None:
        result = adapter_pkg.dag_service.evaluate(_context(weapon={"friendly": 1.0, "hit_fighter": 0.0, "hit_frigate": 0.0}))
        full = result.outputs["满命中每分钟伤害"]
        assert full > 0
        for _, label in _TARGETS:
            assert result.outputs[f"最终每分钟伤害_{label}"] == pytest.approx(full)


class TestInputDeclarations:
    """用户输入的类型与上下限声明。"""

    def test_fleet_count_is_integer(self, adapter_pkg: AdapterPackage) -> None:
        variable = adapter_pkg.dag_service.dag.variables["user_input.fleet_count"]
        assert variable.type == "int"
        assert variable.default == 1

    def test_only_flight_and_cooldown_bonuses_have_upper_limit(self, adapter_pkg: AdapterPackage) -> None:
        variables = adapter_pkg.dag_service.dag.variables
        capped = {path for path, variable in variables.items() if path.startswith("user_input.") and variable.max is not None}
        assert capped == {
            "user_input.self_flight_bonus",
            "user_input.mothership_flight_bonus",
            "user_input.self_cooldown_bonus",
            "user_input.mothership_cooldown_bonus",
        }
        for path in capped:
            assert variables[path].max == 100.0

    def test_percentage_inputs_declare_percent_suffix(self, adapter_pkg: AdapterPackage) -> None:
        variables = adapter_pkg.dag_service.dag.variables
        paths = {
            "user_input.self_flight_bonus",
            "user_input.mothership_flight_bonus",
            "user_input.self_cooldown_bonus",
            "user_input.mothership_cooldown_bonus",
            "user_input.self_duration_bonus",
            "user_input.mothership_duration_bonus",
            "user_input.bonus_crit_rate",
            "user_input.crit_multiplier_bonus",
            "user_input.damage_bonus",
        }
        for path in paths:
            assert variables[path].ui_control.get("suffix") == "%", path
            assert variables[path].ui_control.get("step") == 1, path
        assert variables["user_input.physical_armor"].ui_control.get("suffix", "") == ""

    def test_target_parameters_are_removed(self, adapter_pkg: AdapterPackage) -> None:
        dag = adapter_pkg.dag_service.dag
        assert "user_input.enemy_hp" not in dag.variables
        assert "user_input.firepower" not in dag.variables
        assert "official_ttk" not in dag.nodes
        assert "官方火力击杀时间(秒)" not in dag.outputs

    def test_layout_has_no_target_or_supplemental_section(self) -> None:
        layout = json.loads((_ADAPTER_DIR / "ui" / "layout.json").read_text(encoding="utf-8"))
        ids = {section["id"] for section in layout["sections"]}
        assert "target" not in ids
        assert "supplemental" not in ids
