#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""搜索结果导出测试。"""

import json
import tempfile
import unittest
from pathlib import Path

from calculation.loadout_optimizer import LoadoutScore
from calculation.result_export import export_search_outputs


class TestResultExport(unittest.TestCase):
    def test_export_top_json_and_csv_and_all_ndjson(self):
        scores = (
            LoadoutScore(
                weapon_name="武器A",
                final_damage=1234.5,
                loadout_names={
                    "chest": "胸甲A",
                    "gloves": "护手A",
                    "accessory_a": "配件1",
                    "accessory_b": "配件2",
                },
            ),
            LoadoutScore(
                weapon_name="武器B",
                final_damage=1000.0,
                loadout_names={
                    "chest": "胸甲B",
                    "gloves": "护手A",
                    "accessory_a": "配件3",
                    "accessory_b": "配件4",
                },
            ),
        )
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp)
            outputs = export_search_outputs(
                scores=scores,
                output_dir=out_dir,
                top_n=1,
                export_all=True,
            )
            self.assertTrue(outputs["top_json"].is_file())
            self.assertTrue(outputs["top_csv"].is_file())
            self.assertTrue(outputs["all_ndjson"].is_file())

            top_json_data = json.loads(outputs["top_json"].read_text(encoding="utf-8"))
            self.assertEqual(len(top_json_data), 1)
            self.assertEqual(top_json_data[0]["weapon_name"], "武器A")

            csv_text = outputs["top_csv"].read_text(encoding="utf-8")
            self.assertIn("rank,weapon_name,final_damage,chest,gloves,accessory_a,accessory_b", csv_text)
            self.assertIn("1,武器A,1234.5,胸甲A,护手A,配件1,配件2", csv_text)

            ndjson_lines = [
                line for line in outputs["all_ndjson"].read_text(encoding="utf-8").splitlines() if line.strip()
            ]
            self.assertEqual(len(ndjson_lines), 2)


if __name__ == "__main__":
    unittest.main()
