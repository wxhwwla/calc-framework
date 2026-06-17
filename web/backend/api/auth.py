# SPDX-License-Identifier: AGPL-3.0
"""Web 后端管理 Token 认证。"""

from __future__ import annotations

import logging
import os
import secrets

from fastapi import Header, HTTPException

logger = logging.getLogger(__name__)

ADMIN_TOKEN_ENV = "CALC_ADMIN_TOKEN"
ADMIN_TOKEN_HEADER = "X-Admin-Token"


def _configured_admin_token() -> str:
    """读取环境变量中的管理 Token（未配置时返回空串）。"""
    return os.environ.get(ADMIN_TOKEN_ENV, "").strip()


def verify_admin_token(
    x_admin_token: str | None = Header(default=None, alias=ADMIN_TOKEN_HEADER),
) -> None:
    """校验管理 Token，保护 admin 与数据写接口。

    - 未配置 ``CALC_ADMIN_TOKEN`` → 503（服务未就绪）
    - 缺少或错误 Token → 401
    """
    configured = _configured_admin_token()
    if not configured:
        logger.warning("%s 未配置，管理写操作已拒绝", ADMIN_TOKEN_ENV)
        raise HTTPException(status_code=503, detail="管理接口未配置，请联系管理员")

    if not x_admin_token:
        raise HTTPException(status_code=401, detail="缺少管理 Token")

    if not secrets.compare_digest(x_admin_token.strip(), configured):
        raise HTTPException(status_code=401, detail="管理 Token 无效")


__all__ = [
    "ADMIN_TOKEN_ENV",
    "ADMIN_TOKEN_HEADER",
    "verify_admin_token",
]
