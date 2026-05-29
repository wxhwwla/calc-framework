#!/usr/bin/env python3
"""配装预设导入导出测试。"""

import json
import unittest

from gui_design.app.loadout_preset import (
    PRESET_SCHEMA,
    LoadoutPreset,
    export_preset_json,
    import_preset_json,
)


class TestLoadoutPreset(unittest.TestCase):
    def test_roundtrip_preserves_core_fields(self) -> None:
        preset = LoadoutPreset(
            char_name="测试干员",
            weapon_name="测试武器",
            char_level=80,
            weapon_level=90,
            trust_level=2,
            skill_levels=(10, 8, 0),
            calculation_mode="single_hit",
            weapon_scope="当前武器",
            equipment_scope="全部装备",
            fixed_equipment_names={
                "chest": "胸甲A",
                "gloves": None,
                "accessory_a": "配件1",
                "accessory_b": "配件2",
            },
            multi_skill_counts={"战技": 2, "连携技": 1, "终结技": 0},
            use_manual_multi_skill_counts=True,
            weapon_normal_levels=[9, 8, 1],
            weapon_special_states=[{"level": 7, "stack": 2}],
            physical_abnormal_counts={"猛击:2": 3},
            spell_abnormal_counts={"灼热爆发:1": 2},
            damage_component_mode="skill_and_abnormal",
            use_expected_crit=True,
            ui_state={
                "char_advanced_expanded": True,
                "weapon_advanced_expanded": False,
                "more_settings_expanded": True,
                "current_page": "高级页",
            },
        )
        text = export_preset_json(preset)
        restored = import_preset_json(text)
        self.assertEqual(restored.char_name, preset.char_name)
        self.assertEqual(restored.fixed_equipment_names["chest"], "胸甲A")
        self.assertTrue(restored.use_manual_multi_skill_counts)
        self.assertTrue(bool((restored.ui_state or {}).get("char_advanced_expanded")))
        self.assertFalse(bool((restored.ui_state or {}).get("weapon_advanced_expanded")))
        self.assertEqual((restored.ui_state or {}).get("current_page"), "高级页")
        self.assertEqual(restored.physical_abnormal_counts.get("猛击:2"), 3)
        self.assertEqual(restored.spell_abnormal_counts.get("灼热爆发:1"), 2)
        self.assertTrue(restored.use_expected_crit)
        self.assertEqual(restored.weapon_normal_levels, [9, 8, 1])
        self.assertEqual(restored.weapon_special_states, [{"level": 7, "stack": 2}])

    def test_rejects_unknown_schema(self) -> None:
        with self.assertRaises(ValueError):
            import_preset_json(json.dumps({"schema": "other_v9"}))

    def test_export_uses_v2_schema(self) -> None:
        preset = LoadoutPreset(
            char_name="测试干员",
            weapon_name="测试武器",
            char_level=80,
            weapon_level=90,
            trust_level=2,
            skill_levels=(10, 8, 0),
            calculation_mode="single_hit",
            weapon_scope="当前武器",
            equipment_scope="全部装备",
            fixed_equipment_names={"chest": None, "gloves": None, "accessory_a": None, "accessory_b": None},
            multi_skill_counts={},
            use_manual_multi_skill_counts=False,
        )
        exported = json.loads(export_preset_json(preset))
        self.assertEqual(exported["schema"], PRESET_SCHEMA)
        self.assertEqual(PRESET_SCHEMA, "endfield_loadout_preset_v2")

    def test_import_v1_legacy_weapon_levels_maps_to_new_fields(self) -> None:
        data = {
            "schema": "endfield_loadout_preset_v1",
            "char_name": "测试干员",
            "weapon_name": "测试武器",
            "char_level": 80,
            "weapon_level": 90,
            "trust_level": 2,
            "skill_levels": [10, 8, 0],
            "calculation_mode": "single_hit",
            "weapon_scope": "当前武器",
            "equipment_scope": "全部装备",
            "fixed_equipment_names": {"chest": None, "gloves": None, "accessory_a": None, "accessory_b": None},
            "multi_skill_counts": {},
            "use_manual_multi_skill_counts": False,
            "special_ability_1_level": 9,
            "special_ability_2_level": 8,
            "special_ability_3_level": 0,
            "ws_level": 8,
            "ws_stack": 2,
            "ws2_level": 0,
        }
        restored = import_preset_json(json.dumps(data, ensure_ascii=False))
        self.assertEqual(restored.weapon_normal_levels, [9, 8])
        self.assertEqual(restored.weapon_special_states, [{"level": 8, "stack": 2}])


if __name__ == "__main__":
    unittest.main()
