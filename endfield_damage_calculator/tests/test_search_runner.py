#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""并行搜索执行器测试。"""

import unittest

from calculation.damage_engine import DamageContext
from calculation.equipment_system import build_runtime_equipment_from_wiki_draft
from calculation.loadout_optimizer import OptimizerConfig, WeaponCandidate
from calculation.search_runner import SearchCancelToken, run_search_parallel


class TestSearchRunner(unittest.TestCase):
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
            for i in range(6)
        ]
        return {"chest": [chest], "gloves": [gloves], "accessories": accessories}

    def test_parallel_runner_reports_progress_and_eta(self):
        progress_events = []

        def _on_progress(progress):
            progress_events.append(progress)

        result = run_search_parallel(
            base_context=DamageContext(final_attack=0.0, skill_multiplier=1.0, enemy_defense=0.0),
            weapons=[WeaponCandidate(name="武器A", final_attack=1000.0)],
            equipment_catalog=self._catalog(),
            config=OptimizerConfig(top_n=3),
            max_workers=2,
            progress_callback=_on_progress,
        )
        self.assertFalse(result.cancelled)
        self.assertGreater(result.processed_combinations, 0)
        self.assertGreater(len(progress_events), 0)
        self.assertTrue(any(evt["eta_seconds"] >= 0 for evt in progress_events))

    def test_parallel_runner_can_cancel_and_return_partial_results(self):
        token = SearchCancelToken(cancel_after=3)
        result = run_search_parallel(
            base_context=DamageContext(final_attack=0.0, skill_multiplier=1.0, enemy_defense=0.0),
            weapons=[WeaponCandidate(name="武器A", final_attack=1000.0)],
            equipment_catalog=self._catalog(),
            config=OptimizerConfig(top_n=3),
            max_workers=2,
            cancel_token=token,
        )
        self.assertTrue(result.cancelled)
        self.assertLess(result.processed_combinations, result.total_combinations)
        self.assertGreater(len(result.top_results), 0)


if __name__ == "__main__":
    unittest.main()
