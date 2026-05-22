#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""数据来源与许可模块测试。"""

import unittest
from pathlib import Path

from legal.attribution import (
    ATTRIBUTION_DIALOG_MINSIZE,
    ATTRIBUTION_DIALOG_SIZE,
    ATTRIBUTION_DOC_URL,
    BWIKI_ZMD_URL,
    COMMERCIAL_OUTLINE_URL,
    DATA_LICENSE_URL,
    LICENSE_URL,
    NOTICES_URL,
    SUMMARY_TEXT,
    attribution_doc_local_path,
    data_license_local_path,
    notices_local_path,
)

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent


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
            _REPO_ROOT / "docs" / "商业许可要点.md",
            _REPO_ROOT / "docs" / "合规自查清单.md",
            _REPO_ROOT / "tools" / "bwiki_scout" / "scout.py",
        ]
        for path in paths:
            self.assertTrue(path.is_file(), path)

    def test_license_is_agpl_dual(self):
        text = (_REPO_ROOT / "LICENSE").read_text(encoding="utf-8")
        self.assertIn("AGPL-3.0", text)
        self.assertIn("商业许可", text)
        self.assertIn("DATA_LICENSE", text)


if __name__ == "__main__":
    unittest.main()
