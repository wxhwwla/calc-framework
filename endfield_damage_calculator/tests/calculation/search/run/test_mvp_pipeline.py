#!/usr/bin/env python3
"""MVP 端到端基线测试。"""

import tempfile
import unittest
from pathlib import Path

from calculation.damage.engine import DamageContext
from calculation.equipment.system import build_runtime_equipment_from_wiki_draft
from calculation.loadout.optimizer import OptimizerConfig, WeaponCandidate
from calculation.search.run.mvp import run_mvp_search_pipeline


class TestMvpPipeline(unittest.TestCase):
    def _catalog(self):
        return {
            "chest": [
                build_runtime_equipment_from_wiki_draft(
                    {"名称": "胸甲A", "_wiki_params": {"装备种类": "护甲", "所属套组": "套装A", "效果1": "易伤+5%"}}
                )
            ],
            "gloves": [
                build_runtime_equipment_from_wiki_draft(
                    {"名称": "护手A", "_wiki_params": {"部位": "护手", "套装": "套装A"}}
                )
            ],
            "accessories": [
                build_runtime_equipment_from_wiki_draft(
                    {
                        "名称": "配件A",
                        "_wiki_params": {"部位": "配件", "套装": "套装A", "三件套效果1": "易伤+10%"},
                    }
                )
            ],
        }

    def test_mvp_pipeline_runs_search_resume_and_export(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out = run_mvp_search_pipeline(
                db_path=root / "runs.db",
                export_dir=root / "exports",
                run_signature="mvp-demo-1",
                base_context=DamageContext(final_attack=0.0, skill_multiplier=1.0, enemy_defense=0.0),
                weapons=[WeaponCandidate(name="武器A", final_attack=1000.0)],
                equipment_catalog=self._catalog(),
                config=OptimizerConfig(top_n=3),
                max_workers=2,
            )
            self.assertGreaterEqual(out["processed_combinations"], 1)
            self.assertTrue(out["top_results"])
            self.assertIn("weapon_name", out["top_results"][0])
            self.assertTrue((root / "exports" / "top_results.json").is_file())
            self.assertTrue((root / "exports" / "top_results.csv").is_file())
            self.assertTrue((root / "exports" / "all_results.ndjson").is_file())


if __name__ == "__main__":
    unittest.main()
