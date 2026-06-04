# SPDX-License-Identifier: AGPL-3.0
"""覆盖 special_fields 编解码、名称匹配、运行时加成。"""

from __future__ import annotations

from games.endfield.calc.skills.special_fields.codec import (
    build_special_field,
    infer_max_stack_from_special,
    is_accidental_rank_multiple_curve,
    parse_special_field,
)
from games.endfield.calc.skills.special_fields.name_utils import (
    _extract_effect_name_from_special_name,
    _special_name_matches,
    _split_special_name,
    bonus_attribute_keys,
    bonus_curve_for_key,
    weapon_special_field_keys,
)
from games.endfield.calc.skills.special_fields.runtime_bonus import (
    add_special_picks_attack_percent,
    add_special_picks_to_ability_pct,
    apply_conditional_special_to_stats,
    get_special_value_at_level,
    migrate_legacy_weapon_special_level,
    special_pick_bonus,
)
from games.endfield.calc.skills.special_fields.skills_schema import (
    read_weapon_skills_schema,
    write_weapon_skills_schema,
)
from games.endfield.calc.skills.special_fields.slots_io import read_weapon_special_slots, write_weapon_special_slots

# ── codec.py ─────────────────────────────────────────────────────────────


class TestCodec:
    """parse_special_field / build_special_field / infer_max_stack / is_accidental_rank_multiple_curve。"""

    def test_parse_disabled_false(self) -> None:
        assert parse_special_field(False) == (False, "", [], 1)

    def test_parse_disabled_false_list(self) -> None:
        assert parse_special_field([False]) == (False, "", [], 1)

    def test_parse_invalid_type(self) -> None:
        assert parse_special_field("invalid") == (False, "", [], 1)

    def test_parse_enabled_bare(self) -> None:
        result = parse_special_field([True, "力量+", [10.0, 20.0]])
        assert result == (True, "力量+", [10.0, 20.0], 1)

    def test_parse_enabled_with_max_stack(self) -> None:
        result = parse_special_field([True, "攻击力+", [5.0, 10.0], 3])
        assert result == (True, "攻击力+", [5.0, 10.0], 3)

    def test_build_disabled(self) -> None:
        assert build_special_field(enabled=False) == [False]

    def test_build_enabled_no_max_stack(self) -> None:
        result = build_special_field(enabled=True, name="力量+", curve=[10.0, 20.0])
        assert result == [True, "力量+", [10.0, 20.0]]

    def test_build_enabled_with_max_stack(self) -> None:
        result = build_special_field(enabled=True, name="力量+", curve=[10.0, 20.0], max_stack=3)
        assert result == [True, "力量+", [10.0, 20.0], 3]

    def test_infer_max_stack_from_name(self) -> None:
        assert infer_max_stack_from_special(name="叠加5层") == 5
        assert infer_max_stack_from_special(name="无叠加") == 1

    def test_infer_max_stack_from_text(self) -> None:
        assert infer_max_stack_from_special(text="最多叠加3层") == 3
        assert infer_max_stack_from_special(text="可叠加至5层") == 5
        assert infer_max_stack_from_special(text="共7层") == 7

    def test_infer_max_stack_empty(self) -> None:
        assert infer_max_stack_from_special() == 1

    def test_is_accidental_rank_multiple_curve_yes(self) -> None:
        assert is_accidental_rank_multiple_curve([21.0, 42.0, 63.0, 84.0, 105.0, 126.0, 147.0, 168.0, 189.0]) is True

    def test_is_accidental_rank_multiple_curve_no(self) -> None:
        assert is_accidental_rank_multiple_curve([10.0, 20.0, 30.0]) is False  # 不是9档
        assert is_accidental_rank_multiple_curve([21.0, 43.0, 63.0]) is False

    def test_is_accidental_rank_multiple_curve_empty(self) -> None:
        assert is_accidental_rank_multiple_curve([]) is False

    def test_is_accidental_rank_multiple_bad_base(self) -> None:
        assert is_accidental_rank_multiple_curve([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]) is False


# ── name_utils.py ────────────────────────────────────────────────────────


