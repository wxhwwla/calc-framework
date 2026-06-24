#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# SPDX-License-Identifier: AGPL-3.0
"""装备草案同步到本地格式测试。"""

import json
import tempfile
import unittest
from pathlib import Path

from games.endfield.calc.equipment.system import (
    EQUIPMENT_KIND_ACCESSORY,
    EQUIPMENT_KIND_ARMOR,
    EQUIPMENT_KIND_GLOVES,
    build_equipment_catalog_from_local_rows,
    infer_equipment_slot,
)
from games.endfield.tests.conftest import DATA_DIR

_SAMPLE_WIKITEXT = """{{装备

|装备名称=50式应龙护手

|装备种类=护手

|稀有度=金色

|所属套组=50式应龙

|主词条=防御力

|主词条数值=42

|属性词条1=敏捷

|属性词条1数值=65

|装备套组效果=3件套组效果:装备者攻击力+15%。

}}"""


class TestEquipmentSync(unittest.TestCase):
    def test_equipment_wiki_parses_kind_and_set_from_template(self):
        from bwiki_scout.equipment_wiki import equipment_record_from_wiki_params
        from bwiki_scout.parse_draft import extract_template_params

        params = extract_template_params(_SAMPLE_WIKITEXT)

        row = equipment_record_from_wiki_params(name="50式应龙护手", params=params)

        self.assertEqual(row["装备种类"], EQUIPMENT_KIND_GLOVES)

        self.assertEqual(row["所属套组"], "50式应龙")

        self.assertTrue(row["属性词条"])

        self.assertTrue(row["三件套效果"])

    def test_sync_equipments_from_parsed_writes_local_style_json(self):
        from bwiki_scout.equipment_sync import sync_equipments_from_parsed

        parsed_rows = [
            {
                "名称": "测试装备A",
                "_wiki_params": {
                    "装备种类": "护甲",
                    "稀有度": "5星",
                    "所属套组": "寒霜协议",
                    "属性词条1": "寒冷伤害",
                    "属性词条1数值": "10%",
                    "装备套组效果": "易伤+10%",
                },
            }
        ]

        with tempfile.TemporaryDirectory() as tmp:
            parsed = Path(tmp) / "equipment.json"

            local = Path(tmp) / "equipments.json"

            parsed.write_text(json.dumps(parsed_rows, ensure_ascii=False), encoding="utf-8")

            result = sync_equipments_from_parsed(
                parsed_equipment_json=parsed,
                local_equipments_json=local,
                dry_run=False,
            )

            self.assertEqual(result["count"], 1)

            self.assertEqual(result["kind_counts"][EQUIPMENT_KIND_ARMOR], 1)

            rows = json.loads(local.read_text(encoding="utf-8"))

            self.assertEqual(rows[0]["装备种类"], EQUIPMENT_KIND_ARMOR)

            self.assertEqual(rows[0]["所属套组"], "寒霜协议")

            self.assertEqual(rows[0]["三件套效果"], ["易伤+10%"])

    def test_infer_slot_from_name_when_bwiki_left_slot_empty(self):
        self.assertEqual(
            infer_equipment_slot({"名称": "50式应龙护手", "部位": ""}),
            EQUIPMENT_KIND_GLOVES,
        )

        self.assertEqual(
            infer_equipment_slot({"名称": "50式应龙轻甲", "部位": ""}),
            EQUIPMENT_KIND_ARMOR,
        )

        self.assertEqual(
            infer_equipment_slot({"名称": "50式应龙雷达", "部位": ""}),
            EQUIPMENT_KIND_ACCESSORY,
        )

    def test_catalog_includes_rows_with_empty_slot_but_inferable_name(self):
        rows = [
            {"名称": "矿场护手", "部位": "", "套装": "", "效果": [], "三件套效果": []},
            {"名称": "矿场轻甲", "部位": "", "套装": "", "效果": [], "三件套效果": []},
            {"名称": "阿伯莉传感芯片", "部位": "", "套装": "", "效果": [], "三件套效果": []},
        ]

        catalog = build_equipment_catalog_from_local_rows(rows)

        self.assertEqual(len(catalog["chest"]), 1)

        self.assertEqual(len(catalog["gloves"]), 1)

        self.assertEqual(len(catalog["accessories"]), 1)

    def test_local_equipments_file_yields_nonempty_catalog(self):
        """本地 equipments.json 存在时，遍历预览应能分到三部位。"""

        local = DATA_DIR / "equipments.json"

        if not local.is_file():
            self.skipTest("无本地 equipments.json")

        rows = json.loads(local.read_text(encoding="utf-8"))

        catalog = build_equipment_catalog_from_local_rows(rows)

        self.assertGreater(len(catalog["chest"]), 0, "护甲目录为空")

        self.assertGreater(len(catalog["gloves"]), 0, "护手目录为空")

        self.assertGreater(len(catalog["accessories"]), 0, "配件目录为空")

    def test_build_equipment_catalog_from_local_rows(self):
        rows = [
            {
                "名称": "护甲A",
                "装备种类": EQUIPMENT_KIND_ARMOR,
                "套装": "A",
                "效果": [],
                "三件套效果": [],
            },
            {
                "名称": "护手A",
                "装备种类": EQUIPMENT_KIND_GLOVES,
                "套装": "A",
                "效果": [],
                "三件套效果": [],
            },
            {
                "名称": "配件A",
                "装备种类": EQUIPMENT_KIND_ACCESSORY,
                "套装": "A",
                "效果": [],
                "三件套效果": [],
            },
        ]

        catalog = build_equipment_catalog_from_local_rows(rows)

        self.assertEqual(len(catalog["chest"]), 1)

        self.assertEqual(len(catalog["gloves"]), 1)

        self.assertEqual(len(catalog["accessories"]), 1)


if __name__ == "__main__":
    unittest.main()
