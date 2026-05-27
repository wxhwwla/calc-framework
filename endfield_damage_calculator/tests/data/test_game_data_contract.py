#!/usr/bin/env python3
"""characters.json / weapons.json 全库结构契约测试"""

import json
import unittest

from data.loader import CHARACTERS_JSON_PATH, WEAPONS_JSON_PATH
from utils.path_utils import get_resource_path

CHAR_REQUIRED = {"名称", "类型", "星级"}
WEAPON_REQUIRED = {"名称", "类型", "星级", "基础攻击力"}
LEVEL_CURVE_LEN = 90
BONUS_ATTR_LEN = 9


def _load_json_list(relative_path: str) -> list:
    path = get_resource_path(relative_path)
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise AssertionError(f"{relative_path} 根节点必须是数组")
    return data


def _assert_special_ability(entry_name: str, field: list) -> None:
    if field == [False] or field is False:
        return
    if not isinstance(field, list) or len(field) < 1:
        raise AssertionError(f"{entry_name}: 特殊能力 格式无效")
    if field[0] is not True:
        raise AssertionError(f"{entry_name}: 特殊能力 未启用时应为 [False]")
    if len(field) not in (3, 4):
        raise AssertionError(f"{entry_name}: 启用的特殊能力应为 [True, 名称, 曲线] 或含 max_stack")
    if len(field) == 4 and not isinstance(field[3], int):
        raise AssertionError(f"{entry_name}: 特殊能力 max_stack 应为整数")
    if not isinstance(field[1], str) or not field[1]:
        raise AssertionError(f"{entry_name}: 特殊能力名称无效")
    curve = field[2]
    if not isinstance(curve, list) or len(curve) not in (9, 12):
        raise AssertionError(f"{entry_name}: 特殊能力曲线长度应为 9 或 12，实际 {len(curve)}")


def _assert_weapon_skills_schema(entry_name: str, weapon: dict) -> None:
    normal = weapon.get("normal_skills")
    special = weapon.get("special_skills")
    if not isinstance(normal, list):
        raise AssertionError(f"{entry_name}: 缺少 normal_skills 数组")
    if not isinstance(special, list):
        raise AssertionError(f"{entry_name}: 缺少 special_skills 数组")

    for idx, item in enumerate(normal, start=1):
        if not isinstance(item, dict):
            raise AssertionError(f"{entry_name}: normal_skills[{idx}] 必须是对象")
        if not str(item.get("effect", "")):
            raise AssertionError(f"{entry_name}: normal_skills[{idx}] 缺少 effect")
        curve = item.get("curve")
        if not isinstance(curve, list) or len(curve) != BONUS_ATTR_LEN:
            raise AssertionError(f"{entry_name}: normal_skills[{idx}] curve 长度应为 {BONUS_ATTR_LEN}")

    for idx, item in enumerate(special, start=1):
        if not isinstance(item, dict):
            raise AssertionError(f"{entry_name}: special_skills[{idx}] 必须是对象")
        if not str(item.get("name", "")):
            raise AssertionError(f"{entry_name}: special_skills[{idx}] 缺少 name")
        if not str(item.get("effect", "")):
            raise AssertionError(f"{entry_name}: special_skills[{idx}] 缺少 effect")
        curve = item.get("curve")
        if not isinstance(curve, list) or len(curve) != BONUS_ATTR_LEN:
            raise AssertionError(f"{entry_name}: special_skills[{idx}] curve 长度应为 {BONUS_ATTR_LEN}")
        if int(item.get("max_stack", 1)) < 1:
            raise AssertionError(f"{entry_name}: special_skills[{idx}] max_stack 至少为 1")


class TestGameDataContract(unittest.TestCase):
    """游戏数据 JSON 契约"""

    @classmethod
    def setUpClass(cls):
        cls.characters = _load_json_list(CHARACTERS_JSON_PATH)
        cls.weapons = _load_json_list(WEAPONS_JSON_PATH)

    def test_characters_non_empty(self):
        self.assertGreater(len(self.characters), 0, "角色数据为空")

    def test_weapons_non_empty(self):
        self.assertGreater(len(self.weapons), 0, "武器数据为空")

    def test_each_character_required_fields(self):
        for char in self.characters:
            name = char.get("名称", "<未命名>")
            missing = CHAR_REQUIRED - set(char.keys())
            self.assertFalse(missing, f"角色「{name}」缺少字段: {missing}")
            if "基础攻击力" in char:
                atk = char["基础攻击力"]
                self.assertIsInstance(atk, list)
                self.assertEqual(
                    len(atk),
                    LEVEL_CURVE_LEN,
                    f"角色「{name}」基础攻击力长度应为 {LEVEL_CURVE_LEN}",
                )

    def test_each_weapon_required_fields_and_curves(self):
        for weapon in self.weapons:
            name = weapon.get("名称", "<未命名>")
            missing = WEAPON_REQUIRED - set(weapon.keys())
            self.assertFalse(missing, f"武器「{name}」缺少字段: {missing}")

            atk = weapon["基础攻击力"]
            self.assertIsInstance(atk, list)
            self.assertEqual(
                len(atk),
                LEVEL_CURVE_LEN,
                f"武器「{name}」基础攻击力长度应为 {LEVEL_CURVE_LEN}",
            )

            for key, value in weapon.items():
                if key.endswith("+") and isinstance(value, list):
                    self.assertEqual(
                        len(value),
                        BONUS_ATTR_LEN,
                        f"武器「{name}」附加属性「{key}」长度应为 {BONUS_ATTR_LEN}",
                    )

            from character_weapon_equipment.weapon_data.special_fields import (
                SPECIAL_FIELD_KEYS,
                read_weapon_special_slots,
                write_weapon_special_slots,
            )

            slots = read_weapon_special_slots(weapon)
            if weapon.get(SPECIAL_FIELD_KEYS[0]) or weapon.get(SPECIAL_FIELD_KEYS[1]):
                write_weapon_special_slots(weapon, slots)
            for key in SPECIAL_FIELD_KEYS:
                if key in weapon:
                    _assert_special_ability(name, weapon[key])
            _assert_weapon_skills_schema(name, weapon)

    def test_weapon_special_curves_not_rank_multiple_mistake(self) -> None:
        """可叠层特殊能力九档须为「每层%」，不得误录为 base×档序。"""
        from character_weapon_equipment.weapon_data.special_fields import (
            is_accidental_rank_multiple_curve,
            read_weapon_special_slots,
        )

        bad: list[str] = []
        for weapon in self.weapons:
            name = weapon.get("名称", "<未命名>")
            for enabled, sa_name, curve, max_stack in read_weapon_special_slots(weapon):
                if not enabled or max_stack <= 1:
                    continue
                if is_accidental_rank_multiple_curve(curve):
                    bad.append(f"{name}（{sa_name}）")
        self.assertFalse(
            bad,
            "以下武器特殊曲线疑似把满档每层%误写成 base×(1..9)：" + "；".join(bad),
        )


if __name__ == "__main__":
    unittest.main()
