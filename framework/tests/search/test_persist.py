# SPDX-License-Identifier: AGPL-3.0
"""SearchRunStore 单元测试。"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from calc_framework.search.persist import SearchRunStore


class TestSearchRunStore(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.mkdtemp()
        self.db_path = Path(self._tmpdir) / "search_runs.db"
        self.store = SearchRunStore(self.db_path)

    def tearDown(self) -> None:
        if self.db_path.exists():
            self.db_path.unlink()
        Path(self._tmpdir).rmdir()

    def test_ensure_run_creates_entry(self) -> None:
        self.store.ensure_run("sig001", total_combinations=100)
        status = self.store.run_status("sig001")
        self.assertEqual(status, "running")

    def test_mark_run_status(self) -> None:
        self.store.ensure_run("sig001", 100)
        self.store.mark_run_status("sig001", "completed")
        self.assertEqual(self.store.run_status("sig001"), "completed")

    def test_get_processed_keys_empty(self) -> None:
        self.store.ensure_run("sig001", 100)
        keys = self.store.get_processed_keys("sig001")
        self.assertEqual(keys, set())

    def test_mark_processed_batch(self) -> None:
        self.store.ensure_run("sig001", 100)
        self.store.mark_processed_batch("sig001", ["k1", "k2", "k3"])
        keys = self.store.get_processed_keys("sig001")
        self.assertEqual(keys, {"k1", "k2", "k3"})

    def test_count_processed(self) -> None:
        self.store.ensure_run("sig001", 100)
        self.store.mark_processed_batch("sig001", ["k1", "k2"])
        self.assertEqual(self.store.count_processed("sig001"), 2)

    def test_mark_processed_empty_batch(self) -> None:
        self.store.ensure_run("sig001", 100)
        self.store.mark_processed_batch("sig001", [])  # no crash
        self.assertEqual(self.store.count_processed("sig001"), 0)

    def test_delete_run(self) -> None:
        self.store.ensure_run("sig001", 100)
        self.store.mark_processed_batch("sig001", ["k1"])
        self.store.delete_run("sig001")
        self.assertIsNone(self.store.run_status("sig001"))
        self.assertEqual(self.store.count_processed("sig001"), 0)

    def test_two_runs_independent(self) -> None:
        self.store.ensure_run("sig001", 100)
        self.store.ensure_run("sig002", 200)
        self.store.mark_processed_batch("sig001", ["a", "b"])
        self.store.mark_processed_batch("sig002", ["c"])
        self.assertEqual(self.store.count_processed("sig001"), 2)
        self.assertEqual(self.store.count_processed("sig002"), 1)
