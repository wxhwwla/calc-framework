# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""
Coverage expansion tests for games.endfield.calc.

Covers under-tested areas:
- equipment/affix — parse_equipment_affix_line variants
- equipment/system — build_four_slot_loadout, collect_loadout_effects, equipment_kind
- equipment/prune — equipment_stat_affinity_tier, sort_equipment_catalog_by_priority
- survival/estimate — build_survival_estimate edge cases
- manual_buff/model — ManualBuffEntry, build_active_keys_from_counts
- damage/engine — DamageContext, DamageEffect, DamageResult
"""

from __future__ import annotations

import pytest

# =========================================================================
# Equipment Affix — parse_equipment_affix_line
# =========================================================================


class TestEquipmentAffixExpanded:
    """parse_equipment_affix_line with various input patterns."""

    def test_empty_string(self):
        from games.endfield.calc.equipment.affix import parse_equipment_affix_line

        effects, flats = parse_equipment_affix_line("", source="test")
        assert effects == []
        assert flats == {}

    def test_none_input(self):
        from games.endfield.calc.equipment.affix import parse_equipment_affix_line

        effects, flats = parse_equipment_affix_line(None, source="test")  # type: ignore[arg-type]
        assert effects == []
        assert flats == {}

    def test_whitespace_only(self):
        from games.endfield.calc.equipment.affix import parse_equipment_affix_line

        effects, flats = parse_equipment_affix_line("   ", source="test")
        assert effects == []
        assert flats == {}

    def test_skill_bonus_normal_attack(self):
        from games.endfield.calc.equipment.affix import parse_equipment_affix_line

        effects, flats = parse_equipment_affix_line("普通攻击伤害加成15%", source="test_item")
        assert len(effects) == 1
        assert effects[0].effect_type == "技能类型伤害加成"
        assert effects[0].value == 0.15
        assert effects[0].source == "test_item"
        assert effects[0].skill_types == ("普通攻击",)
        assert flats == {}

    def test_skill_bonus_skill(self):
        from games.endfield.calc.equipment.affix import parse_equipment_affix_line

        effects, _flats = parse_equipment_affix_line("战技伤害20%", source="test_item")
        assert len(effects) == 1
        assert effects[0].skill_types == ("战技",)
        assert effects[0].value == 0.20

    def test_skill_bonus_chain(self):
        from games.endfield.calc.equipment.affix import parse_equipment_affix_line

        effects, _flats = parse_equipment_affix_line("连携技伤害加成25.5%", source="test_item")
        assert effects[0].skill_types == ("连携技",)
        assert effects[0].value == 0.255

    def test_skill_bonus_ultimate(self):
        from games.endfield.calc.equipment.affix import parse_equipment_affix_line

        effects, _flats = parse_equipment_affix_line("终结技伤害加成30%", source="test_item")
        assert effects[0].skill_types == ("终结技",)

    def test_all_skill_bonus(self):
        from games.endfield.calc.equipment.affix import parse_equipment_affix_line

        effects, _flats = parse_equipment_affix_line("全技能伤害加成10%", source="test_item")
        assert len(effects) == 1
        assert effects[0].effect_type == "技能类型伤害加成"
        assert effects[0].skill_types == ("战技", "连携技", "终结技")
        assert effects[0].value == 0.10

    def test_damage_type_bonus_physical(self):
        from games.endfield.calc.equipment.affix import parse_equipment_affix_line

        effects, _flats = parse_equipment_affix_line("物理伤害加成12%", source="test_item")
        assert len(effects) == 1
        assert effects[0].effect_type == "伤害类型伤害加成"

    def test_damage_type_bonus_灼热(self):
        from games.endfield.calc.equipment.affix import parse_equipment_affix_line

        effects, _flats = parse_equipment_affix_line("灼热伤害8%", source="test_item")
        assert len(effects) == 1
        assert effects[0].effect_type == "伤害类型伤害加成"

    def test_damage_type_bonus_electromagnetic(self):
        from games.endfield.calc.equipment.affix import parse_equipment_affix_line

        effects, _flats = parse_equipment_affix_line("电磁伤害加成18%", source="test_item")
        assert len(effects) == 1

    def test_originium_arts_strength(self):
        from games.endfield.calc.equipment.affix import parse_equipment_affix_line

        effects, flats = parse_equipment_affix_line("源石技艺强度50", source="test_item")
        from games.endfield.calc.damage.originium_arts import ORIGINIUM_FLAT_STAT_KEY

        assert effects == []
        assert ORIGINIUM_FLAT_STAT_KEY in flats

    def test_flat_attack_percent(self):
        from games.endfield.calc.equipment.affix import parse_equipment_affix_line

        effects, _flats = parse_equipment_affix_line("攻击力5%", source="test_item")
        assert len(effects) == 1
        assert effects[0].effect_type == "装备攻击力加成"

    def test_flat_stat_strength(self):
        from games.endfield.calc.equipment.affix import parse_equipment_affix_line

        _effects, flats = parse_equipment_affix_line("力量12", source="test_item")
        assert "力量" in flats
        assert flats["力量"] > 0

    def test_flat_stat_intelligence(self):
        from games.endfield.calc.equipment.affix import parse_equipment_affix_line

        _effects, flats = parse_equipment_affix_line("智识8", source="test_item")
        assert "智识" in flats

    def test_flat_stat_agility(self):
        from games.endfield.calc.equipment.affix import parse_equipment_affix_line

        _effects, flats = parse_equipment_affix_line("敏捷15", source="test_item")
        assert "敏捷" in flats

    def test_flat_stat_will(self):
        from games.endfield.calc.equipment.affix import parse_equipment_affix_line

        _effects, flats = parse_equipment_affix_line("意志10", source="test_item")
        assert "意志" in flats

    def test_set_effect_sentence_physical_damage(self):
        from games.endfield.calc.equipment.affix import parse_equipment_affix_line

        effects, _flats = parse_equipment_affix_line("物理伤害+20%", source="set_bonus")
        assert len(effects) == 1
        assert effects[0].effect_type == "伤害类型伤害加成"

    def test_set_effect_sentence_generic_damage(self):
        from games.endfield.calc.equipment.affix import parse_equipment_affix_line

        effects, _flats = parse_equipment_affix_line("伤害加成+15%", source="set_bonus")
        assert len(effects) == 1
        assert effects[0].effect_type == "其他伤害加成"

    def test_parse_equipment_effect_block_multiple_lines(self):
        from games.endfield.calc.equipment.affix import parse_equipment_effect_block

        block = "物理伤害+10%；战技伤害加成12%"
        effects, _flats = parse_equipment_effect_block(block, source="set")
        assert len(effects) == 2

    def test_parse_equipment_effect_block_with_flats(self):
        from games.endfield.calc.equipment.affix import parse_equipment_effect_block

        block = "力量12\n敏捷8\n战技伤害10%"
        effects, flats = parse_equipment_effect_block(block, source="set")
        assert len(effects) == 1
        assert len(flats) >= 2


# =========================================================================
# Equipment System — FourSlotLoadout & helpers
# =========================================================================


class TestEquipmentSystemExpanded:
    """build_four_slot_loadout, collect_loadout_effects, equipment_kind."""

    def test_equipment_kind_with_wiki_field(self):
        from games.endfield.calc.equipment.system import equipment_kind

        record = {"装备种类": "护甲"}
        assert equipment_kind(record) == "护甲"

    def test_equipment_kind_with_部位_field(self):
        from games.endfield.calc.equipment.system import equipment_kind

        record = {"部位": "护手"}
        assert equipment_kind(record) == "护手"

    def test_equipment_kind_alias_胸甲(self):
        from games.endfield.calc.equipment.system import equipment_kind

        record = {"装备种类": "胸甲"}
        assert equipment_kind(record) == "护甲"

    def test_equipment_kind_unknown(self):
        from games.endfield.calc.equipment.system import equipment_kind

        record = {"装备种类": "未知部位"}
        assert equipment_kind(record) == "未知部位"

    def test_equipment_kind_empty(self):
        from games.endfield.calc.equipment.system import equipment_kind

        assert equipment_kind({}) == ""

    def test_infer_equipment_slot_by_field(self):
        from games.endfield.calc.equipment.system import infer_equipment_slot

        record = {"装备种类": "护甲"}
        assert infer_equipment_slot(record) == "护甲"

    def test_infer_equipment_slot_by_name(self):
        from games.endfield.calc.equipment.system import infer_equipment_slot

        record = {"名称": "战术轻甲"}
        assert infer_equipment_slot(record) == "护甲"

    def test_infer_equipment_slot_gloves_by_name(self):
        from games.endfield.calc.equipment.system import infer_equipment_slot

        record = {"名称": "防护手套"}
        assert infer_equipment_slot(record) == "护手"

    def test_infer_equipment_slot_accessory_by_name(self):
        from games.endfield.calc.equipment.system import infer_equipment_slot

        record = {"名称": "能量芯片"}
        assert infer_equipment_slot(record) == "配件"

    def test_infer_equipment_slot_unknown(self):
        from games.endfield.calc.equipment.system import infer_equipment_slot

        record = {"名称": "xyzabc"}
        assert infer_equipment_slot(record) == ""

    def test_parse_percent_value(self):
        from games.endfield.calc.equipment.system import _parse_percent_value

        assert _parse_percent_value("伤害+15%") == 0.15
        assert _parse_percent_value("+20.5%") == 0.205
        assert _parse_percent_value("no percent") == 0.0

    def test_build_four_slot_loadout_valid(self):
        from games.endfield.calc.equipment.system import (
            FourSlotLoadout,
            build_four_slot_loadout,
        )

        loadout = build_four_slot_loadout(
            chest={"名称": "测试护甲", "装备种类": "护甲"},
            gloves={"名称": "测试护手", "装备种类": "护手"},
            accessory_a={"名称": "测试配件A", "装备种类": "配件"},
            accessory_b={"名称": "测试配件B", "装备种类": "配件"},
        )
        assert isinstance(loadout, FourSlotLoadout)
        assert loadout.chest["名称"] == "测试护甲"
        assert loadout.gloves["名称"] == "测试护手"

    def test_build_four_slot_loadout_duplicate_accessory_allowed(self):
        from games.endfield.calc.equipment.system import build_four_slot_loadout

        loadout = build_four_slot_loadout(
            chest={"名称": "甲", "装备种类": "护甲"},
            gloves={"名称": "手", "装备种类": "护手"},
            accessory_a={"名称": "同配件", "装备种类": "配件"},
            accessory_b={"名称": "同配件", "装备种类": "配件"},
            allow_duplicate_accessory=True,
        )
        assert loadout.accessory_a["名称"] == loadout.accessory_b["名称"]

    def test_build_four_slot_loadout_duplicate_accessory_forbidden(self):
        from games.endfield.calc.equipment.system import build_four_slot_loadout

        with pytest.raises(ValueError, match="不允许重复配件"):
            build_four_slot_loadout(
                chest={"名称": "甲", "装备种类": "护甲"},
                gloves={"名称": "手", "装备种类": "护手"},
                accessory_a={"名称": "同", "装备种类": "配件"},
                accessory_b={"名称": "同", "装备种类": "配件"},
                allow_duplicate_accessory=False,
            )

    def test_build_four_slot_loadout_wrong_chest_slot(self):
        from games.endfield.calc.equipment.system import build_four_slot_loadout

        with pytest.raises(ValueError, match="护甲槽位"):
            build_four_slot_loadout(
                chest={"名称": "手套", "装备种类": "护手"},
                gloves={"名称": "手", "装备种类": "护手"},
                accessory_a={"名称": "件A", "装备种类": "配件"},
                accessory_b={"名称": "件B", "装备种类": "配件"},
            )

    def test_build_four_slot_loadout_wrong_gloves_slot(self):
        from games.endfield.calc.equipment.system import build_four_slot_loadout

        with pytest.raises(ValueError, match="护手槽位"):
            build_four_slot_loadout(
                chest={"名称": "甲", "装备种类": "护甲"},
                gloves={"名称": "甲2", "装备种类": "护甲"},
                accessory_a={"名称": "件A", "装备种类": "配件"},
                accessory_b={"名称": "件B", "装备种类": "配件"},
            )

    def test_collect_loadout_effects(self):
        from games.endfield.calc.equipment.system import (
            FourSlotLoadout,
            collect_loadout_effects,
        )

        loadout = FourSlotLoadout(
            chest={"效果": [], "套装": "test_set", "三件套效果": []},
            gloves={"效果": [], "套装": "test_set", "三件套效果": []},
            accessory_a={"效果": [], "套装": "test_set", "三件套效果": []},
            accessory_b={"效果": [], "套装": ""},
        )
        effects = collect_loadout_effects(loadout)
        assert isinstance(effects, list)

    def test_aggregate_loadout_modifiers_no_set_bonus(self):
        from games.endfield.calc.equipment.affix import aggregate_loadout_modifiers
        from games.endfield.calc.equipment.system import FourSlotLoadout

        loadout = FourSlotLoadout(
            chest={"效果": [], "套装": "", "flat_stats": {"力量": 10}},
            gloves={"效果": [], "套装": "", "flat_stats": {"力量": 5}},
            accessory_a={"效果": [], "套装": "", "flat_stats": {}},
            accessory_b={"效果": [], "套装": "", "flat_stats": {}},
        )
        _effects, flat_stats, attack_percent = aggregate_loadout_modifiers(loadout)
        assert "力量" in flat_stats
        assert flat_stats["力量"] == 15.0
        assert attack_percent == 0.0

    def test_build_equipment_catalog_from_runtime(self):
        from games.endfield.calc.equipment.system import build_equipment_catalog_from_runtime

        records = [
            {"装备种类": "护甲", "名称": "测试甲"},
            {"装备种类": "护手", "名称": "测试手"},
            {"装备种类": "配件", "名称": "测试件1"},
            {"装备种类": "配件", "名称": "测试件2"},
        ]
        catalog = build_equipment_catalog_from_runtime(records)
        assert len(catalog["chest"]) == 1
        assert len(catalog["gloves"]) == 1
        assert len(catalog["accessories"]) == 2


# =========================================================================
# Equipment Prune — affinity and sorting
# =========================================================================


class TestEquipmentPruneExpanded:
    """equipment_stat_affinity_tier, equipment_prune_sort_key."""

    def test_stat_affinity_tier_both(self):
        from games.endfield.calc.equipment.prune import equipment_stat_affinity_tier

        item = {"属性词条": ["力量15", "敏捷10"]}
        tier = equipment_stat_affinity_tier(item, "力量", "敏捷")
        assert tier == 0

    def test_stat_affinity_tier_main_only(self):
        from games.endfield.calc.equipment.prune import equipment_stat_affinity_tier

        item = {"属性词条": ["力量15"]}
        tier = equipment_stat_affinity_tier(item, "力量", "敏捷")
        assert tier == 1

    def test_stat_affinity_tier_sub_only(self):
        from games.endfield.calc.equipment.prune import equipment_stat_affinity_tier

        item = {"属性词条": ["敏捷10"]}
        tier = equipment_stat_affinity_tier(item, "力量", "敏捷")
        assert tier == 2

    def test_stat_affinity_tier_neither(self):
        from games.endfield.calc.equipment.prune import equipment_stat_affinity_tier

        item = {"属性词条": ["智识5"]}
        tier = equipment_stat_affinity_tier(item, "力量", "敏捷")
        assert tier == 3

    def test_skill_affinity_tier_has_bonus(self):
        from games.endfield.calc.equipment.prune import equipment_skill_affinity_tier

        item = {"属性词条": ["战技伤害10%"]}
        tier = equipment_skill_affinity_tier(item, ("战技",))
        assert tier == 0

    def test_skill_affinity_tier_no_bonus(self):
        from games.endfield.calc.equipment.prune import equipment_skill_affinity_tier

        item = {"属性词条": ["普通攻击伤害10%"]}
        tier = equipment_skill_affinity_tier(item, ("战技",))
        assert tier == 1

    def test_skill_affinity_tier_empty_skills(self):
        from games.endfield.calc.equipment.prune import equipment_skill_affinity_tier

        item = {"属性词条": ["战技伤害10%"]}
        tier = equipment_skill_affinity_tier(item, ())
        assert tier == 1

    def test_prune_sort_key(self):
        from games.endfield.calc.equipment.prune import equipment_prune_sort_key

        item = {"名称": "测试装", "属性词条": ["力量15"]}
        key = equipment_prune_sort_key(item, "力量", "敏捷", ("战技",))
        assert isinstance(key, tuple)
        assert len(key) == 3

    def test_sort_equipment_catalog_by_priority(self):
        from games.endfield.calc.equipment.prune import sort_equipment_catalog_by_priority

        catalog = {
            "chest": [
                {"名称": "甲B", "属性词条": []},
                {"名称": "甲A", "属性词条": ["力量15"]},
            ],
            "gloves": [],
            "accessories": [],
        }
        sorted_cat = sort_equipment_catalog_by_priority(
            catalog, main_attr="力量", sub_attr="敏捷", skill_types=("战技",)
        )
        # 甲A before 甲B because it has the main stat
        names = [item["名称"] for item in sorted_cat["chest"]]
        assert names.index("甲A") < names.index("甲B")

    def test_character_ability_attrs(self):
        from games.endfield.calc.equipment.prune import character_ability_attrs

        char = {"主能力": "力量", "副能力": "敏捷"}
        main, sub = character_ability_attrs(char)
        assert main == "力量"
        assert sub == "敏捷"


# =========================================================================
# Manual Buff Model
# =========================================================================


class TestManualBuffModel:
    """ManualBuffEntry, empty_buff_dict, get/set_buffs_for_key."""

    def test_manual_buff_entry_creation(self):
        from games.endfield.calc.manual_buff.model import ManualBuffEntry

        entry = ManualBuffEntry(effect_type="暴击率", value=0.10)
        assert entry.effect_type == "暴击率"
        assert entry.value == 0.10

    def test_empty_buff_dict(self):
        from games.endfield.calc.manual_buff.model import empty_buff_dict

        d = empty_buff_dict()
        assert d == {}

    def test_get_buffs_for_key_empty(self):
        from games.endfield.calc.manual_buff.model import get_buffs_for_key

        result = get_buffs_for_key({}, "暴击率")
        assert result == []

    def test_set_and_get_buffs(self):
        from games.endfield.calc.manual_buff.model import get_buffs_for_key, set_buffs_for_key

        store = {}
        set_buffs_for_key(store, "暴击率", [{"effect_type": "暴击率", "value": 0.10}])
        result = get_buffs_for_key(store, "暴击率")
        assert len(result) == 1
        assert result[0]["value"] == 0.10

    def test_set_buffs_empty_removes_key(self):
        from games.endfield.calc.manual_buff.model import set_buffs_for_key

        store = {"暴击率": [{"effect_type": "暴击率", "value": 0.10}]}
        set_buffs_for_key(store, "暴击率", [])
        assert "暴击率" not in store

    def test_build_active_keys_skills_only(self):
        from games.endfield.calc.manual_buff.model import build_active_keys_from_counts

        keys = build_active_keys_from_counts(
            skill_counts={"战技": 2, "终结技": 1},
            physical_abnormal_counts={},
            spell_abnormal_counts={},
        )
        assert set(keys) == {"战技:1", "战技:2", "终结技:1"}

    def test_build_active_keys_skills_ordered(self):
        from games.endfield.calc.manual_buff.model import build_active_keys_from_counts

        keys = build_active_keys_from_counts(
            skill_counts={"终结技": 1, "战技": 2, "连携技": 3},
            physical_abnormal_counts={},
            spell_abnormal_counts={},
        )
        # All expected keys should be present (order may depend on dict insertion)
        expected = {"战技:1", "战技:2", "连携技:1", "连携技:2", "连携技:3", "终结技:1"}
        assert set(keys) == expected

    def test_build_active_keys_zero_counts_skipped(self):
        from games.endfield.calc.manual_buff.model import build_active_keys_from_counts

        keys = build_active_keys_from_counts(
            skill_counts={"战技": 0, "终结技": 2},
            physical_abnormal_counts={},
            spell_abnormal_counts={},
        )
        assert "战技:" not in str(keys)
        assert "终结技:1" in keys

    def test_build_active_keys_with_physical_abnormal(self):
        from games.endfield.calc.manual_buff.model import build_active_keys_from_counts

        keys = build_active_keys_from_counts(
            skill_counts={},
            physical_abnormal_counts={"燃烧": 2},
            spell_abnormal_counts={},
        )
        assert "燃烧:1" in keys
        assert "燃烧:2" in keys

    def test_build_active_keys_with_spell_abnormal(self):
        from games.endfield.calc.manual_buff.model import build_active_keys_from_counts

        keys = build_active_keys_from_counts(
            skill_counts={},
            physical_abnormal_counts={},
            spell_abnormal_counts={"冰冻": 1},
        )
        assert "冰冻:1" in keys

    def test_build_active_keys_mixed_all(self):
        from games.endfield.calc.manual_buff.model import build_active_keys_from_counts

        keys = build_active_keys_from_counts(
            skill_counts={"战技": 1},
            physical_abnormal_counts={"燃烧": 1},
            spell_abnormal_counts={"冰冻": 1},
        )
        assert "战技:1" in keys
        assert "燃烧:1" in keys
        assert "冰冻:1" in keys


# =========================================================================
# Damage Engine — DamageContext, DamageEffect, DamageResult
# =========================================================================


class TestDamageEngineTypes:
    """Damage engine types creation and properties."""

    def test_damage_context_creation(self):
        from games.endfield.calc.damage.engine.types import DamageContext

        ctx = DamageContext(
            final_attack=1000.0,
            skill_multiplier=1.5,
            damage_type="物理",
            skill_type="普通攻击",
            is_unbalanced=False,
        )
        assert ctx.final_attack == 1000.0
        assert ctx.skill_multiplier == 1.5
        assert ctx.damage_type == "物理"
        assert ctx.skill_type == "普通攻击"
        assert ctx.is_unbalanced is False

    def test_damage_effect_creation_basic(self):
        from games.endfield.calc.damage.engine.types import DamageEffect

        effect = DamageEffect(
            effect_type="伤害类型伤害加成",
            value=0.20,
            source="test",
            raw_text="物理伤害20%",
        )
        assert effect.effect_type == "伤害类型伤害加成"
        assert effect.value == 0.20
        assert effect.source == "test"
        assert effect.raw_text == "物理伤害20%"

    def test_damage_effect_with_skill_types(self):
        from games.endfield.calc.damage.engine.types import DamageEffect

        effect = DamageEffect(
            effect_type="技能类型伤害加成",
            value=0.15,
            source="test",
            raw_text="战技伤害15%",
            skill_types=("战技",),
        )
        assert effect.skill_types == ("战技",)

    def test_damage_effect_with_damage_types(self):
        from games.endfield.calc.damage.engine.types import DamageEffect

        effect = DamageEffect(
            effect_type="伤害类型伤害加成",
            value=0.10,
            source="test",
            raw_text="物理伤害10%",
            damage_types=("物理",),
        )
        assert effect.damage_types == ("物理",)

    def test_damage_result_creation(self):
        from games.endfield.calc.damage.engine.types import DamageResult

        result = DamageResult(
            final_damage=1500.0,
            zone_values={"基础伤害区": 1000.0, "暴击区": 1.0},
            crit_mode="non_crit",
            warnings=(),
            unknown_effects=(),
        )
        assert result.final_damage == 1500.0
        assert isinstance(result.zone_values, dict)

    def test_damage_context_default_is_unbalanced(self):
        from games.endfield.calc.damage.engine.types import DamageContext

        ctx = DamageContext(
            final_attack=500.0,
            skill_multiplier=1.0,
            damage_type="物理",
            skill_type="普通攻击",
        )
        assert ctx.is_unbalanced is False

    def test_known_effect_types(self):
        from games.endfield.calc.damage.engine.types import KNOWN_EFFECT_TYPES

        assert isinstance(KNOWN_EFFECT_TYPES, tuple | list | set | frozenset)
        assert len(KNOWN_EFFECT_TYPES) > 0

    def test_zone_order(self):
        from games.endfield.calc.damage.engine.types import ZONE_ORDER

        assert isinstance(ZONE_ORDER, tuple | list)
        assert len(ZONE_ORDER) > 0

    def test_crit_mode_literal_values(self):
        from typing import get_args

        from games.endfield.calc.damage.engine.types import CritMode

        values = set(get_args(CritMode))
        assert "non_crit" in values
        assert "expected" in values
        assert "always_crit" in values

    def test_damage_effect_repr(self):
        from games.endfield.calc.damage.engine.types import DamageEffect

        effect = DamageEffect(
            effect_type="易伤",
            value=0.20,
            source="test",
        )
        r = repr(effect)
        assert "易伤" in r or "DamageEffect" in r


# =========================================================================
# Survival Estimate — build_survival_estimate edge cases
# =========================================================================


class TestSurvivalEstimate:
    """build_survival_estimate with minimal inputs."""

    def test_build_survival_estimate_basic(self):
        from games.endfield.calc.survival.estimate import build_survival_estimate

        char_data = {
            "力量": [100.0] * 90,
            "意志": [100.0] * 90,
            "主能力": "力量",
            "副能力": "敏捷",
        }
        weapon_data = {"基础攻击": 200, "攻击成长": 10, "攻击除数": 1}

        result = build_survival_estimate(
            char_data=char_data,
            weapon_data=weapon_data,
            char_level=80,
            weapon_level=80,
        )
        assert "execute_damage" in result
        assert "imbalance_cap" in result
        assert "burn_tick_per_sec" in result
        assert "enemy_max_hp" in result
        assert "healing_amount" in result
        assert "character_max_hp" in result

    def test_build_survival_estimate_with_enemy_max_hp(self):
        from games.endfield.calc.survival.estimate import build_survival_estimate

        char_data = {
            "力量": [100.0] * 90,
            "意志": [100.0] * 90,
        }
        weapon_data = {"基础攻击": 200, "攻击成长": 10, "攻击除数": 1}

        result = build_survival_estimate(
            char_data=char_data,
            weapon_data=weapon_data,
            char_level=80,
            weapon_level=80,
            enemy_max_hp=50000.0,
        )
        assert result["enemy_max_hp"] == 50000.0

    def test_build_survival_estimate_with_sp(self):
        from games.endfield.calc.survival.estimate import build_survival_estimate

        char_data = {
            "力量": [100.0] * 90,
            "意志": [100.0] * 90,
        }
        weapon_data = {"基础攻击": 200, "攻击成长": 10, "攻击除数": 1}

        result = build_survival_estimate(
            char_data=char_data,
            weapon_data=weapon_data,
            char_level=80,
            weapon_level=80,
            sp_start=50.0,
            sp_seconds=5.0,
            ult_start=50.0,
        )
        assert result["sp_after_regen"] > 0
        assert result["ultimate_charge_after"] >= 0

    def test_build_survival_estimate_zero_hp(self):
        from games.endfield.calc.survival.estimate import build_survival_estimate

        char_data = {
            "力量": [100.0] * 90,
            "意志": [100.0] * 90,
        }
        weapon_data = {"基础攻击": 200, "攻击成长": 10, "攻击除数": 1}

        result = build_survival_estimate(
            char_data=char_data,
            weapon_data=weapon_data,
            char_level=80,
            weapon_level=80,
            enemy_max_hp=0.0,
        )
        assert result["burn_tick_per_sec"] == 0.0

    def test_build_survival_estimate_keys_present(self):
        from games.endfield.calc.survival.estimate import build_survival_estimate

        char_data = {
            "力量": [100.0] * 90,
            "意志": [100.0] * 90,
        }
        weapon_data = {"基础攻击": 200, "攻击成长": 10, "攻击除数": 1}

        result = build_survival_estimate(
            char_data=char_data,
            weapon_data=weapon_data,
            char_level=80,
            weapon_level=80,
        )
        required_keys = [
            "execute_damage",
            "execute_multiplier",
            "execute_sp_restore",
            "imbalance_cap",
            "imbalance_duration_sec",
            "imbalance_nodes_1",
            "imbalance_nodes_2",
            "imbalance_gain_effective",
            "imbalance_gain_percent",
            "fast_break_multiplier",
            "burn_tick_per_sec",
            "enemy_max_hp",
            "sp_after_regen",
            "sp_regen_per_sec",
            "ultimate_charge_after",
            "ultimate_charge_per_100_sp",
            "dodge_sp_gain",
            "life_steal_heal",
            "healing_amount",
            "character_max_hp",
        ]
        for key in required_keys:
            assert key in result, f"Missing key: {key}"
