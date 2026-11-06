# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""安全响应头与 API 文档访问控制。

生产环境默认关闭 Swagger / ReDoc / OpenAPI schema，减少公网可枚举面；
所有响应附加 CSP、nosniff、X-Frame-Options 等基础安全头。

CSP 说明：
- ``script-src`` 必须含 ``'wasm-unsafe-eval'``：``sql.js`` 与 ``wasm-curve``
  通过 ``WebAssembly.instantiate`` 加载，CSP3 下未声明会被浏览器拦截。
- ``style-src`` 必须含 ``'unsafe-inline'``：``index.html`` 有骨架屏内联样式，
  MUI 的 emotion 也会在运行时注入 ``<style>``。
- 开放 API 文档时不附加 CSP：Swagger UI 需要从 CDN 加载脚本。

环境变量 ``CALC_ENABLE_API_DOCS=1`` 或 ``CALC_DEBUG=1`` 可重新开放文档。
"""

from __future__ import annotations

import os

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

_TRUTHY = frozenset({"1", "true", "yes", "on"})

# 文档路径前缀（含 Swagger UI 的 OAuth2 回调）
_DOCS_PATH_PREFIXES = ("/api/docs", "/api/redoc")
_OPENAPI_PATH = "/openapi.json"

_CSP = (
    "default-src 'self'; "
    "script-src 'self' 'wasm-unsafe-eval'; "
    "style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data: blob:; "
    "font-src 'self' data:; "
    "connect-src 'self'; "
    "worker-src 'self' blob:; "
    "manifest-src 'self'; "
    "object-src 'none'; "
    "base-uri 'self'; "
    "form-action 'self'; "
    "frame-ancestors 'none'"
)

# HSTS 仅对 HTTPS 响应生效，HTTP 下浏览器会忽略
_SECURITY_HEADERS: dict[str, str] = {
    "Content-Security-Policy": _CSP,
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
    "Strict-Transport-Security": "max-age=31536000",
}


def api_docs_enabled() -> bool:
    """API 文档是否开放；默认关闭，需显式环境变量开启。"""
    return any(os.environ.get(key, "").strip().lower() in _TRUTHY for key in ("CALC_ENABLE_API_DOCS", "CALC_DEBUG"))


def _is_docs_path(path: str) -> bool:
    """路径是否属于 API 文档 / OpenAPI schema。"""
    if path == _OPENAPI_PATH:
        return True
    return any(path.startswith(prefix) for prefix in _DOCS_PATH_PREFIXES)


class SecurityMiddleware(BaseHTTPMiddleware):
    """关闭未开放的 API 文档，并为所有响应附加安全头。

    文档被拦截时仍返回带安全头的 404，避免暴露该端点是否存在。
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        path = request.url.path
        docs_path = _is_docs_path(path)

        if docs_path and not api_docs_enabled():
            response: Response = JSONResponse(status_code=404, content={"detail": "Not Found"})
        else:
            response = await call_next(request)

        for name, value in _SECURITY_HEADERS.items():
            if name == "Content-Security-Policy" and docs_path:
                continue
            response.headers.setdefault(name, value)

        return response


__all__ = ["SecurityMiddleware", "api_docs_enabled"]
