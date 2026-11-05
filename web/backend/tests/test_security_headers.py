# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""安全响应头与 API 文档访问控制测试。"""

from __future__ import annotations

import sys
from pathlib import Path

from starlette.applications import Starlette
from starlette.responses import PlainTextResponse
from starlette.routing import Route
from starlette.testclient import TestClient

_REPO = Path(__file__).resolve().parents[3]
_BACKEND = _REPO / "web" / "backend"
for _p in (str(_REPO / "framework" / "src"), str(_REPO), str(_BACKEND)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from api.internal.security_headers import SecurityMiddleware

_DOCS_PATHS = ("/api/docs", "/api/docs/oauth2-redirect", "/api/redoc", "/openapi.json")


def _docs_response(request):
    return PlainTextResponse(f"<html>docs {request.url.path}</html>")


def _build_client() -> TestClient:
    app = Starlette(
        routes=[
            Route("/", lambda request: PlainTextResponse(f"ok {request.url.path}")),
            *[Route(path, _docs_response) for path in _DOCS_PATHS],
        ]
    )
    app.add_middleware(SecurityMiddleware)
    return TestClient(app)


def _clear_docs_env(monkeypatch) -> None:
    monkeypatch.delenv("CALC_ENABLE_API_DOCS", raising=False)
    monkeypatch.delenv("CALC_DEBUG", raising=False)


class TestSecurityHeaders:
    """所有响应都附加基础安全头。"""

    def test_headers_present(self, monkeypatch) -> None:
        _clear_docs_env(monkeypatch)
        response = _build_client().get("/")

        assert response.headers["x-content-type-options"] == "nosniff"
        assert response.headers["x-frame-options"] == "DENY"
        assert response.headers["referrer-policy"] == "strict-origin-when-cross-origin"
        assert response.headers["strict-transport-security"].startswith("max-age=")
        assert "camera=()" in response.headers["permissions-policy"]

    def test_csp_allows_wasm_but_not_eval(self, monkeypatch) -> None:
        _clear_docs_env(monkeypatch)
        csp = _build_client().get("/").headers["content-security-policy"]

        assert "default-src 'self'" in csp
        assert "script-src 'self' 'wasm-unsafe-eval'" in csp
        assert "'unsafe-eval'" not in csp
        assert "style-src 'self' 'unsafe-inline'" in csp
        assert "worker-src 'self'" in csp
        assert "frame-ancestors 'none'" in csp
        assert "object-src 'none'" in csp


class TestDocsAccess:
    """API 文档默认关闭，显式开关才开放。"""

    def test_docs_disabled_by_default(self, monkeypatch) -> None:
        _clear_docs_env(monkeypatch)
        client = _build_client()

        for path in _DOCS_PATHS:
            assert client.get(path).status_code == 404, path

        # 被拦截的响应同样带安全头
        blocked = client.get("/api/docs")
        assert blocked.headers["x-content-type-options"] == "nosniff"

    def test_docs_enabled_by_env(self, monkeypatch) -> None:
        monkeypatch.setenv("CALC_ENABLE_API_DOCS", "1")
        monkeypatch.delenv("CALC_DEBUG", raising=False)
        client = _build_client()

        assert client.get("/api/docs").status_code == 200
        assert client.get("/openapi.json").status_code == 200

    def test_calc_debug_also_enables_docs(self, monkeypatch) -> None:
        monkeypatch.delenv("CALC_ENABLE_API_DOCS", raising=False)
        monkeypatch.setenv("CALC_DEBUG", "1")

        assert _build_client().get("/api/docs").status_code == 200

    def test_csp_skipped_for_enabled_docs(self, monkeypatch) -> None:
        """Swagger UI 需从 CDN 加载脚本，开放文档时不附加 CSP。"""
        monkeypatch.setenv("CALC_ENABLE_API_DOCS", "1")

        response = _build_client().get("/api/docs")

        assert "content-security-policy" not in response.headers
        assert response.headers["x-content-type-options"] == "nosniff"


class TestRealAppWiring:
    """真实应用已注册中间件。"""

    def test_health_has_headers_and_docs_hidden(self, monkeypatch) -> None:
        _clear_docs_env(monkeypatch)

        from web.backend.main import app

        client = TestClient(app)
        health = client.get("/api/health")

        assert health.status_code == 200
        assert health.headers["x-content-type-options"] == "nosniff"
        assert client.get("/api/docs").status_code == 404
