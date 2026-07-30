#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""Rust 全批量接入：开关门禁与固定配装目录展开。"""

from __future__ import annotations

import os
import unittest
from unittest import mock

from games.endfield.calc.damage.engine import DamageContext
from games.endfield.calc.loadout.in_memory_optimizer import run_enumerated_optimizer_parallel
from games.endfield.calc.loadout.optimizer import LoadoutScore, OptimizerConfig, WeaponCandidate
from games.endfield.calc.loadout.slot_search import FixedLoadoutSelection, equipment_catalog_for_selection
from games.endfield.calc.search.evaluate.context import SearchEvalContext
from games.endfield.calc.search.evaluate.full_batch_eval import can_run_full_batch_search


def _eq(name: str, kind: str) -> dict:
    return {
        "名称": name,
        "装备种类": kind,
        "效果": ["攻击力+1%"],
        "三件套效果": [],
        "属性词条": ["攻击力1"],
    }


class TestEquipmentCatalogForSelection(unittest.TestCase):
    def test_fixed_chest_collapses_to_one(self) -> None:
        catalog = {
            "chest": [_eq("胸1", "护甲"), _eq("胸2", "护甲")],
            "gloves": [_eq("手1", "护手")],
            "accessories": [_eq("件1", "配件"), _eq("件2", "配件")],
        }
        fixed = FixedLoadoutSelection(chest=catalog["chest"][0])
        four = equipment_catalog_for_selection(catalog, selection=fixed)
        self.assertEqual([x["名称"] for x in four["chest"]], ["胸1"])
        self.assertEqual(len(four["accessory_a"]), 2)
        self.assertEqual(len(four["accessory_b"]), 2)


class TestCanRunFullBatchSearch(unittest.TestCase):
    def tearDown(self) -> None:
        os.environ.pop("CALC_RUST_FULL_BATCH", None)
        os.environ.pop("RUST_SEARCH_FALLBACK", None)

    def test_off_by_default(self) -> None:
        os.environ.pop("CALC_RUST_FULL_BATCH", None)
        self.assertFalse(
            can_run_full_batch_search(
                search_eval=SearchEvalContext(
                    char_data={"名称": "测", "基础攻击": [100]},
                    char_level=90,
                    weapon_level=90,
                    trust_level=0,
                    weapon_data_by_name={},
                ),
                search_job=None,
                task_evaluator=None,
            )
        )

    def test_requires_search_eval(self) -> None:
        os.environ["CALC_RUST_FULL_BATCH"] = "1"
        with mock.patch(
            "games.endfield.calc.search.evaluate.full_batch_eval._rust_full_batch_importable",
            return_value=True,
        ):
            self.assertFalse(
                can_run_full_batch_search(
                    search_eval=None,
                    search_job=None,
                    task_evaluator=None,
                )
            )


class TestFullBatchMemoryHook(unittest.TestCase):
    def tearDown(self) -> None:
        os.environ.pop("CALC_RUST_FULL_BATCH", None)

    def test_memory_path_uses_full_batch_when_enabled(self) -> None:
        os.environ["CALC_RUST_FULL_BATCH"] = "1"
        catalog = {
            "chest": [_eq("胸1", "护甲")],
            "gloves": [_eq("手1", "护手")],
            "accessories": [_eq("件1", "配件")],
        }
        weapons = [WeaponCandidate(name="武器A", final_attack=1000.0)]
        search_eval = SearchEvalContext(
            char_data={"名称": "角色", "基础攻击": [500.0]},
            char_level=90,
            weapon_level=90,
            trust_level=0,
            weapon_data_by_name={"武器A": {"名称": "武器A"}},
        )
        fake_scores = [
            LoadoutScore(
                weapon_name="武器A",
                final_damage=1234.0,
                loadout_names={
                    "chest": "胸1",
                    "gloves": "手1",
                    "accessory_a": "件1",
                    "accessory_b": "件1",
                },
            )
        ]

        with (
            mock.patch(
                "games.endfield.calc.search.evaluate.full_batch_eval._rust_full_batch_importable",
                return_value=True,
            ),
            mock.patch(
                "games.endfield.calc.loadout.in_memory_optimizer.can_run_full_batch_search",
                return_value=True,
            ),
            mock.patch(
                "games.endfield.calc.loadout.in_memory_optimizer.try_run_full_batch_from_plan",
                return_value=fake_scores,
            ) as full_batch,
        ):
            top, total, processed, cancelled, _warnings = run_enumerated_optimizer_parallel(
                base_context=DamageContext(final_attack=1000.0, skill_multiplier=1.0, enemy_defense=0.0),
                weapons=weapons,
                equipment_catalog=catalog,
                config=OptimizerConfig(top_n=3, prune_non_beneficial=False),
                search_eval=search_eval,
                max_workers=1,
            )

        full_batch.assert_called_once()
        self.assertEqual(len(top), 1)
        self.assertAlmostEqual(top[0].final_damage, 1234.0)
        self.assertFalse(cancelled)
        self.assertGreater(total, 0)
        self.assertEqual(processed, total)


