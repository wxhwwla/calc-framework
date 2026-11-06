# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""无尽的拉格朗日适配器 — 命中率乘区测试。"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pytest

_FRAMEWORK_SRC = Path(__file__).resolve().parents[2] / "src"

if str(_FRAMEWORK_SRC) not in sys.path:
    sys.path.insert(0, str(_FRAMEWORK_SRC))

from wjdlglr_test_helpers import _ADAPTER_DIR, _TARGETS, _context

from calc_framework.config.adapter import AdapterPackage


def _final_hit(result: Any, label: str) -> float:
    return float(result.outputs[f"最终命中率_{label}"])


class TestHitRateFormula:
    """中间命中率公式、钳制顺序与浮动。"""

    def test_mid_hit_uses_evasion_bonus_and_wiki_base_hit(self, adapter_pkg: AdapterPackage) -> None:
        result = adapter_pkg.dag_service.evaluate(
            _context(
                weapon={"hit_fighter": 60.0},
                user={"target_evasion": 20.0, "hit_rate_bonus": 10.0},
            )
        )
        assert _final_hit(result, "战机") == pytest.approx((0.20 + 0.10) * (1.0 + 0.60))

    def test_final_hit_is_clamped_to_five_percent_before_fluctuation(self, adapter_pkg: AdapterPackage) -> None:
        result = adapter_pkg.dag_service.evaluate(
            _context(
                weapon={"hit_fighter": 0.0},
                user={"target_evasion": 0.0, "hit_rate_bonus": 0.0, "hit_rate_fluctuation": 0.0},
            )
        )
        assert _final_hit(result, "战机") == pytest.approx(0.05)

    def test_final_hit_is_clamped_to_ninety_five_percent_before_fluctuation(self, adapter_pkg: AdapterPackage) -> None:
        result = adapter_pkg.dag_service.evaluate(
            _context(
                weapon={"hit_fighter": 100.0},
                user={"target_evasion": 100.0, "hit_rate_bonus": 100.0, "hit_rate_fluctuation": 0.0},
            )
        )
        assert _final_hit(result, "战机") == pytest.approx(0.95)

    def test_positive_fluctuation_is_added_after_clamp(self, adapter_pkg: AdapterPackage) -> None:
        result = adapter_pkg.dag_service.evaluate(
            _context(
                weapon={"hit_fighter": 100.0},
                user={"target_evasion": 100.0, "hit_rate_bonus": 100.0, "hit_rate_fluctuation": 3.0},
            )
        )
        assert _final_hit(result, "战机") == pytest.approx(0.98)

    def test_negative_fluctuation_is_added_after_clamp(self, adapter_pkg: AdapterPackage) -> None:
        result = adapter_pkg.dag_service.evaluate(
            _context(
                weapon={"hit_fighter": 0.0},
                user={"target_evasion": 0.0, "hit_rate_bonus": 0.0, "hit_rate_fluctuation": -3.0},
            )
        )
        assert _final_hit(result, "战机") == pytest.approx(0.02)

    def test_friendly_weapon_final_hit_is_fixed_at_one_hundred_percent(self, adapter_pkg: AdapterPackage) -> None:
        result = adapter_pkg.dag_service.evaluate(
            _context(
                weapon={"friendly": 1.0, "hit_fighter": 0.0},
                user={"target_evasion": 100.0, "hit_rate_bonus": 100.0, "hit_rate_fluctuation": 3.0},
            )
        )
        assert _final_hit(result, "战机") == pytest.approx(1.0)


