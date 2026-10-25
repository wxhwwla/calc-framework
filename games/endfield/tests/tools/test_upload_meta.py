#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""upload_meta / _version 版本与提交说明测试（无 UPLOAD_SUMMARY 磁盘块）。"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.upload_meta import (
    build_commit_message,
    bump_minor,
    bump_patch,
    classify_changed_paths,
    read_version,
    summarize_changes,
    write_version,
)


class TestUploadMeta(unittest.TestCase):
    def test_bump_patch_and_minor(self) -> None:
        self.assertEqual(bump_patch("1.8.1"), "1.8.2")
        self.assertEqual(bump_minor("1.8.1"), "1.9.0")

    def test_classify_business_paths(self) -> None:
        self.assertTrue(
            classify_changed_paths(
                ["games/endfield/gui/gui.py"],
                "games/endfield",
            )
        )
        self.assertFalse(
            classify_changed_paths(
                ["scripts/_version.py"],
                "games/endfield",
            )
        )
        self.assertTrue(
            classify_changed_paths(
                ["framework/foo.py"],
                "games/endfield",
            )
        )

    def test_write_and_read_version(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "_version.py"
            path.write_text(
                '_VERSION = "1.0.0"\n_EXE_VERSION = "0.1.0-beta"\n',
                encoding="utf-8",
            )
            self.assertEqual(read_version(path), "1.0.0")
            write_version(path, "1.0.1")
            self.assertEqual(read_version(path), "1.0.1")
            # 写版本不得再夹带 SUMMARY 标记
            text = path.read_text(encoding="utf-8")
            self.assertNotIn("UPLOAD_SUMMARY", text)
            self.assertNotIn("SUMMARY_MARKER", text)

    def test_summarize_and_commit_message_in_memory(self) -> None:
        title, bullets = summarize_changes(["games/endfield/data/weapons.json", "docs/README.md"])
        self.assertTrue(title)
        self.assertGreaterEqual(len(bullets), 1)
        msg = build_commit_message("3.29.25", title, bullets)
        self.assertTrue(msg.startswith("v3.29.25:"))
        self.assertIn("- ", msg)


if __name__ == "__main__":
    unittest.main()
