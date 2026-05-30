#!/usr/bin/env python3
"""仓库根目录门面分区约定（tools / docs / legacy）。"""

import unittest

from adapters.endfield.tests.conftest import REPO_ROOT


class TestRepoLayout(unittest.TestCase):
    def test_bwiki_scout_lives_under_tools(self):
        scout = REPO_ROOT / "tools" / "bwiki_scout" / "scout.py"
        self.assertTrue(scout.is_file(), "BWIKI 侦察应在 tools/bwiki_scout/")

    def test_old_scripts_bwiki_path_removed(self):
        old = REPO_ROOT / "scripts" / "bwiki_scout"
        self.assertFalse(old.exists(), "不应再保留 scripts/bwiki_scout/")

    def test_algorithm_documentation_in_docs(self):
        doc = REPO_ROOT / "docs" / "算法与架构.md"
        self.assertTrue(doc.is_file())
        text = doc.read_text(encoding="utf-8")
        self.assertIn("乘区", text)

    def test_root_project_doc_points_to_docs(self):
        stub = REPO_ROOT / "PROJECT_DOCUMENTATION.md"
        self.assertTrue(stub.is_file())
        self.assertIn("算法与架构", stub.read_text(encoding="utf-8"))

    def test_legacy_character_script_fully_removed(self):
        self.assertFalse((REPO_ROOT / "_add_character_legacy.py").exists())
        self.assertFalse((REPO_ROOT / "legacy").exists(),
                         "legacy/ 目录已清理完毕")

    def test_tools_readme_describes_maintenance_zone(self):
        readme = REPO_ROOT / "tools" / "README.md"
        self.assertTrue(readme.is_file())
        text = readme.read_text(encoding="utf-8")
        self.assertIn("bwiki_scout", text)
        self.assertIn("仓库根目录", text)


if __name__ == "__main__":
    unittest.main()
