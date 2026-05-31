# SPDX-License-Identifier: AGPL-3.0
from __future__ import annotations

import unittest

from games.endfield.calc.loadout.optimizer import (
    LoadoutScore,
    OptimizerConfig,
    OptimizerResult,
    RuntimeEvalSnapshot,
    WeaponCandidate,
)
from games.endfield.calc.loadout.slot_search import FixedLoadoutSelection


class TestWeaponCandidate(unittest.TestCase):
    def test_defaults(self) -> None:
        w = WeaponCandidate(name="测试剑", final_attack=100.0)
        self.assertEqual(w.name, "测试剑")
        self.assertEqual(w.final_attack, 100.0)
        self.assertEqual(w.effects, ())

    def test_with_effects(self) -> None:
        w = WeaponCandidate(name="特效剑", final_attack=200.0, effects=(("攻+10%", "+10%"),))
        self.assertEqual(len(w.effects), 1)

    def test_equality(self) -> None:
        w1 = WeaponCandidate(name="剑", final_attack=100.0)
        w2 = WeaponCandidate(name="剑", final_attack=100.0)
        self.assertEqual(w1, w2)


class TestOptimizerConfig(unittest.TestCase):
    def test_defaults(self) -> None:
        c = OptimizerConfig()
        self.assertEqual(c.top_n, 10)
        self.assertEqual(c.crit_mode, "non_crit")
        self.assertIsInstance(c.fixed_loadout, FixedLoadoutSelection)
        self.assertIsNone(c.varying_slot_count)
        self.assertEqual(c.priority_skill_types, ())

    def test_custom(self) -> None:
        c = OptimizerConfig(
            top_n=20,
            crit_mode="max",
            varying_slot_count=2,
            priority_skill_types=("战技",),
            candidate_weapon_names={"剑", "刀"},
        )
        self.assertEqual(c.top_n, 20)
        self.assertEqual(c.varying_slot_count, 2)
        self.assertEqual(c.candidate_weapon_names, {"剑", "刀"})


class TestLoadoutScore(unittest.TestCase):
    def test_basic(self) -> None:
        s = LoadoutScore(
            weapon_name="测试剑",
            final_damage=5000.0,
            loadout_names={"chest": "甲", "gloves": "手"},
        )
        self.assertEqual(s.weapon_name, "测试剑")
        self.assertEqual(s.final_damage, 5000.0)
        self.assertEqual(s.loadout_names["chest"], "甲")
        self.assertIsNone(s.segment_breakdown)

    def test_with_segment_breakdown(self) -> None:
        s = LoadoutScore(
            weapon_name="多段剑",
            final_damage=10000.0,
            loadout_names={},
            segment_breakdown={"战技:1": 3000.0, "连携技:1": 7000.0},
        )
        self.assertEqual(s.segment_breakdown["战技:1"], 3000.0)

    def test_equality(self) -> None:
        s1 = LoadoutScore(weapon_name="剑", final_damage=100.0, loadout_names={})
        s2 = LoadoutScore(weapon_name="剑", final_damage=100.0, loadout_names={})
        self.assertEqual(s1, s2)


class TestRuntimeEvalSnapshot(unittest.TestCase):
    def test_basic(self) -> None:
        snap = RuntimeEvalSnapshot(
            weapon_name="测试剑",
            final_attack=1500.0,
            effects=(("攻+5%", "5%"),),
            loadout_names={"chest": "甲"},
        )
        self.assertEqual(snap.weapon_name, "测试剑")
        self.assertEqual(snap.final_attack, 1500.0)
        self.assertEqual(len(snap.effects), 1)


class TestOptimizerResult(unittest.TestCase):
    def test_empty(self) -> None:
        r = OptimizerResult(
            top_results=(),
            total_combinations=0,
            searched_combinations=0,
            pruned_weapon_count=0,
            warnings=(),
        )
        self.assertEqual(len(r.top_results), 0)
        self.assertEqual(r.total_combinations, 0)

    def test_with_results(self) -> None:
        score = LoadoutScore(weapon_name="剑", final_damage=100.0, loadout_names={})
        r = OptimizerResult(
            top_results=(score,),
            total_combinations=100,
            searched_combinations=50,
            pruned_weapon_count=2,
            warnings=("部分武器无候选",),
        )
        self.assertEqual(len(r.top_results), 1)
        self.assertEqual(r.top_results[0].final_damage, 100.0)
        self.assertIn("部分武器", r.warnings[0])
