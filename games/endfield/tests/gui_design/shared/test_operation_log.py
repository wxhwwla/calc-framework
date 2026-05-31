#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""分级操作日志测试。"""

import json
import tempfile
import unittest
from pathlib import Path

from utils.operation_log import LogLevel, OperationLog, get_session_operation_log, reset_session_operation_log


class TestOperationLog(unittest.TestCase):
    def setUp(self) -> None:
        reset_session_operation_log()

    def test_records_user_visible_actions_at_info_or_above(self) -> None:
        log = OperationLog(min_level=LogLevel.INFO)
        log.record(LogLevel.USER, "confirm_selection", {"mode": "zone_snapshot"})
        log.record(LogLevel.DEBUG, "internal_trace", {"_hidden": True})
        exported = json.loads(log.export_json())
        self.assertEqual(len(exported["entries"]), 1)
        self.assertEqual(exported["entries"][0]["action"], "confirm_selection")

    def test_export_to_file_writes_utf8_json(self) -> None:
        log = OperationLog()
        log.record(LogLevel.ERROR, "search_failed", {"reason": "cancelled"})
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "session_log.json"
            log.export_to_file(path)
            payload = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(payload["entries"][0]["level"], "ERROR")

    def test_session_singleton_returns_same_instance(self) -> None:
        a = get_session_operation_log()
        b = get_session_operation_log()
        self.assertIs(a, b)


if __name__ == "__main__":
    unittest.main()
