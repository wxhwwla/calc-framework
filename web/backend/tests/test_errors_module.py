# SPDX-License-Identifier: AGPL-3.0
"""_errors 模块单元测试。"""

from __future__ import annotations

import os
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
_BACKEND = _REPO / "web" / "backend"
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from api._errors import CALC_DEBUG_ENV, calc_debug_enabled, safe_http_detail


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
