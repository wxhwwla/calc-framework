# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""装备词条解析的覆盖扩展测试（P2-07 从 test_coverage_expansion.py 拆分）。"""

from __future__ import annotations


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
