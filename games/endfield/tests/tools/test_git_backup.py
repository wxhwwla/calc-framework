#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""git_backup 模块测试。"""

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts.tools import git_backup


class TestGitBackup(unittest.TestCase):
    def test_backup_creates_snapshot_with_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            git_dir = root / ".git"
            git_dir.mkdir()
            (git_dir / "HEAD").write_text("ref: refs/heads/main\n", encoding="utf-8")

            with mock.patch.object(git_backup, "_git_head", return_value="abc123"):
                dest = git_backup.backup_git_dir(
                    root,
                    current_version="1.2.3",
                    bump_kind="minor",
                )

            self.assertTrue((dest / ".git" / "HEAD").is_file())
            manifest = json.loads((dest / git_backup.MANIFEST_NAME).read_text(encoding="utf-8"))
            self.assertEqual(manifest["current_version"], "1.2.3")
            self.assertEqual(manifest["bump_kind"], "minor")
            self.assertEqual(manifest["head"], "abc123")

    def test_backup_missing_git_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(FileNotFoundError):
                git_backup.backup_git_dir(Path(tmp), current_version="1.0.0")

    def test_prune_keeps_latest_snapshots(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "snapshots"
            root.mkdir(parents=True)
            for name in ("a", "b", "c"):
                path = root / name
                path.mkdir()
                (path / "marker").write_text(name, encoding="utf-8")

            git_backup._prune_old_snapshots(root, keep=2)
            remaining = sorted(p.name for p in root.iterdir() if p.is_dir())
            self.assertEqual(len(remaining), 2)


if __name__ == "__main__":
    unittest.main()
