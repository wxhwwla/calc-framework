# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""请求体大小限制中间件测试。"""

from __future__ import annotations

import sys
from pathlib import Path

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

from api.internal.request_limits import (  # noqa: I001
    ContentSizeLimitMiddleware,
    DEFAULT_MAX_BODY_BYTES,
    parse_max_body_bytes_env,
)


async def _echo_size(request: Request) -> PlainTextResponse:
    body = await request.body()
    return PlainTextResponse(str(len(body)))


def _build_app(*, default_max_bytes: int | None = 100) -> Starlette:
    app = Starlette(routes=[Route("/api/data/x", _echo_size, methods=["POST"])])
    app.add_middleware(ContentSizeLimitMiddleware, default_max_bytes=default_max_bytes)
    return app


class TestParseMaxBodyBytesEnv:
    def test_empty_uses_default(self) -> None:
        assert parse_max_body_bytes_env(None) == DEFAULT_MAX_BODY_BYTES
        assert parse_max_body_bytes_env("") == DEFAULT_MAX_BODY_BYTES

    def test_zero_disables_default(self) -> None:
        assert parse_max_body_bytes_env("0") is None
        assert parse_max_body_bytes_env("off") is None

    def test_custom_integer(self) -> None:
        assert parse_max_body_bytes_env("2048") == 2048


class TestContentSizeLimitMiddleware:
    def test_allows_body_under_limit(self) -> None:
        client = TestClient(_build_app(default_max_bytes=100))
        resp = client.post("/api/data/x", content=b"a" * 50)
        assert resp.status_code == 200
        assert resp.text == "50"

    def test_rejects_body_over_limit(self) -> None:
        client = TestClient(_build_app(default_max_bytes=100))
        resp = client.post("/api/data/x", content=b"b" * 150)
        assert resp.status_code == 413
        assert "请求体过大" in resp.json()["detail"]

    def test_path_prefix_uses_higher_limit(self) -> None:
        app = Starlette(
            routes=[
                Route("/api/ocr/detect", _echo_size, methods=["POST"]),
            ]
        )
        app.add_middleware(ContentSizeLimitMiddleware, default_max_bytes=100)
        client = TestClient(app)
        resp = client.post("/api/ocr/detect", content=b"c" * 200)
        assert resp.status_code == 200

    def test_max_bytes_for_path(self) -> None:
        app = _build_app(default_max_bytes=1000)
        mw = ContentSizeLimitMiddleware(app, default_max_bytes=1000)
        assert mw.max_bytes_for_path("/api/data/x") == 1000
        assert mw.max_bytes_for_path("/api/ocr/detect") == 5 * 1024 * 1024

    def test_no_limit_when_default_and_paths_empty(self) -> None:
        mw = ContentSizeLimitMiddleware(_build_app(), default_max_bytes=None, path_max_bytes={})
        assert mw.max_bytes_for_path("/api/data/x") is None


class TestNonHttpScope:
    def test_non_http_scope_passes_through(self) -> None:
        seen: list[str] = []

        async def websocket_app(scope, receive, send):
            seen.append(scope["type"])

        mw = ContentSizeLimitMiddleware(websocket_app, default_max_bytes=10)

        async def _run() -> None:
            await mw(
                {"type": "websocket", "path": "/"},
                lambda: None,  # type: ignore[arg-type]
                lambda message: None,  # type: ignore[arg-type]
            )

        import asyncio

        asyncio.run(_run())
        assert seen == ["websocket"]