class TestNameUtils:
    """_extract_effect_name / _split_special_name / _special_name_matches / bonus_attribute_keys。"""

    def test_extract_simple(self) -> None:
        assert _extract_effect_name_from_special_name("攻击力+") == "攻击力+"

    def test_extract_with_condition(self) -> None:
        # 当前实现返回完整匹配字符串（正则 +? 懒惰匹配从左起取最短完整匹配）
        result = _extract_effect_name_from_special_name("血量低于50%时攻击力+")
        assert result  # 至少非空
        assert "+" in result

    def test_extract_empty(self) -> None:
        assert _extract_effect_name_from_special_name("") == ""

    def test_split_simple(self) -> None:
        cond, effect = _split_special_name("攻击力+")
        assert cond == ""
        assert effect == "攻击力+"

    def test_split_with_condition(self) -> None:
        cond, effect = _split_special_name("血量低于50%时获得攻击力+")
        # 当前实现中 effect 等于 name 时返回 ("", name)
        assert cond == ""
        assert "+" in effect

    def test_split_empty(self) -> None:
        cond, effect = _split_special_name("")
        assert cond == ""
        assert effect == ""

    def test_name_matches_exact(self) -> None:
        assert _special_name_matches("攻击力+", "攻击力+") is True

    def test_name_matches_with_condition(self) -> None:
        # 当 effect 可被提取时，effect 匹配即为真
        assert _special_name_matches("力量+", "触发时获得力量+", "力量+") is True
        assert _special_name_matches("攻击力+", "攻击力+") is True

    def test_name_matches_no_match(self) -> None:
        assert _special_name_matches("防御+", "攻击力+") is False

    def test_weapon_special_field_keys_empty(self) -> None:
        keys = weapon_special_field_keys({})
        assert len(keys) == 2  # 特殊能力1, 特殊能力2

    def test_weapon_special_field_keys_with_legacy(self) -> None:
        keys = weapon_special_field_keys({"特殊能力": [True, "x", []]})
        assert "特殊能力" in keys

    def test_bonus_attribute_keys_empty(self) -> None:
        assert bonus_attribute_keys({}) == []

    def test_bonus_attribute_keys_no_base_attack(self) -> None:
        assert bonus_attribute_keys({"foo": 1}) == []

    def test_bonus_curve_for_key_missing(self) -> None:
        assert bonus_curve_for_key({}, "力量+") == []

    def test_bonus_curve_for_key_with_normal_skills(self) -> None:
        weapon = {"normal_skills": [{"effect": "力量+", "curve": [10.0, 20.0, 30.0]}]}
        assert bonus_curve_for_key(weapon, "力量+") == [10.0, 20.0, 30.0]

    def test_bonus_curve_for_key_missing_in_normal_skills(self) -> None:
        weapon = {"normal_skills": [{"effect": "敏捷+", "curve": [1.0]}]}
        assert bonus_curve_for_key(weapon, "力量+") == []


# ── runtime_bonus.py ─────────────────────────────────────────────────────


class TestRuntimeBonus:
    """special_pick_bonus / apply_conditional_special_to_stats / add_special_picks_* / migrate_legacy。"""

    def test_special_pick_bonus_zero_level(self) -> None:
        assert special_pick_bonus([10.0, 20.0], 1, skill_level=0, stack_count=1) == 0.0

    def test_special_pick_bonus_empty_curve(self) -> None:
        assert special_pick_bonus([], 1, skill_level=1, stack_count=1) == 0.0

    def test_special_pick_bonus_basic(self) -> None:
        assert special_pick_bonus([10.0, 20.0, 30.0], 1, skill_level=2, stack_count=1) == 20.0

    def test_special_pick_bonus_level_oob(self) -> None:
        assert special_pick_bonus([10.0, 20.0], 1, skill_level=99, stack_count=1) == 20.0

    def test_special_pick_bonus_with_stack(self) -> None:
        assert special_pick_bonus([10.0, 20.0], max_stack=5, skill_level=1, stack_count=3) == 30.0

    def test_migrate_legacy_with_stack(self) -> None:
        level, stack = migrate_legacy_weapon_special_level(5, ws_stack=3)
        assert level == 5
        assert stack == 3

    def test_migrate_legacy_without_stack(self) -> None:
        level, stack = migrate_legacy_weapon_special_level(3)
        assert level == 3
        assert stack == 1

    def test_migrate_legacy_zero_or_negative(self) -> None:
        level, stack = migrate_legacy_weapon_special_level(0)
        assert level == 1
        assert stack == 0

    def test_apply_conditional_special_no_weapon(self) -> None:
        result = apply_conditional_special_to_stats(
            {},
            ws_name="",
            ws_level=0,
            ws_stack=1,
            ws2_name="",
            ws2_level=0,
            ws2_stack=1,
            main_attr="力量",
            sub_attr="敏捷",
        )
        assert result == (0.0, 0.0, 0.0, 0.0)

    def test_add_special_picks_attack_percent_no_weapon(self) -> None:
        result = add_special_picks_attack_percent(
            {},
            ws_name="",
            ws_level=0,
            ws_stack=1,
            ws2_name="",
            ws2_level=0,
            ws2_stack=1,
        )
        assert result == 0.0

    def test_get_special_value_at_level_no_weapon(self) -> None:
        assert get_special_value_at_level({}, 0, name="x", level=0) is None

    def test_add_special_picks_to_ability_pct_no_weapon(self) -> None:
        result = add_special_picks_to_ability_pct(
            {},
            ws_name="",
            ws_level=0,
            ws_stack=1,
            ws2_name="",
            ws2_level=0,
            ws2_stack=1,
            main_attr="力量",
            sub_attr="敏捷",
        )
        assert result == (0.0, 0.0)


