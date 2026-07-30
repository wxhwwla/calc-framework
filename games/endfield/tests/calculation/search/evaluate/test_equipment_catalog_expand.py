#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""装备目录三槽→四槽展开与 Rust 全批量预处理。"""

from __future__ import annotations

import unittest

from games.endfield.calc.search.evaluate.rust_batch_data import (
    prepare_equipment_combos,
    resolve_equipment_slot_lists,
)


def _eq(name: str, kind: str) -> dict:
    return {
        "名称": name,
        "装备种类": kind,
        "效果": [],
        "三件套效果": [],
        "属性词条": [],
    }


class TestResolveEquipmentSlotLists(unittest.TestCase):
    def test_accessories_catalog_expands_to_a_and_b(self) -> None:
        catalog = {
            "chest": [_eq("胸", "护甲")],
            "gloves": [_eq("手", "护手")],
            "accessories": [_eq("件1", "配件"), _eq("件2", "配件")],
        }
        chest, gloves, acc_a, acc_b = resolve_equipment_slot_lists(catalog)
        self.assertEqual(len(chest), 1)
        self.assertEqual(len(gloves), 1)
        self.assertEqual([x["名称"] for x in acc_a], ["件1", "件2"])
        self.assertEqual([x["名称"] for x in acc_b], ["件1", "件2"])

    def test_explicit_four_slot_preferred_over_accessories(self) -> None:
        catalog = {
            "chest": [_eq("胸", "护甲")],
            "gloves": [_eq("手", "护手")],
            "accessory_a": [_eq("A", "配件")],
            "accessory_b": [_eq("B", "配件")],
            "accessories": [_eq("忽略", "配件")],
        }
        _c, _g, acc_a, acc_b = resolve_equipment_slot_lists(catalog)
        self.assertEqual([x["名称"] for x in acc_a], ["A"])
        self.assertEqual([x["名称"] for x in acc_b], ["B"])

    def test_prepare_equipment_combos_non_empty_for_accessories_catalog(self) -> None:
        """回归：曾因未展开 accessories 导致全批量返回空结果。"""
        catalog = {
            "chest": [_eq("胸", "护甲")],
            "gloves": [_eq("手", "护手")],
            "accessories": [_eq("件1", "配件"), _eq("件2", "配件")],
        }
        combos = prepare_equipment_combos(catalog)
        # 1×1×2×2 = 4
        self.assertEqual(len(combos), 4)
        names = {(c.acc_a_name, c.acc_b_name) for c in combos}
        self.assertIn(("件1", "件1"), names)
        self.assertIn(("件1", "件2"), names)
        self.assertIn(("件2", "件1"), names)
        self.assertIn(("件2", "件2"), names)

    def test_prepare_empty_without_accessories(self) -> None:
        catalog = {"chest": [_eq("胸", "护甲")], "gloves": [_eq("手", "护手")]}
        self.assertEqual(prepare_equipment_combos(catalog), [])


class TestUseRustFullBatchFlag(unittest.TestCase):
    def test_flag_default_on_opt_out_with_zero(self) -> None:
        import os

        from utils.frozen_runtime import use_rust_full_batch

        old = os.environ.pop("CALC_RUST_FULL_BATCH", None)
        old_fb = os.environ.pop("RUST_SEARCH_FALLBACK", None)
        try:
            self.assertTrue(use_rust_full_batch())
            os.environ["CALC_RUST_FULL_BATCH"] = "0"
            self.assertFalse(use_rust_full_batch())
            os.environ["CALC_RUST_FULL_BATCH"] = "1"
            self.assertTrue(use_rust_full_batch())
        finally:
            if old is None:
                os.environ.pop("CALC_RUST_FULL_BATCH", None)
            else:
                os.environ["CALC_RUST_FULL_BATCH"] = old
            if old_fb is None:
                os.environ.pop("RUST_SEARCH_FALLBACK", None)
            else:
                os.environ["RUST_SEARCH_FALLBACK"] = old_fb


if __name__ == "__main__":
    unittest.main()
