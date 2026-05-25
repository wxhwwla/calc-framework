#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""武器特殊能力1/2 字段读写与迁移。"""

import unittest

from character_weapon_equipment.weapon_data.special_fields import (
    LEGACY_SPECIAL_KEY,
    SPECIAL_FIELD_KEYS,
    bonus_attribute_keys,
    build_special_field,
    parse_special_field,
    read_weapon_special_slots,
    write_weapon_special_slots,
)


class TestWeaponSpecialFields(unittest.TestCase):
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
        from character_weapon_equipment.weapon_data.special_fields import (
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