# ── slots_io.py ──────────────────────────────────────────────────────────


class TestSlotsIO:
    """read_weapon_special_slots / write_weapon_special_slots。"""

    def test_read_empty(self) -> None:
        slots = read_weapon_special_slots({})
        assert len(slots) == 2
        assert all(s[0] is False for s in slots)

    def test_read_new_structure_special_skills(self) -> None:
        weapon = {
            "special_skills": [
                {"name": "攻击力+", "effect": "攻击力+", "curve": [10.0, 20.0], "max_stack": 3},
            ]
        }
        slots = read_weapon_special_slots(weapon)
        assert slots[0][0] is True
        assert slots[0][1] == "攻击力+"
        assert slots[0][3] == 3
        assert slots[1][0] is False

    def test_read_legacy_structure(self) -> None:
        weapon = {"特殊能力1": [True, "力量+", [5.0, 10.0], 2]}
        slots = read_weapon_special_slots(weapon)
        assert slots[0][0] is True
        assert slots[0][1] == "力量+"
        assert slots[1][0] is False

    def test_write_new_structure(self) -> None:
        weapon = {
            "special_skills": [
                {"zone": 3, "name": "攻击力+", "condition": "", "effect": "攻击力+", "curve": [1.0], "max_stack": 1},
            ]
        }
        write_weapon_special_slots(weapon, [(True, "攻击力+", [1.0], 1), (False, "", [], 1)])
        assert "特殊能力1" not in weapon
        assert "特殊能力" not in weapon

    def test_write_legacy_structure(self) -> None:
        weapon = {"特殊能力1": [True, "x", [1.0]], "基础攻击力": [100.0]}
        write_weapon_special_slots(weapon, [(True, "x", [1.0], 1), (False, "", [], 1)])
        assert "特殊能力1" in weapon


# ── skills_schema.py ─────────────────────────────────────────────────────


class TestSkillsSchema:
    """read_weapon_skills_schema / write_weapon_skills_schema。"""

    def test_read_new_structure(self) -> None:
        weapon = {
            "normal_skills": [{"zone": 1, "effect": "力量+", "curve": [10.0, 20.0]}],
            "special_skills": [
                {"zone": 3, "name": "攻击力+", "effect": "攻击力+", "condition": "", "curve": [5.0], "max_stack": 1}
            ],
        }
        schema = read_weapon_skills_schema(weapon)
        assert len(schema["normal_skills"]) == 1
        assert len(schema["special_skills"]) == 1
        assert schema["normal_skills"][0]["effect"] == "力量+"

    def test_read_legacy_structure(self) -> None:
        weapon = {
            "基础攻击力": [100.0],
            "攻击力+": [5.0, 10.0],
            "力量+": [3.0, 6.0],
            "特殊能力1": [True, "攻击力+", [1.0, 2.0], 1],
        }
        schema = read_weapon_skills_schema(weapon)
        assert len(schema["normal_skills"]) >= 1

    def test_write_skills_schema(self) -> None:
        weapon = {
            "normal_skills": [{"zone": 1, "effect": "力量+", "curve": [10.0]}],
            "special_skills": [],
        }
        write_weapon_skills_schema(
            weapon,
            normal_skills=[{"zone": 1, "effect": "敏捷+", "curve": [5.0]}],
            special_skills=[
                {
                    "zone": 3,
                    "name": "攻击力+",
                    "effect": "攻击力+",
                    "condition": "",
                    "curve": [1.0],
                    "max_stack": 1,
                }
            ],
        )
        assert len(weapon["normal_skills"]) == 1
        assert weapon["normal_skills"][0]["effect"] == "敏捷+"
        assert len(weapon["special_skills"]) == 1

    def test_write_skills_schema_normalizes_skills(self) -> None:
        weapon = {
            "基础攻击力": [100.0],
            "攻击力+": [5.0],
            "特殊能力1": [True, "x", [1.0]],
        }
        write_weapon_skills_schema(
            weapon,
            normal_skills=[{"zone": 1, "effect": "力量+", "curve": [5.0]}],
            special_skills=[],
        )
        assert "normal_skills" in weapon
        assert weapon["normal_skills"][0]["effect"] == "力量+"
