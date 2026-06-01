#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""NGA 第十一批：EnemyEvalParams Web 接缝、逐 hit 破防、搜索请求组装。"""

import unittest
from types import SimpleNamespace

from games.endfield.calc.damage.physical_abnormal_state import break_defense_stacks_at_hit
from games.endfield.calc.loadout.slot_search import FixedLoadoutSelection
from games.endfield.data_loading.enemy_eval_params import (
    EnemyEvalParams,
    build_search_job_inputs_from_request,
)


class TestNgaBatch11(unittest.TestCase):
    def test_from_request_clamps_stacks(self) -> None:
        req = SimpleNamespace(
            enemy_defense=200.0,
            combo_stacks=9,
            break_defense_stacks=-1,
            attached_effect_multiplier=1.25,
            corrosion_duration_seconds=20.0,
        )
        params = EnemyEvalParams.from_request(req)
        self.assertEqual(params.combo_stacks, 4)
        self.assertEqual(params.break_defense_stacks, 0)
        self.assertAlmostEqual(params.attached_effect_multiplier, 1.25)
        self.assertAlmostEqual(params.corrosion_duration_seconds, 20.0)

    def test_abnormal_eval_kwargs(self) -> None:
        params = EnemyEvalParams(attached_effect_multiplier=1.5, corrosion_duration_seconds=10.0)
        kw = params.abnormal_eval_kwargs()
        self.assertAlmostEqual(kw["attached_effect_multiplier"], 1.5)
        self.assertAlmostEqual(kw["corrosion_duration_seconds"], 10.0)

    def test_break_defense_stacks_at_hit(self) -> None:
        self.assertEqual(break_defense_stacks_at_hit(4, 1), 4)
        self.assertEqual(break_defense_stacks_at_hit(4, 2), 3)
        self.assertEqual(break_defense_stacks_at_hit(4, 5), 0)

    def test_build_search_job_inputs_from_request(self) -> None:
        req = SimpleNamespace(
            char_data={"名称": "T"},
            char_level=90,
            weapon_level=90,
            trust_level=0,
            skill_name="战技",
            skill_type="战技",
            skill_multiplier=1.0,
            damage_type="物理",
            weapon_scope_label="同类型",
            equipment_scope_label="全部",
            all_weapons=[],
            current_weapon={},
            equipment_catalog={},
            use_manual_multi_skill_counts=False,
            skill_1_level=8,
            skill_2_level=8,
            skill_3_level=8,
            manual_counts=None,
            physical_abnormal_counts=None,
            spell_abnormal_counts=None,
            damage_component_mode="skill_and_abnormal",
            use_expected_crit=False,
            extra_crit_rate=0.0,
            extra_crit_damage=0.0,
            enemy_defense=150.0,
            is_true_damage=True,
            combo_stacks=2,
            break_defense_stacks=3,
            attached_effect_multiplier=1.1,
            corrosion_duration_seconds=12.0,
        )
        fixed = FixedLoadoutSelection()
        inputs = build_search_job_inputs_from_request(req, fixed_loadout=fixed)
        self.assertEqual(inputs.enemy_defense, 150.0)
        self.assertTrue(inputs.is_true_damage)
        self.assertEqual(inputs.combo_stacks, 2)
        self.assertEqual(inputs.break_defense_stacks, 3)
        self.assertAlmostEqual(inputs.attached_effect_multiplier, 1.1)
        self.assertAlmostEqual(inputs.corrosion_duration_seconds, 12.0)
        self.assertIs(inputs.fixed_loadout, fixed)


if __name__ == "__main__":
    unittest.main()
