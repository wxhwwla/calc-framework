#!/usr/bin/env python3
"""add_weapon 无副作用测试"""

import copy
import json
import tempfile
import unittest
from pathlib import Path

from tools.endfield_scripts.add_weapon import add_weapon, remove_weapon


class TestAddWeaponNoMutation(unittest.TestCase):
    def test_bonus_attrs_not_mutated(self):
        bonus = {
            "意志+": {"base": 12, "growth": 48, "divisor": 5, "offset": 0, "special": [93]},
        }
        before = copy.deepcopy(bonus)
        with tempfile.TemporaryDirectory() as tmp:
            json_path = Path(tmp) / "weapons.json"
            json_path.write_text("[]", encoding="utf-8")
            add_weapon(
                name="测试武器",
                weapon_type="单手剑",
                star=3,
                base_atk={"base": 10, "growth": 10, "divisor": 5, "offset": 0},
                bonus_attrs=bonus,
                json_path=json_path,
            )
        self.assertEqual(bonus, before)
        self.assertIn("special", bonus["意志+"])

    def test_remove_weapon_deletes_by_name(self):
        """按名称从 weapons.json 删除条目，且不误删其它武器。"""
        with tempfile.TemporaryDirectory() as tmp:
            json_path = Path(tmp) / "weapons.json"
            json_path.write_text("[]", encoding="utf-8")
            add_weapon(
                name="保留",
                weapon_type="单手剑",
                star=3,
                base_atk={"base": 10, "growth": 10, "divisor": 5, "offset": 0},
                json_path=json_path,
            )
            add_weapon(
                name="待删",
                weapon_type="单手剑",
                star=3,
                base_atk={"base": 10, "growth": 10, "divisor": 5, "offset": 0},
                json_path=json_path,
            )
            removed = remove_weapon("待删", json_path=json_path)
            self.assertTrue(removed)
            names = [w["名称"] for w in json.loads(json_path.read_text(encoding="utf-8"))]
            self.assertEqual(names, ["保留"])

    def test_remove_weapon_returns_false_when_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            json_path = Path(tmp) / "weapons.json"
            json_path.write_text("[]", encoding="utf-8")
            self.assertFalse(remove_weapon("不存在", json_path=json_path))


if __name__ == "__main__":
    unittest.main()
