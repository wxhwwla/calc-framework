# SPDX-License-Identifier: AGPL-3.0
"""_errors 模块单元测试。"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
from fastapi import HTTPException

_REPO = Path(__file__).resolve().parents[3]
_BACKEND = _REPO / "web" / "backend"
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from api.internal.errors import (
    CALC_DEBUG_ENV,
    calc_debug_enabled,
    http_exception_from_exc,
    raise_http_from_exc,
    safe_http_detail,
)


def test_safe_http_detail_production() -> None:
    os.environ.pop(CALC_DEBUG_ENV, None)
    exc = RuntimeError("E:\\repo\\games\\endfield\\module.py:99 boom")
    assert safe_http_detail(exc, status_code=500) == "服务器内部错误"
    assert "module.py" not in safe_http_detail(exc, status_code=500)


def test_safe_http_detail_debug() -> None:
    os.environ[CALC_DEBUG_ENV] = "1"
    try:
        exc = RuntimeError("debug detail")
        assert safe_http_detail(exc, status_code=500) == "debug detail"
    finally:
        os.environ.pop(CALC_DEBUG_ENV, None)


def test_calc_debug_enabled_truthy_values() -> None:
    for val in ("1", "true", "yes", "on"):
        os.environ[CALC_DEBUG_ENV] = val
        assert calc_debug_enabled() is True
    os.environ[CALC_DEBUG_ENV] = "0"
    assert calc_debug_enabled() is False
    os.environ.pop(CALC_DEBUG_ENV, None)


def test_safe_http_detail_404_default() -> None:
    os.environ.pop(CALC_DEBUG_ENV, None)
    assert safe_http_detail(ValueError("x"), status_code=404) == "未找到所需资源"


def test_http_exception_from_exc_production_500() -> None:
    os.environ.pop(CALC_DEBUG_ENV, None)
    exc = http_exception_from_exc(RuntimeError("internal"), status_code=500)
    assert exc.status_code == 500
    assert exc.detail == "服务器内部错误"


def test_raise_http_from_exc_wraps_cause() -> None:
    os.environ.pop(CALC_DEBUG_ENV, None)
    with pytest.raises(HTTPException) as exc_info:
        raise_http_from_exc(ValueError("bad input"), status_code=400)
    assert exc_info.value.status_code == 400
    assert exc_info.value.__cause__ is not None
