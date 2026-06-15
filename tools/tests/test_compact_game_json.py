#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""compact_game_json 单元测试。"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from games.endfield.calc.damage.formula import calculate_growth_curve, calculate_skill_curve
from games.endfield.calc.damage.inverse.adapter import EndfieldInverseAdapter
from games.endfield.data_loading.curve_materialize import materialize_character_entity, materialize_weapon_entity
from tools.compact_game_json import compact_character, compact_weapon


def _linear_90(base: int, growth: int, divisor: int) -> list[float]:
    return calculate_growth_curve(base=base, growth=growth, divisor=divisor, offset=0)


def test_compact_character_roundtrip_normal_attrs() -> None:
    char = {
        "名称": "测试角色",
        "等级": list(range(1, 91)),
        "力量": _linear_90(21, 22, 98),
        "敏捷": _linear_90(10, 15, 50),
    }
    compacted, _ = compact_character(char, EndfieldInverseAdapter(), max_error=0.05)
    assert "成长参数" in compacted
    assert "力量" not in compacted
    baked = materialize_character_entity(compacted)
    assert baked["力量"] == pytest.approx(char["力量"], abs=0.01)


def test_compact_character_skill_with_special() -> None:
    skill = calculate_skill_curve(
        base=1.0,
        growth=10,
        divisor=98,
        offset=0,
        special_values=[2.3, 2.5, 2.7],
    )
    char = {
        "名称": "技能测试",
        "等级": list(range(1, 91)),
        "战技倍率": [skill],
    }
    compacted, warns = compact_character(char, EndfieldInverseAdapter(), max_error=0.05)
    assert not warns or all("不一致" not in w for w in warns)
    assert "成长参数" in compacted
    baked = materialize_character_entity(compacted)
    assert baked["战技倍率"][0] == pytest.approx(skill, abs=0.01)


def test_compact_weapon_base_atk() -> None:
    values = _linear_90(100, 50, 99)
    weapon = {"名称": "测试武器", "等级": list(range(1, 91)), "基础攻击力": values}
    compacted, _ = compact_weapon(weapon, EndfieldInverseAdapter(), max_error=0.05)
    assert "成长参数" in compacted
    baked = materialize_weapon_entity(compacted)
    assert baked["基础攻击力"] == pytest.approx(values, abs=0.01)
