#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""武器特殊能力1/2 字段读写与迁移。"""

import unittest

from calc_engine.endfield.calc.skills.special_fields import (
    LEGACY_SPECIAL_KEY,
    SPECIAL_FIELD_KEYS,
    bonus_attribute_keys,
    migrate_weapon_record_to_skill_schema,
    migrate_weapon_records_to_skill_schema,
    parse_special_field,
    read_weapon_skills_schema,
    read_weapon_special_slots,
    write_weapon_skills_schema,
    write_weapon_special_slots,
)


class TestWeaponSpecialFields(unittest.TestCase):
    def test_migrate_weapon_record_to_skill_schema(self):
        weapon = {
            "名称": "测试武器",
            "基础攻击力": [1] * 90,
            "敏捷+": [10.0] * 9,
            "攻击力+": [20.0] * 9,
            "特殊能力1": [True, "施放战技后，攻击力+", [5.0] * 9, 2],
            "特殊能力2": [False],
        }
        changed = migrate_weapon_record_to_skill_schema(weapon)
        self.assertTrue(changed)
        self.assertNotIn("敏捷+", weapon)
        self.assertNotIn("特殊能力1", weapon)
        self.assertIn("normal_skills", weapon)
        self.assertIn("special_skills", weapon)
        self.assertEqual(weapon["normal_skills"][0]["effect"], "敏捷+")
        self.assertEqual(weapon["special_skills"][0]["effect"], "攻击力+")

    def test_migrate_weapon_record_to_skill_schema_is_idempotent(self):
        weapon = {
            "名称": "测试武器",
            "基础攻击力": [1] * 90,
            "normal_skills": [{"zone": 1, "effect": "敏捷+", "curve": [10.0] * 9}],
            "special_skills": [],
        }
        changed = migrate_weapon_record_to_skill_schema(weapon)
        self.assertFalse(changed)

    def test_migrate_weapon_records_to_skill_schema_returns_changed_names(self):
        weapons = [
            {
                "名称": "武器A",
                "基础攻击力": [1] * 90,
                "敏捷+": [10.0] * 9,
                "特殊能力1": [False],
                "特殊能力2": [False],
            },
            {
                "名称": "武器B",
                "基础攻击力": [1] * 90,
                "normal_skills": [],
                "special_skills": [],
            },
        ]
        changed_names = migrate_weapon_records_to_skill_schema(weapons)
        self.assertEqual(changed_names, ["武器A"])

    def test_read_weapon_skills_schema_from_legacy_fields(self):
        weapon = {
            "基础攻击力": [1] * 90,
            "敏捷+": [10.0] * 9,
            "攻击力+": [20.0] * 9,
            "特殊能力1": [True, "施放战技后，攻击力+", [5.0] * 9, 2],
            "特殊能力2": [False],
        }
        schema = read_weapon_skills_schema(weapon)
        self.assertEqual(
            schema["normal_skills"],
            [
                {"zone": 1, "effect": "敏捷+", "curve": [10.0] * 9},
                {"zone": 2, "effect": "攻击力+", "curve": [20.0] * 9},
            ],
        )
        self.assertEqual(schema["special_skills"][0]["name"], "施放战技后，攻击力+")
        self.assertEqual(schema["special_skills"][0]["effect"], "攻击力+")
        self.assertEqual(schema["special_skills"][0]["max_stack"], 2)

    def test_read_weapon_skills_schema_keeps_new_structure(self):
        weapon = {
            "normal_skills": [
                {"zone": 1, "effect": "敏捷+", "curve": [1.0] * 9},
            ],
            "special_skills": [
                {
                    "zone": 3,
                    "name": "施放战技后，攻击力+",
                    "condition": "施放战技后",
                    "curve": [2.0] * 9,
                    "max_stack": 3,
                }
            ],
        }
        schema = read_weapon_skills_schema(weapon)
        self.assertEqual(schema["normal_skills"][0]["effect"], "敏捷+")
        self.assertEqual(schema["special_skills"][0]["effect"], "攻击力+")
        self.assertEqual(schema["special_skills"][0]["condition"], "施放战技后")

    def test_bonus_and_special_slots_work_with_new_schema(self):
        weapon = {
            "基础攻击力": [1] * 90,
            "normal_skills": [
                {"zone": 1, "effect": "敏捷+", "curve": [10.0] * 9},
                {"zone": 2, "effect": "攻击力+", "curve": [20.0] * 9},
            ],
            "special_skills": [
                {
                    "zone": 3,
                    "name": "施放战技后，法术伤害+",
                    "condition": "施放战技后",
                    "effect": "法术伤害+",
                    "curve": [12.0] * 9,
                    "max_stack": 2,
                }
            ],
        }
        self.assertEqual(bonus_attribute_keys(weapon), ["敏捷+", "攻击力+"])
        slots = read_weapon_special_slots(weapon)
        self.assertTrue(slots[0][0])
        self.assertEqual(slots[0][1], "施放战技后，法术伤害+")
        self.assertEqual(slots[0][3], 2)

    def test_write_weapon_skills_schema_replaces_legacy_fields(self):
        weapon = {
            "基础攻击力": [1] * 90,
            "敏捷+": [10.0] * 9,
            "特殊能力1": [True, "施放战技后，攻击力+", [5.0] * 9, 2],
            "特殊能力2": [False],
        }
        write_weapon_skills_schema(
            weapon,
            normal_skills=[{"zone": 1, "effect": "攻击力+", "curve": [11.0] * 9}],
            special_skills=[
                {
                    "zone": 3,
                    "name": "施放连携技后，法术伤害+",
                    "condition": "施放连携技后",
                    "effect": "法术伤害+",
                    "curve": [3.0] * 9,
                    "max_stack": 3,
                }
            ],
        )
        self.assertNotIn("敏捷+", weapon)
        self.assertNotIn("特殊能力1", weapon)
        self.assertIn("normal_skills", weapon)
        self.assertIn("special_skills", weapon)
        self.assertEqual(weapon["normal_skills"][0]["effect"], "攻击力+")
        self.assertEqual(weapon["special_skills"][0]["max_stack"], 3)

    def test_parse_disabled_special(self):
        self.assertEqual(parse_special_field([False]), (False, "", [], 1))

    def test_parse_special_field_reads_max_stack(self):
        self.assertEqual(
            parse_special_field([True, "攻击力+", [21.0] * 9, 2]),
            (True, "攻击力+", [21.0] * 9, 2),
        )
        self.assertEqual(
            parse_special_field([True, "源石技艺强度+", [10.0] * 9]),
            (True, "源石技艺强度+", [10.0] * 9, 1),
        )

    def test_infer_max_stack_from_special_text(self):
        from calc_engine.endfield.calc.skills.special_fields import (
            infer_max_stack_from_special,
        )

        self.assertEqual(
            infer_max_stack_from_special(
                "造成'''物理异常'''时获得攻击力+",
                "最多可叠加2层",
            ),
            2,
        )
        self.assertEqual(
            infer_max_stack_from_special("每层'''狼血'''", "可叠加9层"),
            9,
        )
        self.assertEqual(
            infer_max_stack_from_special(
                "造成'''物理异常'''时获得攻击力+",
                "同名效果最多叠加2层，每层单独计算持续时间",
            ),
            2,
        )

    def test_build_and_read_two_slots(self):
        weapon: dict = {}
        write_weapon_special_slots(
            weapon,
            [
                (True, "施放战技后，法术伤害+", [12.0, 14.4], 1),
                (True, "施放连携技后，法术伤害+", [12.0, 33.6], 2),
            ],
        )
        slots = read_weapon_special_slots(weapon)
        self.assertEqual(slots[0][1], "施放战技后，法术伤害+")
        self.assertEqual(slots[0][3], 1)
        self.assertEqual(slots[1][3], 2)
        self.assertNotIn(LEGACY_SPECIAL_KEY, weapon)
        self.assertIn(SPECIAL_FIELD_KEYS[0], weapon)
        self.assertIn(SPECIAL_FIELD_KEYS[1], weapon)

    def test_migrate_legacy_weapon_special_level(self):
        from calc_engine.endfield.calc.skills.special_fields import (
            migrate_legacy_weapon_special_level,
        )

        self.assertEqual(migrate_legacy_weapon_special_level(0), (1, 0))
        self.assertEqual(migrate_legacy_weapon_special_level(8), (8, 1))
        self.assertEqual(migrate_legacy_weapon_special_level(8, ws_stack=2), (8, 2))

    def test_legacy_special_migrates_to_slot1(self):
        weapon = {
            "基础攻击力": [1] * 90,
            LEGACY_SPECIAL_KEY: [True, "源石技艺强度+", [10.0] * 9],
        }
        slots = read_weapon_special_slots(weapon)
        self.assertTrue(slots[0][0])
        self.assertEqual(slots[0][1], "源石技艺强度+")
        self.assertFalse(slots[1][0])

    def test_bonus_keys_stop_before_special_fields(self):
        weapon = {
            "基础攻击力": [1] * 90,
            "主能力值+": [1.0] * 9,
            "攻击力+": [2.0] * 9,
            "法术伤害+": [3.0] * 9,
            SPECIAL_FIELD_KEYS[0]: [False],
            SPECIAL_FIELD_KEYS[1]: [False],
        }
        self.assertEqual(
            bonus_attribute_keys(weapon),
            ["主能力值+", "攻击力+", "法术伤害+"],
        )


if __name__ == "__main__":
    unittest.main()
