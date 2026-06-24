# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""Web API 异常响应安全封装 — 避免生产环境泄露内部路径与堆栈。"""

from __future__ import annotations

import os
from typing import NoReturn

from fastapi import HTTPException

from web.backend.bridge import get_logger

logger = get_logger(__name__)

CALC_DEBUG_ENV = "CALC_DEBUG"

# 生产模式默认文案（按 HTTP 状态）
_DEFAULT_PUBLIC_MESSAGES: dict[int, str] = {
    400: "请求参数或计算数据无效",
    404: "未找到所需资源",
    500: "服务器内部错误",
}


def calc_debug_enabled() -> bool:
    """是否开启调试模式（``CALC_DEBUG=1/true/yes/on``）。"""
    return os.environ.get(CALC_DEBUG_ENV, "").strip().lower() in ("1", "true", "yes", "on")


def safe_http_detail(
    exc: BaseException,
    *,
    status_code: int,
    public_message: str | None = None,
    debug: bool | None = None,
) -> str:
    """生成 HTTP 响应 detail：调试模式返回 ``str(exc)``，否则返回固定文案。"""
    if debug is None:
        debug = calc_debug_enabled()
    if debug:
        return str(exc)
    return public_message or _DEFAULT_PUBLIC_MESSAGES.get(status_code, "请求处理失败")


def http_exception_from_exc(
    exc: BaseException,
    *,
    status_code: int,
    public_message: str | None = None,
) -> HTTPException:
    """记录异常并构造 ``HTTPException``（生产环境不泄露内部信息）。"""
    if calc_debug_enabled():
        logger.warning("HTTP %s: %s", status_code, exc, exc_info=exc)
    elif status_code >= 500:
        logger.error("HTTP %s: %s", status_code, exc, exc_info=exc)
    else:
        logger.warning("HTTP %s: %s", status_code, exc)
    return HTTPException(
        status_code=status_code,
        detail=safe_http_detail(exc, status_code=status_code, public_message=public_message),
    )


def raise_http_from_exc(
    exc: BaseException,
    *,
    status_code: int,
    public_message: str | None = None,
) -> NoReturn:
    """``raise http_exception_from_exc(...)`` 的便捷包装。"""
    raise http_exception_from_exc(exc, status_code=status_code, public_message=public_message) from exc


__all__ = [
    "CALC_DEBUG_ENV",
    "calc_debug_enabled",
    "http_exception_from_exc",
    "raise_http_from_exc",
    "safe_http_detail",
]
