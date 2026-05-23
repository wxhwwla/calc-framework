#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""统一装备目录接缝测试。"""

import unittest

from data.equipment_catalog import (
    EQUIPMENT_SCOPE_ALL,
    EQUIPMENT_SCOPE_LOOSE,
    EQUIPMENT_SCOPE_SET,
    equipment_scope_from_label,
    filter_equipment_rows_by_scope,
    get_equipment_catalog,
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


if __name__ == "__main__":
    unittest.main()
