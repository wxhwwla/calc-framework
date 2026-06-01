#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""明日方舟干员数据源：目录不足时回退 zip。"""

from __future__ import annotations

import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

import sys
from pathlib import Path

_BACKEND = Path(__file__).resolve().parents[1]
_REPO = _BACKEND.parents[1]
sys.path.insert(0, str(_REPO / "framework" / "src"))
sys.path.insert(0, str(_REPO))
sys.path.insert(0, str(_BACKEND))

from api.arknights import (  # noqa: E402
    _DATA_DIR,
    _arknights_zip_path,
    _load_operator,
    _resolve_operator_names,
)


class TestArknightsDataFallback(unittest.TestCase):
    def test_resolve_prefers_full_parsed_dir(self) -> None:
        if not _DATA_DIR.is_dir():
            self.skipTest("无 parsed 目录")
        names = _resolve_operator_names()
        self.assertGreaterEqual(len(names), 100)

    def test_resolve_falls_back_to_zip_when_parsed_sparse(self) -> None:
        if _arknights_zip_path() is None:
            self.skipTest("无 arknights_parsed.zip")

        with tempfile.TemporaryDirectory() as tmp:
            sparse = Path(tmp) / "parsed"
            sparse.mkdir()
            (sparse / "12F.json").write_text(
                json.dumps({"名称": "12F"}, ensure_ascii=False), encoding="utf-8",
            )
            with patch("api.arknights._DATA_DIR", sparse):
                names = _resolve_operator_names()
        self.assertGreater(len(names), 10)

    def test_load_operator_from_zip_only(self) -> None:
        zip_path = _arknights_zip_path()
        if zip_path is None:
            self.skipTest("无 zip")
        with zipfile.ZipFile(_arknights_zip_path()) as zf:
            first = next(n for n in zf.namelist() if n.endswith(".json"))
            stem = Path(first).stem
        with tempfile.TemporaryDirectory() as tmp:
            empty = Path(tmp) / "parsed"
            empty.mkdir()
            with patch("api.arknights._DATA_DIR", empty):
                data = _load_operator(stem)
        self.assertTrue(data)


if __name__ == "__main__":
    unittest.main()
