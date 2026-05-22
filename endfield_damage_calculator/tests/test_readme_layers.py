#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""仓库 README 双层结构约定。"""

import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_ROOT_README = _REPO_ROOT / "README.md"
_PKG_README = _REPO_ROOT / "endfield_damage_calculator" / "README.md"


class TestReadmeLayers(unittest.TestCase):
    def test_repo_root_has_facade_readme(self):
        text = _ROOT_README.read_text(encoding="utf-8")
        self.assertIn("endfield_damage_calculator/README.md", text)
        self.assertIn("docs/操作指令集.md", text)
        self.assertIn("LICENSE", text)
        self.assertIn("DATA_LICENSE", text)

    def test_license_file_documents_agpl_and_commercial_dual_license(self):
        text = (_REPO_ROOT / "LICENSE").read_text(encoding="utf-8")
        self.assertIn("AGPL-3.0", text)
        self.assertIn("商业许可", text)
        self.assertIn("充电", text)
        self.assertIn("DATA_LICENSE", text)

    def test_data_license_file_exists(self):
        path = _REPO_ROOT / "DATA_LICENSE"
        self.assertTrue(path.is_file())
        self.assertIn("商业", path.read_text(encoding="utf-8"))

    def test_package_readme_links_back_to_root_docs(self):
        text = _PKG_README.read_text(encoding="utf-8")
        self.assertIn("../README.md", text)
        self.assertIn("../docs/操作指令集.md", text)


if __name__ == "__main__":
    unittest.main()
