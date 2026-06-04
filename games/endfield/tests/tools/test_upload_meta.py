#!/usr/bin/env python3

# SPDX-License-Identifier: AGPL-3.0
"""upload_meta 版本与总结块测试"""

import re
import tempfile
import unittest
from pathlib import Path

from scripts._version import ensure_summary_marker_assignments
from scripts.upload_meta import (
    SUMMARY_BEGIN,
    SUMMARY_END,
    build_commit_message,
    bump_minor,
    bump_patch,
    classify_changed_paths,
    read_summary_for_commit,
    read_version,
    remove_summary_block,
    write_summary_block,
    write_version,
)


class TestUploadMeta(unittest.TestCase):
    def test_bump_patch_and_minor(self):
        self.assertEqual(bump_patch("1.8.1"), "1.8.2")

        self.assertEqual(bump_minor("1.8.1"), "1.9.0")

    def test_classify_business_paths(self):
        self.assertTrue(
            classify_changed_paths(
                ["games/endfield/gui/gui.py"],
                "games/endfield",
            )
        )

        self.assertFalse(
            classify_changed_paths(
                ["games/endfield/please_read_me.py"],
                "games/endfield",
            )
        )

        self.assertFalse(
            classify_changed_paths(
                ["scripts/_version.py"],
                "games/endfield",
            )
        )

        self.assertFalse(
            classify_changed_paths(
                ["scripts/please_read_me.py"],
                "games/endfield",
            )
        )

        self.assertTrue(
            classify_changed_paths(
                ["framework/foo.py"],
                "games/endfield",
            )
        )

    def test_summary_block_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "please_read_me.py"

            path.write_text('_VERSION = "1.0.0"\n', encoding="utf-8")

            write_summary_block(path, "更新武器数据", ["修改 weapons.json"])

            title, bullets = read_summary_for_commit(path)

            self.assertEqual(title, "更新武器数据")

            self.assertEqual(bullets, ["修改 weapons.json"])

            msg = build_commit_message("1.0.1", title, bullets)

            self.assertIn("v1.0.1: 更新武器数据", msg)

            self.assertIn("- 修改 weapons.json", msg)

            remove_summary_block(path)

            text = path.read_text(encoding="utf-8")

            self.assertNotIn(SUMMARY_BEGIN, text)

            self.assertNotIn(SUMMARY_END, text)

    def test_ensure_summary_marker_assignments_repairs_empty_begin(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "_version.py"
            path.write_text(
                "# ==============================================================\n\n"
                'SUMMARY_BEGIN = ""\n'
                '_VERSION_PATTERN = re.compile(r"x")\n'
                '_VERSION = "1.0.0"\n',
                encoding="utf-8",
            )
            self.assertTrue(ensure_summary_marker_assignments(path))
            text = path.read_text(encoding="utf-8")
            self.assertIn("SUMMARY_BEGIN = _UPLOAD_SUMMARY_BEGIN", text)
            self.assertIn("SUMMARY_END = _UPLOAD_SUMMARY_END", text)

    def test_ensure_repairs_empty_upload_summary_begin(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "_version.py"
            path.write_text(
                "# ==============================================================\n\n"
                '_UPLOAD_SUMMARY_BEGIN = ""\n'
                "SUMMARY_BEGIN = _UPLOAD_SUMMARY_BEGIN\n"
                "SUMMARY_END = _UPLOAD_SUMMARY_END\n"
                '_VERSION_PATTERN = re.compile(r"x")\n'
                '_VERSION = "1.0.0"\n',
                encoding="utf-8",
            )
            self.assertTrue(ensure_summary_marker_assignments(path))
            text = path.read_text(encoding="utf-8")
            self.assertNotIn('_UPLOAD_SUMMARY_BEGIN = ""', text)
            self.assertIn('_SUMMARY_MARKER_BEGIN = "# --- BEGIN UPLOAD_SUMMARY ---"', text)

    def test_write_version_keeps_summary_markers(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "_version.py"
            path.write_text(
                """# ==============================================================

_SUMMARY_MARKER_BEGIN = "# --- BEGIN UPLOAD_SUMMARY ---"
_SUMMARY_MARKER_END = "# --- END UPLOAD_SUMMARY ---"
_UPLOAD_SUMMARY_BEGIN = _SUMMARY_MARKER_BEGIN
_UPLOAD_SUMMARY_END = _SUMMARY_MARKER_END
SUMMARY_BEGIN = _UPLOAD_SUMMARY_BEGIN
SUMMARY_END = _UPLOAD_SUMMARY_END
_VERSION_PATTERN = re.compile(
    r'^(_VERSION\\s*=\\s*["\\'])([^"\\']+)(["\\'])',
    re.MULTILINE,
)
_VERSION = "1.0.0"
""",
                encoding="utf-8",
            )
            write_version(path, "1.0.1")
            text = path.read_text(encoding="utf-8")
            self.assertIn("SUMMARY_BEGIN = _UPLOAD_SUMMARY_BEGIN", text)
            self.assertIn("SUMMARY_END = _UPLOAD_SUMMARY_END", text)
            self.assertEqual(read_version(path), "1.0.1")

    def test_ensure_summary_marker_assignments_repairs_crlf(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "_version.py"
            path.write_text(
                "# ==============================================================\n\n"
                'SUMMARY_BEGIN = "# --- BEGIN UPLOAD_SUMMARY ---"\r\n'
                'SUMMARY_END = "# --- END UPLOAD_SUMMARY ---"\r\n'
                '_VERSION_PATTERN = re.compile(r"x")\n'
                '_VERSION = "1.0.0"\n',
                encoding="utf-8",
            )
            self.assertTrue(ensure_summary_marker_assignments(path))
            text = path.read_text(encoding="utf-8")
            self.assertIn("SUMMARY_BEGIN = _UPLOAD_SUMMARY_BEGIN", text)
            self.assertEqual(len(re.findall(r"^SUMMARY_END\s*=", text, re.MULTILINE)), 1)

    def test_strip_summary_keeps_workflow_doc_mention(self):
        """删除末尾总结块时，不得截断 UPLOAD_WORKFLOW 字符串内的说明文字。"""

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "please_read_me.py"

            path.write_text(
                f'UPLOAD_WORKFLOW = """\n'
                f"说明 {SUMMARY_BEGIN} 标记\n"
                f'"""\n'
                f"def get_version():\n"
                f'    return "1.0.0"\n'
                f"\n{SUMMARY_BEGIN}\n"
                f"# TITLE: t\n# BODY:\n# - a\n"
                f"{SUMMARY_END}\n",
                encoding="utf-8",
            )

            remove_summary_block(path)

            text = path.read_text(encoding="utf-8")

            self.assertIn('UPLOAD_WORKFLOW = """', text)

            self.assertIn("def get_version():", text)

            self.assertNotIn(SUMMARY_END, text)

    def test_write_version(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "please_read_me.py"

            path.write_text('_VERSION = "1.2.3"\n', encoding="utf-8")

            write_version(path, "1.2.4")

            self.assertEqual(read_version(path), "1.2.4")


if __name__ == "__main__":
    unittest.main()
