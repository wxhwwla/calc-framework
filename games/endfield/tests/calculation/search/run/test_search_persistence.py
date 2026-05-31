#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""SQLite 续跑与去重测试。"""

import tempfile
import unittest
from pathlib import Path

from games.endfield.calc.damage.engine import DamageContext
from games.endfield.calc.equipment.system import build_runtime_equipment_from_wiki_draft
from games.endfield.calc.loadout.optimizer import OptimizerConfig, WeaponCandidate
from games.endfield.calc.search.persist.store import (
    SearchRunStore,
    execute_search_with_resume,
    get_sqlite_viewer_links,
)
from games.endfield.calc.search.run.runner import SearchCancelToken


class TestSearchPersistence(unittest.TestCase):
    def _catalog(self):
        chest = build_runtime_equipment_from_wiki_draft(
            {"名称": "胸甲A", "_wiki_params": {"装备种类": "护甲", "所属套组": "套装A"}}
        )
        gloves = build_runtime_equipment_from_wiki_draft(
            {"名称": "护手A", "_wiki_params": {"部位": "护手", "套装": "套装A"}}
        )
        accessories = [
            build_runtime_equipment_from_wiki_draft(
                {"名称": f"配件{i}", "_wiki_params": {"部位": "配件", "套装": "套装A"}}
            )
            for i in range(5)
        ]
        return {"chest": [chest], "gloves": [gloves], "accessories": accessories}

    def test_resume_skips_processed_combinations(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "search_runs.db"
            signature = "test-signature"
            base_context = DamageContext(final_attack=0.0, skill_multiplier=1.0, enemy_defense=0.0)
            weapons = [WeaponCandidate(name="武器A", final_attack=1000.0)]
            catalog = self._catalog()
            config = OptimizerConfig(top_n=3)

            first = execute_search_with_resume(
                db_path=db_path,
                run_signature=signature,
                base_context=base_context,
                weapons=weapons,
                equipment_catalog=catalog,
                config=config,
                max_workers=2,
                cancel_token=SearchCancelToken(cancel_after=4),
            )
            self.assertTrue(first.cancelled)
            self.assertEqual(first.processed_this_run, 4)

            progress_events: list[int] = []

            def _on_progress(info: dict) -> None:
                progress_events.append(int(info.get("processed", 0)))

            second = execute_search_with_resume(
                db_path=db_path,
                run_signature=signature,
                base_context=base_context,
                weapons=weapons,
                equipment_catalog=catalog,
                config=config,
                max_workers=2,
                progress_callback=_on_progress,
            )
            self.assertFalse(second.cancelled)
            self.assertGreater(second.skipped_preprocessed, 0)
            self.assertGreater(len(progress_events), 0)
            self.assertGreaterEqual(progress_events[0], second.skipped_preprocessed)
            self.assertEqual(second.processed_combinations, second.total_combinations)

    def test_mark_processed_batch_writes_keys(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = SearchRunStore(Path(tmp) / "search_runs.db")
            store.ensure_run("sig", 10)
            store.mark_processed_batch("sig", ["k1", "k2", "k3"])
            self.assertEqual(store.count_processed("sig"), 3)

    def test_full_search_persists_only_top_n_scores(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "search_runs.db"
            signature = "topn-signature"
            base_context = DamageContext(final_attack=0.0, skill_multiplier=1.0, enemy_defense=0.0)
            weapons = [WeaponCandidate(name="武器A", final_attack=1000.0)]
            catalog = self._catalog()
            config = OptimizerConfig(top_n=2)

            result = execute_search_with_resume(
                db_path=db_path,
                run_signature=signature,
                base_context=base_context,
                weapons=weapons,
                equipment_catalog=catalog,
                config=config,
                max_workers=2,
            )
            self.assertFalse(result.cancelled)
            store = SearchRunStore(db_path)
            self.assertLessEqual(store.count_score_rows(signature), 2)
            self.assertEqual(len(result.top_results), 2)

    def test_viewer_links_are_exposed_for_packaging_notice(self):
        links = get_sqlite_viewer_links()
        self.assertGreaterEqual(len(links), 1)
        self.assertTrue(any("sqlite" in link.lower() for link in links))


if __name__ == "__main__":
    unittest.main()
