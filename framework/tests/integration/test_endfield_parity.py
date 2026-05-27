#!/usr/bin/env python3
"""终末地 DAG 引擎与现有引擎的对比集成测试。"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from calc_framework.dag.engine import evaluate_graph
from calc_framework.dag.serializer import load_dag

_REPO_ROOT = Path(__file__).resolve().parents[3]
_PKG_ROOT = _REPO_ROOT / "endfield_damage_calculator"
if str(_PKG_ROOT) not in sys.path:
    sys.path.insert(0, str(_PKG_ROOT))

PARTICIPANTS_JSON = (
    _PKG_ROOT / "character_weapon_equipment" / "character_data" / "characters.json"
)
WEAPONS_JSON = (
    _PKG_ROOT / "character_weapon_equipment" / "weapon_data" / "weapons.json"
)
DAG_FIXTURE_PATH = (
    _REPO_ROOT / "framework" / "tests" / "fixtures" / "endfield_attack_chain.dag.json"
)


def _load_by_name(path: Path, name: str) -> dict:
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    for item in data:
        if item.get("名称") == name:
            return item
    raise KeyError(name)


def _get_attr_at_level(char: dict, attr_name: str, level: int) -> float:
    values = char.get(attr_name, [])
    if isinstance(values, list) and 0 <= level - 1 < len(values):
        return float(values[level - 1])
    return 0.0


def _get_weapon_attr_at_level(weapon: dict, attr_name: str, level: int) -> float:
    values = weapon.get(attr_name, [])
    if isinstance(values, list) and 0 <= level - 1 < len(values):
        return float(values[level - 1])
    if isinstance(values, (int, float)):
        return float(values)
    return 0.0


@pytest.fixture(scope="module")
def endfield_attack_dag():
    return load_dag(DAG_FIXTURE_PATH)


@pytest.fixture(scope="module")
def default_context():
    from calculation.multiplicative_zones.final_attack_zone import calculate_final_attack_with_details

    char = _load_by_name(PARTICIPANTS_JSON, "秋栗")
    weapon = _load_by_name(WEAPONS_JSON, "逐鳞3.0")
    level = 80

    existing = calculate_final_attack_with_details(
        char, weapon, char_level=level, weapon_level=level, trust_level=0,
    )

    return {
        "角色": {
            "基础攻击": existing["char_base_attack"],
        },
        "武器": {
            "基础攻击": existing["weapon_base_attack"],
            "攻击加成": existing["attack_bonus_multiplier"],
            "附加攻击": existing["additional_attack"],
        },
        "computed": {
            "能力乘数": 1.0 + existing["ability_bonus"],
        },
    }


class TestEndfieldAttackDAG:
    def test_loads_successfully(self, endfield_attack_dag):
        assert endfield_attack_dag.name == "终末地伤害公式"
        assert len(endfield_attack_dag.nodes) == 9

    def test_final_attack_positive(self, endfield_attack_dag, default_context):
        result = evaluate_graph(endfield_attack_dag, default_context)
        assert result.outputs["最终攻击力"] > 0

    def test_matches_existing_engine(self, endfield_attack_dag, default_context):
        from calculation.multiplicative_zones.final_attack_zone import calculate_final_attack_with_details

        char = _load_by_name(PARTICIPANTS_JSON, "秋栗")
        weapon = _load_by_name(WEAPONS_JSON, "逐鳞3.0")
        level = 80

        existing = calculate_final_attack_with_details(
            char, weapon, char_level=level, weapon_level=level, trust_level=0,
        )
        result = evaluate_graph(endfield_attack_dag, default_context)

        dag_final = result.outputs["最终攻击力"]
        existing_final = existing["final_attack"]
        assert dag_final == pytest.approx(existing_final, rel=1e-6), (
            f"DAG: {dag_final}, Existing: {existing_final}"
        )
