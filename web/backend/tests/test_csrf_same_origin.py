# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""CSRFSkipMiddleware 同源、反代与 Referer 边界测试。"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.testclient import TestClient

_REPO = Path(__file__).resolve().parents[3]
_BACKEND = _REPO / "web" / "backend"
for _p in (str(_REPO / "framework" / "src"), str(_REPO), str(_BACKEND)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from api.internal.csrf import CSRFSkipMiddleware


async def _ok(request: Request) -> JSONResponse:
    return JSONResponse({"ok": True, "path": request.url.path})


def _make_app() -> Starlette:
    app = Starlette(routes=[Route("/api/x", _ok, methods=["POST"])])
    app.add_middleware(CSRFSkipMiddleware)
    return app


@pytest.fixture(autouse=True)
def enable_csrf(monkeypatch: pytest.MonkeyPatch) -> None:
    """conftest 默认设置 CALC_DISABLE_CSRF=1，这里恢复校验。"""
    monkeypatch.delenv("CALC_DISABLE_CSRF", raising=False)


def test_same_origin_post_allowed() -> None:
    """Origin 与请求 Host 一致时放行（自托管同源）。"""
    client = TestClient(_make_app(), base_url="http://testserver")
    response = client.post("/api/x", headers={"origin": "http://testserver"})
    assert response.status_code == 200


def test_tunnel_same_origin_post_allowed() -> None:
    """经 ngrok/反代以公网域名同源访问时放行。"""
    base = "https://dove-magnitude-runner.ngrok-free.dev"
    client = TestClient(_make_app(), base_url=base)
    response = client.post("/api/x", headers={"origin": base})
    assert response.status_code == 200


def test_cross_origin_post_rejected() -> None:
    """第三方 Origin 仍返回 403。"""
    client = TestClient(_make_app(), base_url="http://testserver")
    response = client.post("/api/x", headers={"origin": "https://evil.example"})
    assert response.status_code == 403


def test_vite_dev_origin_still_allowed() -> None:
    """Vite 开发服务器的跨源白名单保持不变。"""
    client = TestClient(_make_app(), base_url="http://testserver")
    response = client.post("/api/x", headers={"origin": "http://localhost:5173"})
    assert response.status_code == 200


def test_referer_same_origin_allowed() -> None:
    """无 Origin 时，同源 Referer 放行。"""
    client = TestClient(_make_app(), base_url="http://testserver")
    response = client.post("/api/x", headers={"referer": "http://testserver/compute"})
    assert response.status_code == 200


def test_referer_prefix_lookalike_rejected() -> None:
    """Referer 前缀必须到 / 边界，5173.evil.example 不得误放行。"""
    client = TestClient(_make_app(), base_url="http://testserver")
    response = client.post("/api/x", headers={"referer": "http://localhost:5173.evil.example/x"})
    assert response.status_code == 403
