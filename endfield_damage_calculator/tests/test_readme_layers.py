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

    def test_package_readme_links_back_to_root_docs(self):
        text = _PKG_README.read_text(encoding="utf-8")
        self.assertIn("../README.md", text)
        self.assertIn("../docs/操作指令集.md", text)


if __name__ == "__main__":
    unittest.main()
