#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""技能段场景与段级次数测试。"""

import unittest

from games.endfield.calc.damage.engine import DamageContext
from games.endfield.calc.loadout.optimizer import WeaponCandidate
from games.endfield.calc.multi_skill.optimizer import evaluate_multi_skill_task
from games.endfield.calc.skills.segments import (
    aggregate_weighted_damage,
    build_segment_scenarios_from_levels,
    format_segment_breakdown_lines,
    list_segment_count_specs,
    normalize_manual_segment_counts,
)


class TestSkillSegments(unittest.TestCase):
    def _multi_segment_char(self) -> dict:
        return {
            "名称": "多段测试",
            "战技倍率": [[350] * 12],
            "连携技倍率": [[100] * 12, [400] * 12],
            "终结技倍率": [[800] * 12, [600] * 12],
            "基础攻击力": [100] * 12,
        }

    def test_build_segment_scenarios_lists_all_valid_segments(self) -> None:
        scenarios = build_segment_scenarios_from_levels(
            self._multi_segment_char(),
            skill_1_level=12,
            skill_2_level=12,
            skill_3_level=12,
        )
        keys = [s.scenario_key for s in scenarios]
        self.assertEqual(
            keys,
            ["战技:1", "连携技:1", "连携技:2", "终结技:1", "终结技:2"],
        )
        self.assertAlmostEqual(scenarios[1].skill_multiplier, 1.0)
        self.assertAlmostEqual(scenarios[2].skill_multiplier, 4.0)

    def test_legacy_skill_type_count_maps_to_first_segment(self) -> None:
        scenarios = build_segment_scenarios_from_levels(
            self._multi_segment_char(),
            skill_1_level=12,
            skill_2_level=12,
            skill_3_level=0,
        )
        normalized = normalize_manual_segment_counts({"连携技": 2}, scenarios)
        self.assertEqual(normalized["连携技:1"], 2)
        self.assertEqual(normalized["连携技:2"], 0)

    def test_combat_multiplier_field_overrides_display(self) -> None:
        char = {
            "名称": "实战倍率测试",
            "战技倍率": [[350] * 12],
            "战技实战倍率": [[348] * 12],
            "连携技倍率": [],
            "终结技倍率": [],
        }
        scenarios = build_segment_scenarios_from_levels(
            char,
            skill_1_level=12,
            skill_2_level=0,
            skill_3_level=0,
        )
        self.assertEqual(len(scenarios), 1)
        self.assertAlmostEqual(scenarios[0].skill_multiplier, 3.48)
        specs = list_segment_count_specs(
            char,
            skill_1_level=12,
            skill_2_level=0,
            skill_3_level=0,
        )
        self.assertIn("350%→348%", specs[0]["label"])

    def test_two_hits_first_segment_one_hit_second_segment(self) -> None:
        weapon = WeaponCandidate(name="W", final_attack=1000.0)
        task = (
            weapon,
            (
                {"名称": "胸", "装备种类": "护甲"},
                {"名称": "手", "部位": "护手"},
                {"名称": "A", "部位": "配件"},
                {"名称": "B", "部位": "配件"},
            ),
        )
        scenarios = tuple(
            build_segment_scenarios_from_levels(
                self._multi_segment_char(),
                skill_1_level=0,
                skill_2_level=12,
                skill_3_level=0,
            )
        )
        counts = {"连携技:1": 2, "连携技:2": 1}
        score = evaluate_multi_skill_task(
            shared_context=DamageContext(final_attack=0.0, skill_multiplier=1.0, enemy_defense=0.0),
            crit_mode="non_crit",
            task=task,
            scenarios=scenarios,
            skill_counts=counts,
        )
        single_seg1 = score.segment_breakdown["连携技:1"]
        single_seg2 = score.segment_breakdown["连携技:2"]
        expected = single_seg1 * 2 + single_seg2 * 1
        self.assertAlmostEqual(score.final_damage, expected)

    def test_format_breakdown_shows_segment_and_skill_totals(self) -> None:
        breakdown = {"连携技:1": 100.0, "连携技:2": 400.0}
        counts = {"连携技:1": 2, "连携技:2": 1}
        lines = format_segment_breakdown_lines(breakdown, counts)
        text = "\n".join(lines)
        self.assertIn("第1段: 单次 100.0 ×2 = 200.0", text)
        self.assertIn("第2段: 单次 400.0 ×1 = 400.0", text)
        self.assertIn("连携技 合计: 600.0", text)

    def test_multi_segment_damage_types_affect_weighted_total(self) -> None:
        char = {
            "名称": "类型测试",
            "战技倍率": [[100] * 12],
            "连携技倍率": [[100] * 12, [100] * 12],
            "连携技段伤害类型": ["物理", "法术-灼热"],
            "终结技倍率": [],
        }
        weapon = WeaponCandidate(name="W", final_attack=1000.0)
        task = (
            weapon,
            (
                {"名称": "胸", "装备种类": "护甲"},
                {"名称": "手", "部位": "护手"},
                {"名称": "A", "部位": "配件"},
                {"名称": "B", "部位": "配件"},
            ),
        )
        scenarios = tuple(
            build_segment_scenarios_from_levels(
                char,
                skill_1_level=0,
                skill_2_level=12,
                skill_3_level=0,
            )
        )
        self.assertEqual(scenarios[0].damage_type, "物理")
        self.assertEqual(scenarios[1].damage_type, "法术-灼热")
        from games.endfield.calc.damage.engine import DamageEffect

        effect = DamageEffect(
            "伤害类型伤害加成",
            value=0.5,
            damage_types=("法术-灼热",),
            source="test",
        )
        score = evaluate_multi_skill_task(
            shared_context=DamageContext(final_attack=0.0, skill_multiplier=1.0, enemy_defense=0.0),
            crit_mode="non_crit",
            task=(
                WeaponCandidate(name="W", final_attack=1000.0, effects=(effect,)),
                task[1],
            ),
            scenarios=scenarios,
            skill_counts={"连携技:1": 1, "连携技:2": 1},
        )
        seg1 = score.segment_breakdown["连携技:1"]
        seg2 = score.segment_breakdown["连携技:2"]
        self.assertAlmostEqual(seg1, 1000.0)
        self.assertAlmostEqual(seg2, 1500.0)
        self.assertAlmostEqual(score.final_damage, 2500.0)

    def test_aggregate_weighted_damage(self) -> None:
        total, seg_totals, skill_totals = aggregate_weighted_damage(
            {"战技:1": 50.0, "连携技:1": 100.0, "连携技:2": 200.0},
            {"战技:1": 1, "连携技:1": 2, "连携技:2": 1},
        )
        self.assertAlmostEqual(total, 50.0 + 200.0 + 200.0)
        self.assertAlmostEqual(skill_totals["连携技"], 400.0)


if __name__ == "__main__":
    unittest.main()
