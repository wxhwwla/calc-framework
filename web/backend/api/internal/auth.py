# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""Web 后端管理 Token 认证 — 含暴力破解防护。"""

from __future__ import annotations

import logging
import os
import secrets
import threading
import time
from collections import defaultdict

from fastapi import Header, HTTPException, Request

logger = logging.getLogger(__name__)

ADMIN_TOKEN_ENV = "CALC_ADMIN_TOKEN"
ADMIN_TOKEN_HEADER = "X-Admin-Token"

# ── 暴力破解防护 ──────────────────────────────────────

_MAX_FAILED_ATTEMPTS = 5
"""每分钟允许的最大失败尝试次数。"""

_BAN_WINDOW = 60
"""窗口大小（秒）。"""

_lockout: dict[str, list[float]] = defaultdict(list)
_lockout_lock = threading.Lock()
"""IP → 失败时间戳列表（进程内存，仅单 worker 有效）。"""


def _get_client_ip(request: Request) -> str:
    """从请求中提取客户端 IP（优先 X-Forwarded-For）。"""
    forwarded = request.headers.get("X-Forwarded-For", "").strip()
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _check_rate_limit(request: Request) -> None:
    """检查客户端 IP 的失败速率限制。

    在单 worker 进程中生效；多 worker 场景需借助 Redis 等外部存储。
    """
    client_ip = _get_client_ip(request)
    now = time.time()
    window = _lockout[client_ip]
    # 清理过期记录
    window[:] = [t for t in window if now - t < _BAN_WINDOW]

    if len(window) >= _MAX_FAILED_ATTEMPTS:
        retry_after = int(_BAN_WINDOW - (now - window[0])) if window else _BAN_WINDOW
        logger.warning("IP %s 被临时锁定（%s 次失败尝试）", client_ip, len(window))
        raise HTTPException(
            status_code=429,
            detail=f"认证尝试过于频繁，请 {max(retry_after, 1)} 秒后重试",
            headers={"Retry-After": str(max(retry_after, 1))},
        )


def _record_failure(request: Request) -> None:
    """记录一次失败的认证尝试。"""
    client_ip = _get_client_ip(request)
    _lockout[client_ip].append(time.time())


def _clear_rate_limit(request: Request) -> None:
    """认证成功后清除失败记录。"""
    client_ip = _get_client_ip(request)
    _lockout.pop(client_ip, None)


# ── Token 认证 ────────────────────────────────────────


def _configured_admin_token() -> str:
    """读取环境变量中的管理 Token（未配置时返回空串）。"""
    return os.environ.get(ADMIN_TOKEN_ENV, "").strip()


async def verify_admin_token(
    request: Request,
    x_admin_token: str | None = Header(default=None, alias=ADMIN_TOKEN_HEADER),
) -> None:
    """校验管理 Token，保护 admin 与数据写接口。

    包含暴力破解防护：
    - 同一 IP 每分钟最多 5 次失败尝试
    - 超限后返回 429，锁定 1 分钟
    - 认证成功后清除该 IP 失败记录

    - 未配置 ``CALC_ADMIN_TOKEN`` → 503（服务未就绪）
    - 缺少或错误 Token → 401
    """
    configured = _configured_admin_token()
    if not configured:
        logger.warning("%s 未配置，管理写操作已拒绝", ADMIN_TOKEN_ENV)
        raise HTTPException(status_code=503, detail="管理接口未配置，请联系管理员")

    # 在检查失败前做限速检查
    _check_rate_limit(request)

    if not x_admin_token:
        _record_failure(request)
        raise HTTPException(status_code=401, detail="缺少管理 Token")

    if not secrets.compare_digest(x_admin_token.strip(), configured):
        _record_failure(request)
        raise HTTPException(status_code=401, detail="管理 Token 无效")

    # 认证成功，清除该 IP 失败记录
    _clear_rate_limit(request)


__all__ = [
    "ADMIN_TOKEN_ENV",
    "ADMIN_TOKEN_HEADER",
    "verify_admin_token",
]
