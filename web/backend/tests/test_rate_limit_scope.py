# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""RateLimitMiddleware 作用域与匿名分桶测试。"""

from __future__ import annotations

import sys
from collections.abc import Iterator
from pathlib import Path

import pytest
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import PlainTextResponse
from starlette.routing import Route
from starlette.testclient import TestClient

_REPO = Path(__file__).resolve().parents[3]
_BACKEND = _REPO / "web" / "backend"
for _p in (str(_REPO / "framework" / "src"), str(_REPO), str(_BACKEND)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from api.admin import RateLimitMiddleware


async def _ok(request: Request) -> PlainTextResponse:
    return PlainTextResponse(request.url.path)


def _make_app() -> Starlette:
    app = Starlette(
        routes=[
            Route("/", _ok),
            Route("/assets/app.js", _ok),
            Route("/compute", _ok),
            Route("/api/ping", _ok),
        ]
    )
    app.add_middleware(RateLimitMiddleware)
    return app


@pytest.fixture(autouse=True)
def usage_records(monkeypatch: pytest.MonkeyPatch) -> Iterator[list[str]]:
    """清空滑动窗口、启用限速，并拦截 usage 落盘。"""
    previous_enabled = RateLimitMiddleware.enabled
    RateLimitMiddleware._window.clear()
    RateLimitMiddleware.enabled = True
    recorded: list[str] = []

    async def fake_record(path: str) -> None:
        recorded.append(path)

    monkeypatch.setattr(RateLimitMiddleware, "_record_usage_async", staticmethod(fake_record))
    yield recorded
    RateLimitMiddleware._window.clear()
    RateLimitMiddleware.enabled = previous_enabled


def test_static_and_spa_paths_are_not_rate_limited() -> None:
    """首屏静态资源与前端路由不占用匿名额度。"""
    client = TestClient(_make_app(), client=("1.1.1.1", 1000))
    for _ in range(30):
        assert client.get("/").status_code == 200
        assert client.get("/assets/app.js").status_code == 200
        assert client.get("/compute").status_code == 200


def test_anonymous_limit_is_per_client_ip() -> None:
    """匿名额度按客户端 IP 分桶，A 超限不影响 B。"""
    app = _make_app()
    client_a = TestClient(app, client=("1.1.1.1", 1000))
    client_b = TestClient(app, client=("2.2.2.2", 2000))

    for _ in range(20):
        assert client_a.get("/api/ping").status_code == 200

    assert client_a.get("/api/ping").status_code == 429
    assert client_b.get("/api/ping").status_code == 200


def test_same_client_ip_still_limited() -> None:
    """同一 IP 的第 21 次 API 请求仍返回 429。"""
    client = TestClient(_make_app(), client=("3.3.3.3", 3000))
    codes = [client.get("/api/ping").status_code for _ in range(21)]
    assert codes[:20] == [200] * 20
    assert codes[20] == 429


def test_static_paths_do_not_count_usage(usage_records: list[str]) -> None:
    """静态资源不写入 API usage 统计。"""
    client = TestClient(_make_app(), client=("4.4.4.4", 4000))
    client.get("/")
    client.get("/assets/app.js")
    client.get("/compute")
    assert usage_records == []

    assert client.get("/api/ping").status_code == 200
    assert usage_records == ["/api/ping"]
