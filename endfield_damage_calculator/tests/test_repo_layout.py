#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""仓库根目录门面分区约定（tools / docs / legacy）。"""

import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent


class TestRepoLayout(unittest.TestCase):
    def test_bwiki_scout_lives_under_tools(self):
        scout = _REPO_ROOT / "tools" / "bwiki_scout" / "scout.py"
        self.assertTrue(scout.is_file(), "BWIKI 侦察应在 tools/bwiki_scout/")

    def test_old_scripts_bwiki_path_removed(self):
        old = _REPO_ROOT / "scripts" / "bwiki_scout"
        self.assertFalse(old.exists(), "不应再保留 scripts/bwiki_scout/")

    def test_algorithm_documentation_in_docs(self):
        doc = _REPO_ROOT / "docs" / "算法与架构.md"
        self.assertTrue(doc.is_file())
        text = doc.read_text(encoding="utf-8")
        self.assertIn("乘区", text)

    def test_root_project_doc_points_to_docs(self):
        stub = _REPO_ROOT / "PROJECT_DOCUMENTATION.md"
        self.assertTrue(stub.is_file())
        self.assertIn("算法与架构", stub.read_text(encoding="utf-8"))

    def test_legacy_character_script_not_at_root(self):
        self.assertFalse((_REPO_ROOT / "_add_character_legacy.py").exists())
        legacy = _REPO_ROOT / "legacy" / "_add_character_legacy.py"
        self.assertTrue(legacy.is_file())

    def test_tools_readme_describes_maintenance_zone(self):
        readme = _REPO_ROOT / "tools" / "README.md"
        self.assertTrue(readme.is_file())
        text = readme.read_text(encoding="utf-8")
        self.assertIn("bwiki_scout", text)
        self.assertIn("仓库根目录", text)


if __name__ == "__main__":
    unittest.main()
