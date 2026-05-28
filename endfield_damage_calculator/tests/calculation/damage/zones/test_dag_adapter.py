#!/usr/bin/env python3
"""DAG 适配器：将 DAG 引擎接入现有 zone_snapshot 计算链的测试。"""

import json
import unittest
from pathlib import Path
from typing import Any

from calculation.multiplicative_zones.zone_snapshot import (
    MultiplicativeZoneSelection,
    WeaponBonusSelection,
)
from tests.conftest import PKG_ROOT

_CHARACTERS_JSON = PKG_ROOT / "character_weapon_equipment" / "character_data" / "characters.json"
_WEAPONS_JSON = PKG_ROOT / "character_weapon_equipment" / "weapon_data" / "weapons.json"


def _load_by_name(path: Path, name: str) -> dict:
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    for item in data:
        if item.get("名称") == name:
            return item
    raise KeyError(name)


class TestDAGAdapter(unittest.TestCase):
    char: dict[str, Any]
    weapon: dict[str, Any]
    level: int

    def setUp(self):
        self.char = _load_by_name(_CHARACTERS_JSON, "秋栗")
        self.weapon = _load_by_name(_WEAPONS_JSON, "逐鳞3.0")
        self.level = 80

    def test_dag_adapter_imports(self):
        from calculation.multiplicative_zones.dag.adapter import (
            build_dag_context,
            evaluate_attack_chain_via_dag,
        )
        self.assertTrue(callable(build_dag_context))
        self.assertTrue(callable(evaluate_attack_chain_via_dag))

    def test_build_dag_context_returns_all_required_keys(self):
        from calculation.multiplicative_zones.dag.adapter import build_dag_context

        ctx = build_dag_context(
            self.char, self.weapon,
            char_level=self.level, weapon_level=self.level, trust_level=0,
        )
        self.assertIn("character", ctx)
        self.assertIn("weapon", ctx)
        self.assertIn("equipment", ctx)
        self.assertIn("computed", ctx)
        self.assertIn("基础攻击", ctx["character"])
        self.assertIn("基础攻击", ctx["weapon"])
        self.assertIn("攻击力+", ctx["weapon"])
        self.assertIn("附加攻击力+", ctx["weapon"])
        self.assertIn("攻击力平值", ctx["equipment"])
        self.assertIn("主能力平值加算", ctx["computed"])
        self.assertIn("主能力百分比", ctx["computed"])

    def test_evaluate_attack_chain_via_dag_matches_existing_engine(self):
        from calculation.multiplicative_zones.ability_bonus_details import (
            calculate_ability_bonus_with_details,
        )
        from calculation.multiplicative_zones.dag.adapter import evaluate_attack_chain_via_dag
        from calculation.multiplicative_zones.final_attack_zone import (
            calculate_final_attack_with_details,
        )

        existing_final = calculate_final_attack_with_details(
            self.char, self.weapon,
            char_level=self.level, weapon_level=self.level, trust_level=0,
        )
        existing_ability = calculate_ability_bonus_with_details(
            self.char, self.weapon, level=self.level, trust_level=0,
        )

        dag_result = evaluate_attack_chain_via_dag(
            self.char, self.weapon,
            char_level=self.level, weapon_level=self.level, trust_level=0,
        )

        self.assertIn("final_attack", dag_result)
        self.assertIn("ability_bonus", dag_result)
        self.assertAlmostEqual(
            dag_result["final_attack"], existing_final["final_attack"], places=6,
            msg=f"DAG final_attack={dag_result['final_attack']} vs existing={existing_final['final_attack']}",
        )
        self.assertAlmostEqual(
            dag_result["ability_bonus"], existing_ability["bonus"], places=6,
            msg=f"DAG ability_bonus={dag_result['ability_bonus']} vs existing={existing_ability['bonus']}",
        )

    def test_dag_adapted_snapshot_matches_existing_snapshot(self):
        from calculation.multiplicative_zones.dag.adapter import compute_snapshot_with_dag

        selection = MultiplicativeZoneSelection(
            character=self.char,
            weapon=self.weapon,
            char_level=self.level,
            weapon_level=self.level,
            bonuses=WeaponBonusSelection(),
        )
        dag_lines = compute_snapshot_with_dag(selection)
        texts = [line.text for line in dag_lines]

        self.assertTrue(any(t.startswith("敌方防御减伤:") for t in texts),
                        "缺少防御减伤行")
        self.assertTrue(any(t.startswith("能力值加成:") for t in texts),
                        "缺少能力值加成行")
        self.assertTrue(any(t.startswith("基础攻击力:") for t in texts),
                        "缺少基础攻击力行")
        self.assertTrue(any(t.startswith("最终伤害:") for t in texts),
                        "缺少最终伤害行")
        self.assertTrue(any(t.startswith("力量:") for t in texts),
                        "缺少属性行")

        dag_final = [line for line in dag_lines if line.text.startswith("最终伤害:")][0]
        dag_val = float(dag_final.text.split(":")[1].strip())
        self.assertGreater(dag_val, 0, "最终伤害应为正数")

    def test_dag_adapter_with_weapon_bonuses(self):
        from calculation.multiplicative_zones.dag.adapter import compute_snapshot_with_dag

        selection = MultiplicativeZoneSelection(
            character=self.char,
            weapon=self.weapon,
            char_level=self.level,
            weapon_level=self.level,
            bonuses=WeaponBonusSelection(
                normal_skill_1_name="智识+",
                normal_skill_1_level=9,
                special_skill_1_name="源石技艺强度+",
                special_skill_1_level=9,
                special_skill_1_stack=0,
            ),
        )
        dag = compute_snapshot_with_dag(selection)

        self.assertGreater(len(dag), 0)
        final_line = [ln for ln in dag if ln.text.startswith("最终伤害:")][0]
        dag_val = float(final_line.text.split(":")[1].strip().split(" ")[0])
        self.assertGreater(dag_val, 0)
        self.assertTrue(any(ln.text.startswith("能力值加成:") for ln in dag))
        self.assertTrue(any(ln.text.startswith("攻击加成攻击力:") for ln in dag))
        self.assertTrue(any(ln.text.startswith("中间攻击力:") for ln in dag))


if __name__ == "__main__":
    unittest.main()
