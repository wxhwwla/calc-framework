#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""AK compact 工具 — 无 parsed/ 时跳过。"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))


class TestArknightsCompactApply(unittest.TestCase):
    def test_compact_skips_without_parsed_dir(self) -> None:
        from games.arknights.operator_catalog import DEFAULT_PARSED_DIR
        from tools.data_pipeline.compact_arknights_operators import compact_parsed_dir

        if DEFAULT_PARSED_DIR.is_dir():
            self.skipTest("本地已有 parsed/，请人工执行 compact --apply")
        report = compact_parsed_dir(DEFAULT_PARSED_DIR, apply=False)
        self.assertFalse(report.get("success"))
        self.assertIn("不存在", str(report.get("error", "")))


if __name__ == "__main__":
    unittest.main()
