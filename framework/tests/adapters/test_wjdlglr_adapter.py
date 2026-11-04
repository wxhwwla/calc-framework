#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# SPDX-License-Identifier: AGPL-3.0
# ruff: noqa: E402

"""无尽的拉格朗日适配器结构测试 — meta / layout / 数据契约。"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_FRAMEWORK_SRC = Path(__file__).resolve().parents[2] / "src"

if str(_FRAMEWORK_SRC) not in sys.path:
    sys.path.insert(0, str(_FRAMEWORK_SRC))

from wjdlglr_test_helpers import _ADAPTER_DIR, _DPM_KEYS, _TARGETS, _WEAPON_FIELDS

from calc_framework.config.adapter import AdapterPackage


class TestAdapterLoads:
    """适配包应能被框架正常加载。"""

    def test_meta_declares_game_and_data_binding(self, adapter_pkg: AdapterPackage) -> None:
        assert adapter_pkg.meta["name"] == "无尽的拉格朗日 武器输出计算器"
        assert adapter_pkg.meta["game"] == "无尽的拉格朗日"
        assert adapter_pkg.meta["schema_version"] == "dag-v1"
        assert adapter_pkg.meta["version"] == "0.6.0"
        assert "data/weapons.json" in adapter_pkg.meta["entry_data"]

    def test_dag_exposes_per_target_outputs(self, adapter_pkg: AdapterPackage) -> None:
        outputs = set(adapter_pkg.dag_service.dag.outputs)
        assert outputs >= _DPM_KEYS
        assert {
            "发射数",
            "飞行时间(秒)",
            "冷却与持续时间(秒)",
            "每分钟平均发射数",
            "暴击增伤倍率",
            "暴击增伤倍率(对空)",
            "甲后单发",
            "最终单发",
            "最终单发(对空)",
            "满命中每分钟伤害",
        } <= outputs
        assert "击杀时间(秒)" not in outputs
        assert "官方火力击杀时间(秒)" not in outputs

    def test_layout_only_lists_user_inputs_and_target_outputs(self) -> None:
        layout = json.loads((_ADAPTER_DIR / "ui" / "layout.json").read_text(encoding="utf-8"))
        variables = {name for section in layout["sections"] for name in section.get("variables", [])}
        outputs = {name for section in layout["sections"] for name in section.get("outputs", [])}

        assert "user_input.fleet_count" in variables
        assert "user_input.self_flight_bonus" in variables
        assert "user_input.bonus_crit_rate" in variables
        assert "user_input.damage_bonus" in variables
        assert "user_input.base_crit_multiplier" not in variables
        assert "user_input.base_crit_damage" not in variables
        assert "user_input.enemy_hp" not in variables
        assert "user_input.firepower" not in variables
        assert not any(name.startswith("weapon.") for name in variables)
        assert "user_input.weapon_count" not in variables
        assert outputs >= _DPM_KEYS
        assert "满命中每分钟伤害" in outputs

    def test_meta_declares_cascading_entity_selectors(self, adapter_pkg: AdapterPackage) -> None:
        selectors = adapter_pkg.meta["entity_selectors"]
        assert len(selectors) == 1
        selector = selectors[0]
        assert selector["source"] == "weapon"
        assert selector["data_file"] == "weapons"
        assert [step["field"] for step in selector["steps"]] == [
            "舰船分类",
            "舰船",
            "名称",
        ]
        assert selector["steps"][-1]["display_field"] == "武器标签"

    def test_attr_schema_binds_weapon_fields_to_weapon_source(self) -> None:
        schema = json.loads((_ADAPTER_DIR / "attr_schema.json").read_text(encoding="utf-8"))
        attrs = {attr["name"]: attr for attr in schema["attributes"]}

        assert attrs["fleet_count"]["source"] == "user_input"
        assert attrs["weapon_count"]["source"] == "weapon"
        assert attrs["hit_fighter"]["source"] == "weapon"
        assert attrs["needs_mothership"]["source"] == "weapon"
        assert attrs["friendly"]["source"] == "weapon"
        assert attrs["is_energy"]["source"] == "weapon"
        assert attrs["crit_rate"]["source"] == "weapon"
        assert attrs["crit_damage"]["source"] == "weapon"
        assert attrs["crit_vs_air"]["source"] == "weapon"
        assert attrs["energy_armor"]["source"] == "user_input"
        assert attrs["hit_fighter"]["default"] == 0.0
        assert "base_crit_multiplier" not in attrs
        assert "base_crit_damage" not in attrs

    def test_meta_declares_weapon_detail_and_conditional_inputs(self, adapter_pkg: AdapterPackage) -> None:
        detail = adapter_pkg.meta["entity_detail"]
        assert detail["source"] == "weapon"
        assert detail["title"] == "武器数据"
        fields = {field["field"] for section in detail["sections"] for field in section["fields"]}
        assert {"舰船", "舰船类型", "武器作用", "damage_type", "base_damage"} <= fields
        assert {"crit_rate", "crit_damage", "crit_target"} <= fields
        assert {f"hit_{key}" for key, _ in _TARGETS} <= fields
        hit_section = next(section for section in detail["sections"] if section["title"] == "命中率（%）")
        assert hit_section["columns"] == 2

        rules = adapter_pkg.meta["entity_input_rules"]
        disabled = {path for rule in rules for path in rule["disable"]}
        assert disabled == {
            "user_input.mothership_flight_bonus",
            "user_input.mothership_cooldown_bonus",
            "user_input.mothership_duration_bonus",
            "user_input.physical_armor",
            "user_input.energy_armor",
        }

    def test_layout_uses_multi_column_outputs_and_tabs(self) -> None:
        layout = json.loads((_ADAPTER_DIR / "ui" / "layout.json").read_text(encoding="utf-8"))
        sections = {section["id"]: section for section in layout["sections"]}
        assert sections["outputs"]["columns"] == 3
        assert sections["intermediate"]["columns"] == 2
        assert set(sections) == {"inputs", "combat", "outputs", "intermediate"}
        assert sections["outputs"]["tab"] == "计算"
        assert sections["intermediate"]["tab"] == "乘区明细"
        assert set(sections["intermediate"]["outputs"]) >= {
            "发射数",
            "飞行时间(秒)",
            "冷却与持续时间(秒)",
            "每分钟平均发射数",
            "暴击增伤倍率",
            "暴击增伤倍率(对空)",
            "甲后单发",
            "最终单发",
            "最终单发(对空)",
            "满命中每分钟伤害",
        }


class TestWeaponData:
    """data/weapons.json 的字段契约与舰船 × 武器记录。"""

    def test_records_are_unique_and_cover_the_roster(self, weapon_records: list[dict[str, object]]) -> None:
        names = [record["名称"] for record in weapon_records]
        assert len(weapon_records) > 500
        assert len(names) == len(set(names))

    def test_each_record_has_all_dag_weapon_fields(self, weapon_records: list[dict[str, object]]) -> None:
        for record in weapon_records:
            assert set(record) >= _WEAPON_FIELDS

    def test_records_have_cascading_selector_fields(self, weapon_records: list[dict[str, object]]) -> None:
        known_classes = {
            "战机",
            "护航艇",
            "无人机",
            "护卫舰",
            "驱逐舰",
            "巡洋舰",
            "战列巡洋舰",
            "战列舰",
            "航空母舰",
            "支援舰",
            "登陆舰",
            "要塞舰",
            "工程舰",
            "未分类",
        }
        for record in weapon_records:
            classes = record["舰船分类"]
            assert isinstance(classes, list) and classes
            assert set(classes) <= known_classes
            assert "未知" not in classes
            label = record["武器标签"]
            assert isinstance(label, str) and label

    def test_weapon_labels_are_unique_within_each_ship(self, weapon_records: list[dict[str, object]]) -> None:
        seen: dict[str, set[str]] = {}
        for record in weapon_records:
            ship = str(record["舰船"])
            label = str(record["武器标签"])
            assert label not in seen.setdefault(ship, set())
            seen[ship].add(label)

    def test_records_declare_damage_type_and_energy_flag(self, weapon_records: list[dict[str, object]]) -> None:
        for record in weapon_records:
            damage_type = record["damage_type"]
            is_energy = record["is_energy"]
            assert damage_type in {"实弹", "能量", "辅助"}
            assert is_energy in {0.0, 1.0}
            assert (damage_type == "能量") == (is_energy == 1.0)

        energy = [record for record in weapon_records if record["is_energy"] == 1.0]
        assert energy
        assert all(record["武器作用"] == "能量攻击" for record in energy)

    def test_friendly_records_have_hundred_percent_hit(self, weapon_records: list[dict[str, object]]) -> None:
        friendly = [record for record in weapon_records if record["friendly"] == 1.0]
        assert friendly
        for record in friendly:
            assert all(record[f"hit_{key}"] == 100.0 for key, _ in _TARGETS)

    def test_aircraft_records_require_mothership(self, weapon_records: list[dict[str, object]]) -> None:
        aircraft = [record for record in weapon_records if record["舰船类型"] == "战机" or record["舰船类型"] == "护航艇"]
        assert aircraft
        assert all(record["needs_mothership"] == 1.0 for record in aircraft)

    def test_aircraft_records_share_ship_level_flight_time(self, weapon_records: list[dict[str, object]]) -> None:
        by_ship: dict[str, list[dict[str, object]]] = {}
        for record in weapon_records:
            if record["needs_mothership"] == 1.0:
                by_ship.setdefault(str(record["舰船"]), []).append(record)

        assert by_ship
        for records in by_ship.values():
            outbound = {record["outbound"] for record in records}
            inbound = {record["inbound"] for record in records}
            assert len(outbound) == 1 and len(inbound) == 1
            if any(float(str(value)) > 0 for value in outbound):
                assert all(float(str(value)) > 0 for value in outbound)

    def test_records_include_crit_stats(self, weapon_records: list[dict[str, object]]) -> None:
        crit_records = [record for record in weapon_records if float(str(record["crit_rate"])) > 0]
        assert len(crit_records) >= 30
        for record in crit_records:
            assert float(str(record["crit_damage"])) > 0
            assert record["crit_target"] in {"舰船", "舰载机"}
            assert record["crit_vs_air"] in {0.0, 1.0}
        anti_air = [record for record in crit_records if record["crit_vs_air"] == 1.0]
        assert anti_air
        assert all(record["crit_target"] == "舰载机" for record in anti_air)
