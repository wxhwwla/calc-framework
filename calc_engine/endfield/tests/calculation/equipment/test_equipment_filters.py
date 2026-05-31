#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""装备套装筛选（data/equipment_filters）测试。"""

import unittest

from calc_engine.endfield.data_loading.equipment_filters import (
    SET_FILTER_ALL,
    SET_FILTER_LOOSE,
    equipment_names_from_rows,
    filter_rows_by_set_label,
    list_set_filter_options,
)


class TestEquipmentFilters(unittest.TestCase):
    def _rows(self):
        return [
            {"名称": "甲A", "套装": "寒霜"},
            {"名称": "甲B", "套装": ""},
            {"名称": "甲C", "套装": "寒霜"},
        ]

    def test_list_set_filter_options(self) -> None:
        opts = list_set_filter_options(self._rows())
        self.assertEqual(opts[0], SET_FILTER_ALL)
        self.assertIn("寒霜", opts)
        self.assertIn(SET_FILTER_LOOSE, opts)

    def test_filter_by_set_name(self) -> None:
        filtered = filter_rows_by_set_label(self._rows(), "寒霜")
        self.assertEqual(len(filtered), 2)
        self.assertEqual(filtered[0]["名称"], "甲A")

    def test_filter_loose_only(self) -> None:
        filtered = filter_rows_by_set_label(self._rows(), SET_FILTER_LOOSE)
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]["名称"], "甲B")

    def test_equipment_names_from_rows(self) -> None:
        names = equipment_names_from_rows(self._rows())
        self.assertEqual(names, ["甲A", "甲B", "甲C"])


if __name__ == "__main__":
    unittest.main()
