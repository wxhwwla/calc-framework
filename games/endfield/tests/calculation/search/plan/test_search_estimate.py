#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""搜索工作量与耗时预估测试。"""

import unittestfrom games.endfield.calc.damage.engine import DamageContextfrom games.endfield.calc.loadout.optimizer import OptimizerConfig, WeaponCandidate, enumerate_optimizer_tasksfrom games.endfield.calc.search.plan.estimate import (    count_loadout_combinations,    estimate_search_duration,    format_duration_human,    format_workload_estimate_line,    preview_search_workload,)class TestSearchEstimate(unittest.TestCase):
    def test_count_loadout_combinations_matches_enumerate_on_small_catalog(self):
        catalog = {
            "chest": [{"名称": "c1", "部位": "护甲", "效果": [], "三件套效果": []}],
            "gloves": [{"名称": "g1", "部位": "护手", "效果": [], "三件套效果": []}],
            "accessories": [
                {"名称": "a1", "部位": "配件", "效果": [], "三件套效果": []},
                {"名称": "a2", "部位": "配件", "效果": [], "三件套效果": []},
            ],
        }
        loadouts = count_loadout_combinations(catalog, allow_duplicate_accessory=True)
        self.assertEqual(loadouts, 4)
        weapons = [WeaponCandidate(name="w1", final_attack=1000.0)]
        config = OptimizerConfig(prune_non_beneficial=False, warn_on_unfiltered=False)
        preview = preview_search_workload(
            weapons=weapons,
            equipment_catalog=catalog,
            config=config,
        )
        tasks, total, _, _ = enumerate_optimizer_tasks(
            base_context=DamageContext(final_attack=0.0, skill_multiplier=1.0),
            weapons=weapons,
            equipment_catalog=catalog,
            config=config,
        )
        self.assertEqual(preview.total_combinations, total)
        self.assertEqual(sum(1 for _ in tasks), 4)

    def test_estimate_duration_scales_with_workers(self):
        slow = estimate_search_duration(total_combinations=10_000, max_workers=1)
        fast = estimate_search_duration(total_combinations=10_000, max_workers=4)
        self.assertGreater(slow.estimated_seconds, fast.estimated_seconds)

    def test_format_workload_estimate_line_mentions_combinations_and_time(self):
        from games.endfield.calc.search.plan.estimate import SearchDurationEstimate, SearchWorkloadPreview

        line = format_workload_estimate_line(
            workload=SearchWorkloadPreview(
                total_combinations=12_000,
                weapon_count=3,
                loadout_combinations=4_000,
                warnings=(),
            ),
            duration=SearchDurationEstimate(
                total_combinations=12_000,
                max_workers=8,
                estimated_seconds=90.0,
                seconds_per_combo=0.0001,
            ),
        )
        self.assertIn("12,000", line)
        self.assertIn("预计耗时", line)
        self.assertIn(format_duration_human(90.0), line)


if __name__ == "__main__":
    unittest.main()
