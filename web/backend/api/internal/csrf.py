# SPDX-License-Identifier: AGPL-3.0
"""CSRF 保护中间件 — 基于 Origin/Referer 校验 + SameSite Cookie 策略。

设计的核心思路：
- 非 GET/HEAD/OPTIONS 请求必须通过 Origin 或 Referer 校验
- 源站白名单允许的跨域来源（与 CORS 配置一致）
- GET/HEAD/OPTIONS 等安全方法无需校验
- 通过 ``CSRFSkipMiddleware`` 白名单路径可豁免
- 设置 ``CALC_DISABLE_CSRF=1`` 可禁用（仅用于测试环境）
"""

from __future__ import annotations

import os

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

# 允许的来源（与 main.py CORSMiddleware allow_origins 保持一致）
_ALLOWED_ORIGINS = frozenset(
    {
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    }
)

# 白名单路径前缀 — 这些路径跳过 CSRF 校验
_SAFE_PATH_PREFIXES = frozenset(
    {
        "/api/docs",
        "/api/redoc",
        "/api/admin",  # 已受 Token 认证保护
        "/api/download",  # 文件下载
        "/api/data",  # 已受 Admin Token 认证保护
    }
)


def _csrf_disabled() -> bool:
    """检查是否通过环境变量禁用了 CSRF 保护（仅用于测试）。"""
    return os.environ.get("CALC_DISABLE_CSRF", "").strip().lower() in ("1", "true", "yes", "on")


def _is_safe_method(method: str) -> bool:
    """安全方法（只读操作）无需 CSRF 校验。"""
    return method.upper() in {"GET", "HEAD", "OPTIONS"}


def _is_safe_path(path: str) -> bool:
    """检查路径是否在 CSRF 白名单中。"""
    return any(path.startswith(prefix) for prefix in _SAFE_PATH_PREFIXES)


def _validate_origin(request: Request) -> bool:
    """校验 Origin 或 Referer 头是否在允许来源中。"""
    origin = request.headers.get("origin", "").strip().rstrip("/")
    if origin:
        return origin in _ALLOWED_ORIGINS

    referer = request.headers.get("referer", "").strip().rstrip("/")
    if referer:
        for allowed in _ALLOWED_ORIGINS:
            if referer.startswith(allowed):
                return True

    return False


class CSRFSkipMiddleware(BaseHTTPMiddleware):
    """CSRF 保护中间件。

    对非安全方法（POST/PUT/DELETE 等）且非白名单路径：
    - 校验 Origin 或 Referer 是否在允许来源中
    - 校验失败返回 403

    环境变量 ``CALC_DISABLE_CSRF=1`` 可全局禁用（仅测试用）。
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if _csrf_disabled():
            return await call_next(request)

        method = request.method
        path = request.url.path

        if not _is_safe_method(method) and not _is_safe_path(path):
            if not _validate_origin(request):
                logger = None
                try:
                    from web.backend.bridge import get_logger

                    logger = get_logger(__name__)
                except ImportError:
                    import logging

                    logger = logging.getLogger(__name__)

                if logger:
                    logger.warning(
                        "CSRF 校验失败: method=%s path=%s origin=%s referer=%s",
                        method,
                        path,
                        request.headers.get("origin", ""),
                        request.headers.get("referer", ""),
                    )

                return JSONResponse(
                    status_code=403,
                    content={"detail": "CSRF 校验失败：请求来源不被允许"},
                )

        return await call_next(request)


__all__: list[str] = []