class TestFullBatchResumeHook(unittest.TestCase):
    def tearDown(self) -> None:
        os.environ.pop("CALC_RUST_FULL_BATCH", None)

    def test_fresh_resume_uses_full_batch_and_short_circuits_completed(self) -> None:
        import tempfile
        from pathlib import Path

        from games.endfield.calc.search.persist.store import SearchRunStore, execute_search_with_resume

        os.environ["CALC_RUST_FULL_BATCH"] = "1"
        catalog = {
            "chest": [_eq("胸1", "护甲")],
            "gloves": [_eq("手1", "护手")],
            "accessories": [_eq("件1", "配件")],
        }
        weapons = [WeaponCandidate(name="武器A", final_attack=1000.0)]
        search_eval = SearchEvalContext(
            char_data={"名称": "角色", "基础攻击": [500.0]},
            char_level=90,
            weapon_level=90,
            trust_level=0,
            weapon_data_by_name={"武器A": {"名称": "武器A"}},
        )
        fake_scores = [
            LoadoutScore(
                weapon_name="武器A",
                final_damage=999.0,
                loadout_names={
                    "chest": "胸1",
                    "gloves": "手1",
                    "accessory_a": "件1",
                    "accessory_b": "件1",
                },
            )
        ]
        base = DamageContext(final_attack=1000.0, skill_multiplier=1.0, enemy_defense=0.0)
        config = OptimizerConfig(top_n=3, prune_non_beneficial=False)

        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "search_runs.db"
            with (
                mock.patch(
                    "games.endfield.calc.search.evaluate.full_batch_eval._rust_full_batch_importable",
                    return_value=True,
                ),
                mock.patch(
                    "games.endfield.calc.search.persist.full_batch_resume.can_run_full_batch_search",
                    return_value=True,
                ),
                mock.patch(
                    "games.endfield.calc.search.persist.full_batch_resume.try_run_full_batch_from_plan",
                    return_value=fake_scores,
                ) as full_batch,
            ):
                first = execute_search_with_resume(
                    db_path=db_path,
                    run_signature="fb-sig",
                    base_context=base,
                    weapons=weapons,
                    equipment_catalog=catalog,
                    config=config,
                    search_eval=search_eval,
                    max_workers=1,
                )
                full_batch.assert_called_once()
                self.assertAlmostEqual(first.top_results[0].final_damage, 999.0)
                self.assertEqual(first.processed_combinations, first.total_combinations)
                self.assertFalse(first.cancelled)

                store = SearchRunStore(db_path)
                self.assertEqual(store.run_status("fb-sig"), "completed")

                # 已完成签名应短路，不再调用全批量
                full_batch.reset_mock()
                second = execute_search_with_resume(
                    db_path=db_path,
                    run_signature="fb-sig",
                    base_context=base,
                    weapons=weapons,
                    equipment_catalog=catalog,
                    config=config,
                    search_eval=search_eval,
                    max_workers=1,
                )
                full_batch.assert_not_called()
                self.assertAlmostEqual(second.top_results[0].final_damage, 999.0)
                self.assertEqual(second.processed_this_run, 0)
                self.assertEqual(second.skipped_preprocessed, second.total_combinations)


if __name__ == "__main__":
    unittest.main()
