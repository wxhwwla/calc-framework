# SPDX-License-Identifier: AGPL-3.0
"""覆盖 survival/estimate, core/data_generator, formula 未覆盖函数。"""

from __future__ import annotations

from typing import Any

import pytest
from games.endfield.calc.core.data_generator import (
    generate_character_attributes,
    generate_weapon_attributes,
)
from games.endfield.calc.damage.formula import (
    calculate_bonus_attribute,
    has_fractional_part,
    infer_decimal_mode,
)
from games.endfield.calc.survival.estimate import build_survival_estimate

# ── formula.py ───────────────────────────────────────────────────────────


class TestFormulaHelpers:
    """has_fractional_part / infer_decimal_mode。"""

    def test_has_fractional_part_int(self) -> None:
        assert has_fractional_part(5) is False

    def test_has_fractional_part_float_whole(self) -> None:
        assert has_fractional_part(10.0) is False

    def test_has_fractional_part_true(self) -> None:
        assert has_fractional_part(5.4) is True

    def test_infer_decimal_explicit(self) -> None:
        assert infer_decimal_mode(1, 2, 3, is_decimal=True) is True
        assert infer_decimal_mode(1, 2, 3, is_decimal=False) is False

    def test_infer_decimal_from_params(self) -> None:
        assert infer_decimal_mode(1.5, 2, 3) is True
        assert infer_decimal_mode(1, 2.5, 3) is True
        assert infer_decimal_mode(1, 2, 3) is False

    def test_infer_decimal_from_special(self) -> None:
        assert infer_decimal_mode(1, 2, 3, special=[23.4]) is True
        assert infer_decimal_mode(1, 2, 3, special=[10]) is False


class TestCalculateBonusAttribute:
    """calculate_bonus_attribute。"""

    def test_basic_integer(self) -> None:
        result = calculate_bonus_attribute(100, 50, 10)
        assert len(result) == 9
        assert result[0] == 100.0
        assert result[8] == 140.0

    def test_decimal_mode(self) -> None:
        result = calculate_bonus_attribute(8.9, 6.2, 10)
        assert len(result) == 9

    def test_with_special(self) -> None:
        result = calculate_bonus_attribute(100, 20, 10, special=[150.0])
        assert len(result) == 9
        assert result[8] == 150.0

    def test_custom_max_level(self) -> None:
        result = calculate_bonus_attribute(100, 50, 10, max_level=5)
        assert len(result) == 5

    def test_invalid_divisor(self) -> None:
        with pytest.raises(ValueError):
            calculate_bonus_attribute(100, 50, 0)


# ── survival/estimate.py ─────────────────────────────────────────────────


class TestSurvivalEstimate:
    """build_survival_estimate。"""

    def test_basic(self) -> None:
        char = {"名称": "测试", "主能力": "力量", "副能力": "敏捷", "力量": [100.0], "敏捷": [80.0]}
        weapon = {"名称": "测试武器", "基础攻击力": [100.0]}
        result = build_survival_estimate(
            char_data=char,
            weapon_data=weapon,
            char_level=1,
            weapon_level=1,
            enemy_tier="普通",
        )
        assert isinstance(result, dict)
        assert "execute_damage" in result
        assert "imbalance_cap" in result
        assert "burn_tick_per_sec" in result
        assert "sp_after_regen" in result

    def test_with_full_params(self) -> None:
        char = {"名称": "测试", "主能力": "力量", "副能力": "敏捷", "力量": [100.0], "敏捷": [80.0]}
        weapon = {"名称": "测试武器", "基础攻击力": [100.0]}
        result = build_survival_estimate(
            char_data=char,
            weapon_data=weapon,
            char_level=1,
            weapon_level=1,
            trust_level=0,
            enemy_tier="精英",
            imbalance_efficiency_bonus=0.20,
            enemy_max_hp=10000.0,
            enemy_id="",
            sp_start=0.0,
            sp_seconds=10.0,
            ult_start=0.0,
            life_steal_rate=0.10,
        )
        assert result["execute_damage"] > 0
        assert result["imbalance_gain_effective"] > 0


# ── core/data_generator.py ──────────────────────────────────────────────


class TestDataGenerator:
    """generate_character_attributes / generate_weapon_attributes。"""

    def test_generate_character_attributes_basic(self) -> None:
        params: dict[str, Any] = {
            "力量": {"base": 100, "growth": 50, "divisor": 10},
            "敏捷": {"base": 80, "growth": 40, "divisor": 10},
            "基础攻击力": {"base": 500, "growth": 30, "divisor": 10},
            "战技倍率": [{"base": 100, "growth": 20, "divisor": 10}],
            "连携技倍率": [],
            "终结技倍率": [],
        }
        result = generate_character_attributes(params)
        assert "力量" in result
        assert len(result["力量"]) == 90
        assert result["力量"][0] == 100.0
        assert "战技倍率" in result

    def test_generate_character_attributes_empty_skills(self) -> None:
        params: dict[str, Any] = {
            "力量": {"base": 100, "growth": 50, "divisor": 10},
            "敏捷": {"base": 80, "growth": 40, "divisor": 10},
            "基础攻击力": {"base": 500, "growth": 30, "divisor": 10},
            "战技倍率": [],
            "连携技倍率": [],
            "终结技倍率": [],
        }
        result = generate_character_attributes(params)
        assert result["战技倍率"] == []
        assert result["连携技倍率"] == []

    def test_generate_weapon_attributes_basic(self) -> None:
        params: dict[str, Any] = {
            "基础攻击力": {"base": 100, "growth": 50, "divisor": 10},
        }
        result = generate_weapon_attributes(params)
        assert "基础攻击力" in result
        assert len(result["基础攻击力"]) == 90

    def test_generate_weapon_attributes_with_bonus_keys(self) -> None:
        params: dict[str, Any] = {
            "基础攻击力": {"base": 100, "growth": 50, "divisor": 10},
            "攻击力+": {"base": 5, "growth": 5, "divisor": 10},
        }
        result = generate_weapon_attributes(params)
        assert "基础攻击力" in result
        assert "攻击力+" in result
