# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""日志模块测试 — setup_logging, get_logger, set_level, _resolve_level。"""

from __future__ import annotations

import logging
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from calc_framework.logging import _resolve_level, get_logger, set_level, setup_logging

_ROOT_LOGGER = logging.getLogger("calc_framework")


@pytest.fixture(autouse=True)
def _reset_logging():
    _ROOT_LOGGER.handlers.clear()

    _ROOT_LOGGER.setLevel(logging.NOTSET)

    with patch("calc_framework.logging._initialized", False):
        yield


class TestSetupLogging:
    def test_default_level(self):
        setup_logging()

        assert _ROOT_LOGGER.level == logging.WARNING

    def test_level_as_string(self):
        setup_logging(level="DEBUG")

        assert _ROOT_LOGGER.level == logging.DEBUG

    def test_level_as_int(self):
        setup_logging(level=logging.INFO)

        assert _ROOT_LOGGER.level == logging.INFO

    def test_level_as_lowercase_string(self):
        setup_logging(level="info")

        assert _ROOT_LOGGER.level == logging.INFO

    def test_console_handler_added(self):
        setup_logging(console=True)

        handler_types = [type(h) for h in _ROOT_LOGGER.handlers]

        assert logging.StreamHandler in handler_types

    def test_console_disabled(self):
        setup_logging(console=False)

        handler_types = [type(h) for h in _ROOT_LOGGER.handlers]

        assert logging.StreamHandler not in handler_types

    def test_file_handler(self):
        with tempfile.NamedTemporaryFile(suffix=".log", delete=False) as f:
            log_path = f.name

        try:
            setup_logging(log_file=log_path)

            from logging.handlers import RotatingFileHandler

            handlers = [h for h in _ROOT_LOGGER.handlers if isinstance(h, RotatingFileHandler)]

            assert len(handlers) == 1

            handlers[0].close()

            _ROOT_LOGGER.removeHandler(handlers[0])

            assert Path(log_path).exists()

        finally:
            Path(log_path).unlink(missing_ok=True)

    def test_file_handler_with_custom_rotation(self):
        with tempfile.NamedTemporaryFile(suffix=".log", delete=False) as f:
            log_path = f.name

        try:
            setup_logging(log_file=log_path, max_bytes=1024, backup_count=2)

            from logging.handlers import RotatingFileHandler

            handlers = [h for h in _ROOT_LOGGER.handlers if isinstance(h, RotatingFileHandler)]

            assert len(handlers) == 1

            assert handlers[0].maxBytes == 1024

            assert handlers[0].backupCount == 2

            handlers[0].close()

            _ROOT_LOGGER.removeHandler(handlers[0])

        finally:
            Path(log_path).unlink(missing_ok=True)

    def test_noop_on_second_call(self):
        setup_logging(level="DEBUG")

        setup_logging(level="ERROR")

        assert _ROOT_LOGGER.level == logging.DEBUG

    def test_env_var_level(self):
        with patch.dict(os.environ, {"CALC_FRAMEWORK_LOG_LEVEL": "ERROR"}, clear=False):
            setup_logging(level=None)

            assert _ROOT_LOGGER.level == logging.ERROR

    def test_invalid_level_string_falls_to_default(self):
        setup_logging(level="INVALID_LEVEL")

        assert _ROOT_LOGGER.level == logging.WARNING


class TestGetLogger:
    def test_returns_namespaced_logger(self):
        logger = get_logger("test.module")

        assert logger.name == "calc_framework.test.module"

    def test_returns_same_logger_for_same_name(self):
        a = get_logger("same.name")

        b = get_logger("same.name")

        assert a is b

    def test_different_names_different_loggers(self):
        a = get_logger("module.a")

        b = get_logger("module.b")

        assert a is not b


class TestSetLevel:
    def test_set_level_string(self):
        setup_logging()

        set_level("DEBUG")

        assert _ROOT_LOGGER.level == logging.DEBUG

    def test_set_level_int(self):
        setup_logging()

        set_level(logging.CRITICAL)

        assert _ROOT_LOGGER.level == logging.CRITICAL

    def test_set_level_lowercase(self):
        setup_logging()

        set_level("error")

        assert _ROOT_LOGGER.level == logging.ERROR


class TestResolveLevel:
    def test_int_passthrough(self):
        assert _resolve_level(logging.DEBUG) == logging.DEBUG

    def test_valid_string(self):
        assert _resolve_level("INFO") == logging.INFO

        assert _resolve_level("DEBUG") == logging.DEBUG

    def test_case_insensitive(self):
        assert _resolve_level("warning") == logging.WARNING

    def test_none_falls_to_env(self):
        with patch.dict(os.environ, {"CALC_FRAMEWORK_LOG_LEVEL": "CRITICAL"}, clear=False):
            assert _resolve_level(None) == logging.CRITICAL

    def test_none_no_env_falls_to_default(self):
        with patch.dict(os.environ, {}, clear=True):
            assert _resolve_level(None) == logging.WARNING

    def test_invalid_string_falls_to_env(self):
        with patch.dict(os.environ, {"CALC_FRAMEWORK_LOG_LEVEL": "INFO"}, clear=False):
            assert _resolve_level("BOGUS") == logging.INFO

    def test_invalid_string_no_env_falls_to_default(self):
        with patch.dict(os.environ, {}, clear=True):
            assert _resolve_level("BOGUS") == logging.WARNING
