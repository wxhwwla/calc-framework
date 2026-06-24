#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# SPDX-License-Identifier: AGPL-3.0
"""统一装备目录接缝测试。"""

import unittest

from games.endfield.data_loading.equipment_catalog import (
    EQUIPMENT_SCOPE_ALL,
    EQUIPMENT_SCOPE_LOOSE,
    EQUIPMENT_SCOPE_SET,
    catalog_full_search_error,
    catalog_status_message,
    equipment_scope_from_label,
    filter_equipment_rows_by_scope,
    get_equipment_catalog,
    is_equipment_catalog_complete,
    sample_equipment_catalog,
)


class TestEquipmentCatalog(unittest.TestCase):
    def test_scope_from_gui_labels(self):
        self.assertEqual(equipment_scope_from_label("全部装备"), EQUIPMENT_SCOPE_ALL)

        self.assertEqual(equipment_scope_from_label("仅套装装备"), EQUIPMENT_SCOPE_SET)

        self.assertEqual(equipment_scope_from_label("仅散件装备"), EQUIPMENT_SCOPE_LOOSE)

    def test_filter_set_only_keeps_rows_with_set_name(self):
        rows = [
            {"名称": "套装甲", "套装": "寒霜"},
            {"名称": "散件甲", "套装": ""},
        ]

        filtered = filter_equipment_rows_by_scope(rows, EQUIPMENT_SCOPE_SET)

        self.assertEqual([r["名称"] for r in filtered], ["套装甲"])

    def test_filter_loose_only_excludes_set_rows(self):
        rows = [
            {"名称": "套装甲", "套装": "寒霜"},
            {"名称": "散件甲", "套装": ""},
        ]

        filtered = filter_equipment_rows_by_scope(rows, EQUIPMENT_SCOPE_LOOSE)

        self.assertEqual([r["名称"] for r in filtered], ["散件甲"])

    def test_get_equipment_catalog_splits_three_slots(self):
        catalog = get_equipment_catalog(
            scope_label="全部装备",
            equipment_rows=[
                {"名称": "甲", "装备种类": "护甲", "套装": "", "效果": [], "三件套效果": []},
                {"名称": "手", "装备种类": "护手", "套装": "", "效果": [], "三件套效果": []},
                {"名称": "件", "装备种类": "配件", "套装": "", "效果": [], "三件套效果": []},
            ],
        )

        self.assertEqual(len(catalog["chest"]), 1)

        self.assertEqual(len(catalog["gloves"]), 1)

        self.assertEqual(len(catalog["accessories"]), 1)

    def test_catalog_status_message_none_when_complete(self):
        catalog = {
            "chest": [{"名称": "甲"}],
            "gloves": [{"名称": "手"}],
            "accessories": [{"名称": "件"}],
        }

        self.assertTrue(is_equipment_catalog_complete(catalog))

        self.assertIsNone(catalog_status_message(catalog))

    def test_catalog_status_message_when_empty(self):
        empty = {"chest": [], "gloves": [], "accessories": []}

        msg = catalog_status_message(empty)

        self.assertIsNotNone(msg)

        self.assertIn("未加载", msg or "")

    def test_catalog_full_search_error_when_incomplete(self):
        partial = {
            "chest": [{"名称": "甲"}],
            "gloves": [],
            "accessories": [],
        }

        err = catalog_full_search_error(partial)

        self.assertIsNotNone(err)

        self.assertIn("不完整", err or "")

    def test_sample_equipment_catalog_limits_each_slot(self):
        catalog = {
            "chest": [{"名称": f"c{i}"} for i in range(5)],
            "gloves": [{"名称": "g"}],
            "accessories": [{"名称": "a"}],
        }

        sampled = sample_equipment_catalog(catalog, per_slot=2)

        self.assertEqual(len(sampled["chest"]), 2)

        self.assertEqual(len(sampled["gloves"]), 1)


if __name__ == "__main__":
    unittest.main()
