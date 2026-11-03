# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""装备系统辅助函数的覆盖扩展测试（P2-07 从 test_coverage_expansion.py 拆分）。"""

from __future__ import annotations

import pytest


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
