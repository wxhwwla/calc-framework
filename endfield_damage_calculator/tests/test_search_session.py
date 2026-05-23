#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""搜索会话（内存 / 续跑分支）测试。"""

import tempfile
import unittest
from pathlib import Path

from calculation.damage_engine import DamageContext
from calculation.equipment_system import build_runtime_equipment_from_wiki_draft
from calculation.loadout_optimizer import OptimizerConfig, WeaponCandidate
from calculation.search_cancel import SearchCancelToken
from calculation.search_session import run_search_session


class TestSearchSession(unittest.TestCase):
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
            for i in range(4)
        ]
        return {"chest": [chest], "gloves": [gloves], "accessories": accessories}

    def test_memory_path_returns_warnings_when_no_combinations(self):
        result = run_search_session(
            base_context=DamageContext(final_attack=0.0, skill_multiplier=1.0),
            weapons=[],
            equipment_catalog=self._catalog(),
            config=OptimizerConfig(top_n=3),
        )
        self.assertEqual(result.total_combinations, 0)
        self.assertEqual(result.top_results, ())

    def test_memory_path_completes_small_search(self):
        result = run_search_session(
            base_context=DamageContext(final_attack=0.0, skill_multiplier=1.0, enemy_defense=0.0),
            weapons=[WeaponCandidate(name="武器A", final_attack=1000.0)],
            equipment_catalog=self._catalog(),
            config=OptimizerConfig(top_n=2),
            max_workers=1,
        )
        self.assertGreater(result.total_combinations, 0)
        self.assertEqual(result.processed_combinations, result.total_combinations)
        self.assertGreater(len(result.top_results), 0)

    def test_resume_path_delegates_with_signature(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "search_runs.db"
            result = run_search_session(
                base_context=DamageContext(final_attack=0.0, skill_multiplier=1.0, enemy_defense=0.0),
                weapons=[WeaponCandidate(name="武器A", final_attack=1000.0)],
                equipment_catalog=self._catalog(),
                config=OptimizerConfig(top_n=2),
                max_workers=1,
                db_path=db_path,
                run_signature="test-run-sig",
            )
            self.assertGreater(result.processed_combinations, 0)
            self.assertTrue(db_path.is_file())

    def test_memory_path_honours_cancel_token(self):
        token = SearchCancelToken(cancel_after=2)
        result = run_search_session(
            base_context=DamageContext(final_attack=0.0, skill_multiplier=1.0, enemy_defense=0.0),
            weapons=[WeaponCandidate(name="武器A", final_attack=1000.0)],
            equipment_catalog=self._catalog(),
            config=OptimizerConfig(top_n=3),
            max_workers=1,
            cancel_token=token,
        )
        self.assertTrue(result.cancelled)
        self.assertLess(result.processed_combinations, result.total_combinations)


if __name__ == "__main__":
    unittest.main()
