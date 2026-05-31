#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""迁移脚本 tools/migrate_weapon_skills_schema.py 行为测试。"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools.migrate_weapon_skills_schema import migrate_file


class TestMigrateWeaponSkillsSchemaTool(unittest.TestCase):
    def test_migrate_file_dry_run_reports_changes_without_writing(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "weapons.json"
            original = [
                {
                    "名称": "武器A",
                    "基础攻击力": [1] * 90,
                    "敏捷+": [10.0] * 9,
                    "特殊能力1": [False],
                    "特殊能力2": [False],
                }
            ]
            path.write_text(json.dumps(original, ensure_ascii=False), encoding="utf-8")

            result = migrate_file(weapons_json=path, dry_run=True)
            self.assertEqual(result["changed_count"], 1)

            current = json.loads(path.read_text(encoding="utf-8"))
            self.assertIn("敏捷+", current[0])
            self.assertNotIn("normal_skills", current[0])

    def test_migrate_file_apply_writes_new_schema(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "weapons.json"
            original = [
                {
                    "名称": "武器A",
                    "基础攻击力": [1] * 90,
                    "敏捷+": [10.0] * 9,
                    "特殊能力1": [False],
                    "特殊能力2": [False],
                }
            ]
            path.write_text(json.dumps(original, ensure_ascii=False), encoding="utf-8")

            result = migrate_file(weapons_json=path, dry_run=False)
            self.assertEqual(result["changed_names"], ["武器A"])

            current = json.loads(path.read_text(encoding="utf-8"))
            self.assertNotIn("敏捷+", current[0])
            self.assertIn("normal_skills", current[0])


if __name__ == "__main__":
    unittest.main()
