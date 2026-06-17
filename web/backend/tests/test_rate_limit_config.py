# SPDX-License-Identifier: AGPL-3.0
"""RateLimitMiddleware 环境变量配置测试。"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[3]
_BACKEND = _REPO / "web" / "backend"
for _p in (str(_REPO / "framework" / "src"), str(_REPO), str(_BACKEND)):
    if _p not in sys.path:
        sys.path.insert(0, _p)


@pytest.fixture()
def fresh_main(monkeypatch: pytest.MonkeyPatch):
    """重新加载 main 以应用环境变量（测试隔离）。"""
    for key in ("CALC_DISABLE_RATE_LIMIT", "WEB_CONCURRENCY", "UVICORN_WORKERS", "CALC_WEB_WORKERS"):
        monkeypatch.delenv(key, raising=False)
    import web.backend.main as main_mod

    importlib.reload(main_mod)
    yield main_mod
    main_mod.RateLimitMiddleware.enabled = True
    monkeypatch.delenv("CALC_DISABLE_RATE_LIMIT", raising=False)


def test_calc_disable_rate_limit_env(fresh_main, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CALC_DISABLE_RATE_LIMIT", "1")
    importlib.reload(fresh_main)
    assert fresh_main.RateLimitMiddleware.enabled is False


def test_default_rate_limit_enabled(fresh_main) -> None:
    assert fresh_main.RateLimitMiddleware.enabled is True
