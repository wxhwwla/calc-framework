# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""全量搜索诊断日志模块测试。"""

from __future__ import annotations

import logging
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import utils.search_diagnostics as sd


class TestSearchDiagnostics(unittest.TestCase):
    def setUp(self) -> None:
        sd._initialized = False
        sd._search_logger = None
        sd._crash_file = None
        if hasattr(sd._install_exception_hooks, "_done"):
            sd._install_exception_hooks._done = False  # type: ignore[attr-defined]

    def _shutdown(self) -> None:
        self.tearDown()

    def tearDown(self) -> None:
        import faulthandler

        if sd._crash_file is not None:
            try:
                faulthandler.disable()
                sd._crash_file.close()
            except OSError:
                pass
            sd._crash_file = None
        logger = logging.getLogger(sd._LOGGER_NAME)
        for handler in list(logger.handlers):
            try:
                handler.close()
            except OSError:
                pass
            logger.removeHandler(handler)
        sd._initialized = False
        sd._search_logger = None
        sys.excepthook = sys.__excepthook__
        if hasattr(sd._install_exception_hooks, "_done"):
            sd._install_exception_hooks._done = False  # type: ignore[attr-defined]

    def test_init_creates_search_log(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            log_dir = Path(tmp) / "logs"
            with patch.object(sd, "get_logs_dir", return_value=log_dir):
                with patch.dict("os.environ", {"CALC_DISABLE_CRASH_LOG": "1"}, clear=False):
                    result = sd.init_search_diagnostics(force=True)

            self.assertEqual(result, log_dir)
            self.assertTrue((log_dir / "search.log").exists())
            content = (log_dir / "search.log").read_text(encoding="utf-8")
            self.assertIn("搜索诊断日志就绪", content)
            self._shutdown()

    def test_log_search_config_sorted_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            log_dir = Path(tmp) / "logs"
            with patch.object(sd, "get_logs_dir", return_value=log_dir):
                with patch.dict("os.environ", {"CALC_DISABLE_CRASH_LOG": "1"}, clear=False):
                    sd.init_search_diagnostics(force=True)
                    sd.log_search_config(phase="test", total=100, backend="thread")

            content = (log_dir / "search.log").read_text(encoding="utf-8")
            self.assertIn("搜索启动", content)
            self.assertIn("backend='thread'", content)
            self.assertIn("total=100", content)
            self._shutdown()

    def test_summarize_work_item_truncates(self) -> None:
        long_item = {"x": "y" * 300}
        text = sd.summarize_work_item(long_item, max_len=50)
        self.assertLessEqual(len(text), 50)
        self.assertTrue(text.endswith("..."))

    def test_excepthook_writes_crash_log(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            log_dir = Path(tmp) / "logs"
            with patch.object(sd, "get_logs_dir", return_value=log_dir):
                with patch.dict("os.environ", {"CALC_DISABLE_CRASH_LOG": "1"}, clear=False):
                    sd.init_search_diagnostics(force=True)

            crash_path = log_dir / "crash.log"
            sys.excepthook(ValueError, ValueError("diag-test"), None)

            self.assertTrue(crash_path.exists())
            self.assertIn("diag-test", crash_path.read_text(encoding="utf-8"))
            self._shutdown()

    def test_frozen_default_log_level_debug(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            log_dir = Path(tmp) / "logs"
            with patch.object(sd, "get_logs_dir", return_value=log_dir):
                with patch.dict("os.environ", {}, clear=True):
                    with patch.object(sys, "frozen", True, create=True):
                        sd.init_search_diagnostics(force=True)

            logger = logging.getLogger(sd._LOGGER_NAME)
            self.assertEqual(logger.level, logging.DEBUG)
            self._shutdown()


if __name__ == "__main__":
    unittest.main()
