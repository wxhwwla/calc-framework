#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""多进程搜索并行测试。"""

import unittest

from games.endfield.calc.damage.engine import DamageContext
from games.endfield.calc.equipment.system import build_runtime_equipment_from_wiki_draft
from games.endfield.calc.loadout.optimizer import OptimizerConfig, WeaponCandidate
from games.endfield.calc.search.run.cancel import SearchCancelToken
from games.endfield.calc.search.run.session import run_search_session


class TestProcessParallelSearch(unittest.TestCase):
    def _catalog(self):
        chest = build_runtime_equipment_from_wiki_draft(
            {"名称": "胸甲P", "_wiki_params": {"装备种类": "护甲", "所属套组": "套装P"}}
        )
        gloves = build_runtime_equipment_from_wiki_draft(
            {"名称": "护手P", "_wiki_params": {"部位": "护手", "套装": "套装P"}}
        )
        accessories = [
            build_runtime_equipment_from_wiki_draft(
                {"名称": f"配件P{i}", "_wiki_params": {"部位": "配件", "套装": "套装P"}}
            )
            for i in range(3)
        ]
        return {"chest": [chest], "gloves": [gloves], "accessories": accessories}

    def test_memory_search_with_process_backend(self):
        result = run_search_session(
            base_context=DamageContext(final_attack=0.0, skill_multiplier=1.0, enemy_defense=0.0),
            weapons=[WeaponCandidate(name="武器P", final_attack=1000.0)],
            equipment_catalog=self._catalog(),
            config=OptimizerConfig(top_n=2),
            max_workers=2,
            parallel_backend="process",
        )
        self.assertGreater(result.total_combinations, 0)
        self.assertEqual(result.processed_combinations, result.total_combinations)
        self.assertGreater(len(result.top_results), 0)

    def test_cancel_under_process_backend(self):
        token = SearchCancelToken(cancel_after=1)
        result = run_search_session(
            base_context=DamageContext(final_attack=0.0, skill_multiplier=1.0, enemy_defense=0.0),
            weapons=[WeaponCandidate(name="武器P", final_attack=1000.0)],
            equipment_catalog=self._catalog(),
            config=OptimizerConfig(top_n=2),
            max_workers=2,
            cancel_token=token,
            parallel_backend="process",
        )
        self.assertTrue(result.cancelled)
        self.assertLess(result.processed_combinations, result.total_combinations)


if __name__ == "__main__":
    unittest.main()
