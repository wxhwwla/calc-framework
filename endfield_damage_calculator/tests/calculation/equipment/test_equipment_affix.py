#!/usr/bin/env python3
"""装备属性词条解析测试。"""

import unittest

from calculation.damage.engine import DamageContext, calculate_single_hit_damage
from calculation.equipment.affix import (
    parse_equipment_affix_line,
)
from calculation.equipment.system import (
    build_runtime_equipment_from_local_record,
)
from calculation.loadout.optimizer import evaluate_task
from calculation.search.evaluate.context import SearchEvalContext


class TestEquipmentAffix(unittest.TestCase):
    def test_parse_skill_damage_bonus_scoped(self):
        effs, flats = parse_equipment_affix_line("战技伤害加成41.40%", source="测试")
        self.assertEqual(flats, {})
        self.assertEqual(len(effs), 1)
        self.assertEqual(effs[0].effect_type, "技能类型伤害加成")
        self.assertAlmostEqual(effs[0].value, 0.414)
        self.assertEqual(effs[0].skill_types, ("战技",))

        link_effs, _ = parse_equipment_affix_line("连携技伤害加成21.00%", source="测试")
        self.assertEqual(len(link_effs), 1)
        self.assertEqual(link_effs[0].skill_types, ("连携技",))

    def test_parse_flat_main_stat(self):
        _, flats = parse_equipment_affix_line("敏捷21", source="测试")
        self.assertAlmostEqual(flats["敏捷"], 21.0)

    def test_parse_attack_percent_affix(self):
        effs, flats = parse_equipment_affix_line("攻击力12.30%", source="测试")
        self.assertEqual(flats, {})
        self.assertEqual(len(effs), 1)
        self.assertEqual(effs[0].effect_type, "装备攻击力加成")
        self.assertAlmostEqual(effs[0].value, 0.123)

    def test_runtime_record_includes_affix_effects(self):
        runtime = build_runtime_equipment_from_local_record(
            {
                "名称": "测试配件",
                "装备种类": "配件",
                "属性词条": ["战技伤害加成20.00%"],
                "效果": [],
                "三件套效果": [],
            }
        )
        self.assertEqual(len(runtime["效果"]), 1)
        self.assertEqual(runtime["效果"][0].skill_types, ("战技",))

    def test_evaluate_task_prefers_war_skill_damage_affix(self):
        char = {
            "名称": "测试",
            "主能力": "敏捷",
            "副能力": "力量",
            "基础攻击力": [100.0] * 90,
            "敏捷": [10.0] * 90,
            "力量": [10.0] * 90,
        }
        weapon = {"名称": "武", "类型": "单手剑", "基础攻击力": [50.0] * 90}
        war_acc = build_runtime_equipment_from_local_record(
            {
                "名称": "战技件",
                "装备种类": "配件",
                "属性词条": ["战技伤害加成50.00%"],
                "效果": [],
                "三件套效果": [],
            }
        )
        link_acc = build_runtime_equipment_from_local_record(
            {
                "名称": "连携件",
                "装备种类": "配件",
                "属性词条": ["连携技伤害加成50.00%"],
                "效果": [],
                "三件套效果": [],
            }
        )
        neutral_acc = build_runtime_equipment_from_local_record(
            {
                "名称": "白板件",
                "装备种类": "配件",
                "属性词条": [],
                "效果": [],
                "三件套效果": [],
            }
        )
        filler_chest = build_runtime_equipment_from_local_record(
            {
                "名称": "甲",
                "装备种类": "护甲",
                "属性词条": [],
                "效果": [],
                "三件套效果": [],
            }
        )
        filler_gloves = build_runtime_equipment_from_local_record(
            {
                "名称": "手",
                "装备种类": "护手",
                "属性词条": [],
                "效果": [],
                "三件套效果": [],
            }
        )
        ctx = SearchEvalContext(
            char_data=char,
            char_level=1,
            weapon_level=1,
            trust_level=0,
            weapon_data_by_name={"武": weapon},
        )
        from calculation.loadout.optimizer import WeaponCandidate
        from calculation.multiplicative_zones.final_attack_zone import (
            calculate_final_attack_with_details,
        )

        fa = calculate_final_attack_with_details(character=char, weapon=weapon, char_level=1, weapon_level=1)[
            "final_attack"
        ]
        base = DamageContext(
            final_attack=fa,
            skill_multiplier=1.0,
            skill_type="战技",
            enemy_defense=0.0,
        )
        war_score = evaluate_task(
            base_context=base,
            crit_mode="non_crit",
            task=(
                WeaponCandidate(name="武", final_attack=fa),
                (filler_chest, filler_gloves, war_acc, neutral_acc),
            ),
            search_eval=ctx,
        )
        link_score = evaluate_task(
            base_context=base,
            crit_mode="non_crit",
            task=(
                WeaponCandidate(name="武", final_attack=fa),
                (filler_chest, filler_gloves, link_acc, neutral_acc),
            ),
            search_eval=ctx,
        )
        self.assertGreater(war_score.final_damage, link_score.final_damage)

    def test_skill_bonus_only_applies_to_matching_skill_type(self):
        effects, _ = parse_equipment_affix_line("连携技伤害加成30.00%", source="x")
        self.assertEqual(len(effects), 1)
        war_hit = calculate_single_hit_damage(
            DamageContext(
                final_attack=1000.0,
                skill_multiplier=1.0,
                skill_type="战技",
                enemy_defense=0.0,
            ),
            effects=effects,
        )
        link_hit = calculate_single_hit_damage(
            DamageContext(
                final_attack=1000.0,
                skill_multiplier=1.0,
                skill_type="连携技",
                enemy_defense=0.0,
            ),
            effects=effects,
        )
        self.assertAlmostEqual(war_hit.final_damage, 1000.0)
        self.assertGreater(link_hit.final_damage, 1000.0)


if __name__ == "__main__":
    unittest.main()
