#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SQLite 续跑与去重测试。"""

import tempfile
import unittest
from pathlib import Path

from calculation.damage_engine import DamageContext
from calculation.equipment_system import build_runtime_equipment_from_wiki_draft
from calculation.loadout_optimizer import OptimizerConfig, WeaponCandidate
from calculation.search_persistence import (
    execute_search_with_resume,
    get_sqlite_viewer_links,
)
from calculation.search_runner import SearchCancelToken


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

            second = execute_search_with_resume(
                db_path=db_path,
                run_signature=signature,
                base_context=base_context,
                weapons=weapons,
                equipment_catalog=catalog,
                config=config,
                max_workers=2,
            )
            self.assertFalse(second.cancelled)
            self.assertGreater(second.skipped_preprocessed, 0)
            self.assertEqual(second.processed_combinations, second.total_combinations)

    def test_viewer_links_are_exposed_for_packaging_notice(self):
        links = get_sqlite_viewer_links()
        self.assertGreaterEqual(len(links), 1)
        self.assertTrue(any("sqlite" in link.lower() for link in links))


if __name__ == "__main__":
    unittest.main()