class TestHitRateDamage:
    """DPM 使用各目标自己的最终命中率。"""

    def test_dpm_multiplies_full_hit_damage_by_final_hit(self, adapter_pkg: AdapterPackage) -> None:
        result = adapter_pkg.dag_service.evaluate(
            _context(
                weapon={"crit_rate": 0.0, "crit_damage": 0.0, "hit_fighter": 60.0, "hit_frigate": 85.0},
                user={
                    "bonus_crit_rate": 0.0,
                    "crit_multiplier_bonus": 0.0,
                    "target_evasion": 20.0,
                    "hit_rate_bonus": 10.0,
                    "hit_rate_fluctuation": 0.0,
                },
            )
        )
        full = result.outputs["满命中每分钟伤害"]
        assert result.outputs["最终每分钟伤害_战机"] == pytest.approx(full * (0.30 * 1.60))
        assert result.outputs["最终每分钟伤害_护卫舰"] == pytest.approx(full * (0.30 * 1.85))

    def test_zero_evasion_and_bonus_hit_the_five_percent_floor(self, adapter_pkg: AdapterPackage) -> None:
        result = adapter_pkg.dag_service.evaluate(
            _context(
                weapon={"hit_frigate": 85.0},
                user={"target_evasion": 0.0, "hit_rate_bonus": 0.0, "hit_rate_fluctuation": 0.0},
            )
        )
        full = result.outputs["满命中每分钟伤害"]
        assert result.outputs["最终每分钟伤害_护卫舰"] == pytest.approx(full * 0.05)

    def test_friendly_dpm_ignores_hit_rate_zone(self, adapter_pkg: AdapterPackage) -> None:
        result = adapter_pkg.dag_service.evaluate(
            _context(
                weapon={"friendly": 1.0, "hit_fighter": 0.0},
                user={"target_evasion": 0.0, "hit_rate_bonus": 0.0},
            )
        )
        full = result.outputs["满命中每分钟伤害"]
        assert result.outputs["最终每分钟伤害_战机"] == pytest.approx(full)


class TestHitRateDeclarations:
    """新输入与输出在 DAG / layout / attr_schema 中的声明。"""

    def test_all_targets_expose_final_hit_outputs(self, adapter_pkg: AdapterPackage) -> None:
        outputs = adapter_pkg.dag_service.dag.outputs
        for _, label in _TARGETS:
            name = f"最终命中率_{label}"
            assert name in outputs
            assert outputs[name].format == ".2%"
            assert outputs[name].is_primary is False

    def test_three_hit_rate_inputs_are_percentages(self, adapter_pkg: AdapterPackage) -> None:
        variables = adapter_pkg.dag_service.dag.variables
        for name in ("target_evasion", "hit_rate_bonus", "hit_rate_fluctuation"):
            path = f"user_input.{name}"
            assert path in variables
            assert variables[path].default == 0.0
            assert variables[path].ui_control.get("suffix") == "%"

        fluctuation = variables["user_input.hit_rate_fluctuation"]
        assert fluctuation.min == -3.0
        assert fluctuation.max == 3.0
        assert fluctuation.ui_control.get("step") == 0.1
        assert fluctuation.ui_control.get("widget") == "spinbox"

    def test_hit_rate_inputs_have_no_upper_limit_except_fluctuation(self, adapter_pkg: AdapterPackage) -> None:
        variables = adapter_pkg.dag_service.dag.variables
        assert variables["user_input.target_evasion"].max is None
        assert variables["user_input.hit_rate_bonus"].max is None

    def test_layout_has_hit_rate_input_and_output_sections(self) -> None:
        layout = json.loads((_ADAPTER_DIR / "ui" / "layout.json").read_text(encoding="utf-8"))
        sections = {section["id"]: section for section in layout["sections"]}

        inputs = sections["hit_rate_inputs"]
        assert inputs["tab"] == "计算"
        assert inputs["variables"] == [
            "user_input.target_evasion",
            "user_input.hit_rate_bonus",
            "user_input.hit_rate_fluctuation",
        ]

        outputs = sections["hit_rate_outputs"]
        assert outputs["tab"] == "乘区明细"
        assert outputs["columns"] == 3
        assert outputs["outputs"] == [f"最终命中率_{label}" for _, label in _TARGETS]

    def test_attr_schema_marks_hit_rate_inputs_as_user_input(self) -> None:
        schema = json.loads((_ADAPTER_DIR / "attr_schema.json").read_text(encoding="utf-8"))
        attrs = {attr["name"]: attr for attr in schema["attributes"]}
        for name in ("target_evasion", "hit_rate_bonus", "hit_rate_fluctuation"):
            assert attrs[name]["source"] == "user_input"
            assert attrs[name]["default"] == 0.0
