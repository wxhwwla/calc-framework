#!/usr/bin/env python3

# SPDX-License-Identifier: AGPL-3.0
"""数据来源与许可模块测试。"""

import unittest

from games.endfield.gui.legal.attribution_content import (
    ATTRIBUTION_DIALOG_MINSIZE,
    ATTRIBUTION_DIALOG_SIZE,
    SUMMARY_TEXT,
    attribution_doc_local_path,
    data_license_local_path,
    notices_local_path,
)
from games.endfield.tests.conftest import REPO_ROOT


class TestLegalAttribution(unittest.TestCase):
    def test_dialog_default_size_fits_all_buttons(self):
        w, h = ATTRIBUTION_DIALOG_SIZE

        min_w, min_h = ATTRIBUTION_DIALOG_MINSIZE

        self.assertGreaterEqual(h, 700)

        self.assertLessEqual(min_w, w)

        self.assertLessEqual(min_h, h)

    def test_summary_covers_acceptance_and_non_official(self):
        self.assertIn("非官方", SUMMARY_TEXT)

        self.assertIn("AGPL", SUMMARY_TEXT)

        self.assertIn("商业许可", SUMMARY_TEXT)

        self.assertIn("bwiki_scout", SUMMARY_TEXT)

    def test_compliance_docs_exist(self):
        paths = [
            attribution_doc_local_path(),
            data_license_local_path(),
            notices_local_path(),
            REPO_ROOT / "docs" / "商业许可要点.md",
            REPO_ROOT / "docs" / "合规自查清单.md",
            REPO_ROOT / "tools" / "bwiki_scout" / "scout.py",
        ]

        for path in paths:
            self.assertTrue(path.is_file(), path)

    def test_license_is_agpl_dual(self):
        text = (REPO_ROOT / "LICENSE").read_text(encoding="utf-8")

        self.assertIn("AGPL-3.0", text)

        self.assertIn("商业许可", text)

        self.assertIn("DATA_LICENSE", text)


if __name__ == "__main__":
    unittest.main()
