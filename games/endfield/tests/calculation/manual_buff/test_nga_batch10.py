#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""NGA 第十批：EnemyEvalParams 预览接缝、破防轮转说明。"""

import unittest

from games.endfield.calc.damage.engine import DamageContext
from games.endfield.calc.damage.physical_abnormal_state import format_break_defense_rotation_note
from games.endfield.calc.loadout.slot_search import FixedLoadoutSelection
from games.endfield.data_loading.enemy_eval_params import EnemyEvalParams
from games.endfield.gui.app.loadout_state import LoadoutState


class TestNgaBatch10(unittest.TestCase):
    def test_enemy_eval_params_damage_context_fields(self) -> None:
        params = EnemyEvalParams(
            enemy_defense=250.0,
            break_defense_stacks=3,
            is_true_damage=True,
            combo_stacks=2,
        )
        ctx = DamageContext(**params.damage_context_fields(skill_multiplier=2.0))
        self.assertEqual(ctx.enemy_defense, 250.0)
        self.assertEqual(ctx.break_defense_stacks, 3)
        self.assertTrue(ctx.is_true_damage)
        self.assertEqual(ctx.combo_stacks, 2)

    def test_from_loadout_roundtrip(self) -> None:
        state = LoadoutState(
            char_data={"名称": "T", "武器": "单手剑", "战技倍率": [[100]], "基础攻击力": [100]},
            weapon_data={"名称": "W", "类型": "单手剑", "基础攻击力": [100]},
            char_level=1,
            weapon_level=1,
            trust_level=0,
            skill_levels=(1, 0, 0),
            skill_name="战技",
            skill_type="战技",
            skill_multiplier=1.0,
            damage_type="物理",
            calculation_mode="single_hit",
            weapon_scope_label="当前武器",
            equipment_scope_label="全部装备",
            fixed_loadout=FixedLoadoutSelection(),
            fixed_equipment_names={
                "chest": None,
                "gloves": None,
                "accessory_a": None,
                "accessory_b": None,
            },
            use_manual_multi_skill_counts=False,
            manual_counts={"战技": 1},
            enemy_defense=333.0,
            break_defense_stacks=2,
        )
        params = EnemyEvalParams.from_loadout(state)
        self.assertEqual(params.enemy_defense, 333.0)
        self.assertEqual(params.break_defense_stacks, 2)

    def test_break_defense_rotation_note(self) -> None:
        note = format_break_defense_rotation_note(4, {"战技:1": 2, "猛击:1": 3})
        self.assertIsNotNone(note)
        assert note is not None
        self.assertIn("→ 轮转后约 2", note)


if __name__ == "__main__":
    unittest.main()
