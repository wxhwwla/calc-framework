#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""仓库 README 双层结构约定。"""

import unittest

from calc_engine.endfield.tests.conftest import REPO_ROOT

_ROOT_README = REPO_ROOT / "README.md"
_PKG_README = REPO_ROOT / "games" / "endfield" / "README.md"


class TestReadmeLayers(unittest.TestCase):
    def test_repo_root_has_facade_readme(self):
        text = _ROOT_README.read_text(encoding="utf-8")
        self.assertIn("games/endfield/README.md", text)
        self.assertIn("docs/操作指令集.md", text)
        self.assertIn("tools/", text)
        self.assertIn("LICENSE", text)
        self.assertIn("DATA_LICENSE", text)

    def test_license_file_documents_agpl_and_commercial_dual_license(self):
        text = (REPO_ROOT / "LICENSE").read_text(encoding="utf-8")
        self.assertIn("AGPL-3.0", text)
        self.assertIn("商业许可", text)
        self.assertIn("充电", text)
        self.assertIn("DATA_LICENSE", text)

    def test_data_license_file_exists(self):
        path = REPO_ROOT / "DATA_LICENSE"
        self.assertTrue(path.is_file())
        self.assertIn("商业", path.read_text(encoding="utf-8"))

    def test_package_readme_links_back_to_root_docs(self):
        text = _PKG_README.read_text(encoding="utf-8")
        self.assertIn("../README.md", text)
        self.assertIn("../docs/操作指令集.md", text)


if __name__ == "__main__":
    unittest.main()
