#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""装备数据链路与四格装配测试。"""

import unittestfrom games.endfield.calc.damage.engine import DamageContext, calculate_single_hit_damagefrom games.endfield.calc.equipment.system import (    build_four_slot_loadout,    build_runtime_equipment_from_wiki_draft,    collect_loadout_effects,)class TestEquipmentSystem(unittest.TestCase):
    def test_build_runtime_equipment_from_wiki_draft(self):
        draft = {
            "名称": "测试胸甲",
            "_wiki_params": {
                "装备种类": "护甲",
                "套装": "寒霜协议",
                "效果1": "寒冷伤害+12%",
                "三件套效果1": "易伤+10%",
            },
        }
        runtime = build_runtime_equipment_from_wiki_draft(draft)
        self.assertEqual(runtime["装备种类"], "护甲")
        self.assertEqual(runtime["套装"], "寒霜协议")
        self.assertEqual(len(runtime["效果"]), 1)
        self.assertEqual(runtime["效果"][0].effect_type, "伤害类型伤害加成")
        self.assertEqual(runtime["效果"][0].damage_types, ("法术-寒冷",))
        self.assertEqual(len(runtime["三件套效果"]), 1)
        self.assertEqual(runtime["三件套效果"][0].effect_type, "易伤")

    def test_four_slot_loadout_allows_duplicate_accessory(self):
        chest = build_runtime_equipment_from_wiki_draft(
            {
                "名称": "测试胸甲",
                "_wiki_params": {"装备种类": "护甲", "所属套组": "寒霜协议"},
            }
        )
        gloves = build_runtime_equipment_from_wiki_draft(
            {
                "名称": "测试护手",
                "_wiki_params": {"部位": "护手", "套装": "寒霜协议"},
            }
        )
        accessory = build_runtime_equipment_from_wiki_draft(
            {
                "名称": "测试配件",
                "_wiki_params": {"部位": "配件", "套装": "寒霜协议"},
            }
        )
        loadout = build_four_slot_loadout(
            chest=chest,
            gloves=gloves,
            accessory_a=accessory,
            accessory_b=accessory,
            allow_duplicate_accessory=True,
        )
        self.assertEqual(loadout.accessory_a["名称"], "测试配件")
        self.assertEqual(loadout.accessory_b["名称"], "测试配件")

    def test_three_piece_set_effect_applies_once(self):
        chest = build_runtime_equipment_from_wiki_draft(
            {
                "名称": "测试胸甲",
                "_wiki_params": {
                    "装备种类": "护甲",
                    "套装": "寒霜协议",
                    "三件套效果1": "易伤+10%",
                },
            }
        )
        gloves = build_runtime_equipment_from_wiki_draft(
            {
                "名称": "测试护手",
                "_wiki_params": {
                    "部位": "护手",
                    "套装": "寒霜协议",
                    "三件套效果1": "易伤+10%",
                },
            }
        )
        accessory = build_runtime_equipment_from_wiki_draft(
            {
                "名称": "测试配件",
                "_wiki_params": {
                    "部位": "配件",
                    "套装": "寒霜协议",
                    "三件套效果1": "易伤+10%",
                },
            }
        )
        loadout = build_four_slot_loadout(
            chest=chest,
            gloves=gloves,
            accessory_a=accessory,
            accessory_b=build_runtime_equipment_from_wiki_draft(
                {
                    "名称": "散件配件",
                    "_wiki_params": {"部位": "配件", "套装": "散件"},
                }
            ),
        )
        effects = collect_loadout_effects(loadout)
        result = calculate_single_hit_damage(
            DamageContext(final_attack=1000.0, skill_multiplier=1.0, enemy_defense=0.0),
            effects=effects,
        )
        self.assertAlmostEqual(result.zone_values["易伤区"], 1.1)
        self.assertAlmostEqual(result.final_damage, 1100.0)

    def test_unknown_effect_text_is_preserved_for_warning_pipeline(self):
        runtime = build_runtime_equipment_from_wiki_draft(
            {
                "名称": "未知词条配件",
                "_wiki_params": {
                    "部位": "配件",
                    "效果1": "神秘增伤+25%",
                },
            }
        )
        result = calculate_single_hit_damage(
            DamageContext(final_attack=1000.0, skill_multiplier=1.0, enemy_defense=0.0),
            effects=runtime["效果"],
        )
        self.assertEqual(len(result.unknown_effects), 1)
        self.assertTrue(any("神秘增伤" in w for w in result.warnings))


if __name__ == "__main__":
    unittest.main()
