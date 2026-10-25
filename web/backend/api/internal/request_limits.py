# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""入站请求体大小限制（ASGI 中间件）。"""

from __future__ import annotations

from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

# 默认 JSON/API 请求体上限（1 MiB）
DEFAULT_MAX_BODY_BYTES = 1024 * 1024

# 按路径前缀放宽（文件上传等）
PATH_MAX_BODY_BYTES: dict[str, int] = {
    "/api/ocr/": 5 * 1024 * 1024,
    "/api/hub/": 15 * 1024 * 1024,
}


class ContentSizeLimitError(Exception):
    """请求体超过允许上限。"""

    def __init__(self, limit: int, received: int) -> None:
        self.limit = limit
        self.received = received
        super().__init__(f"limit={limit}, received={received}")


class ContentSizeLimitMiddleware:
    """拦截 ``receive()``，累计 body 字节数并在超限时返回 413。

    说明：在 ASGI 层尽早拒绝，避免路由内 ``await request.body()`` 读完全部内容。
    生产环境仍可在 nginx 配置 ``client_max_body_size`` 作为第一道防线。
    """

    def __init__(
        self,
        app: ASGIApp,
        *,
        default_max_bytes: int | None = DEFAULT_MAX_BODY_BYTES,
        path_max_bytes: dict[str, int] | None = None,
    ) -> None:
        self.app = app
        self.default_max_bytes = default_max_bytes
        self.path_max_bytes = path_max_bytes if path_max_bytes is not None else dict(PATH_MAX_BODY_BYTES)

    def max_bytes_for_path(self, path: str) -> int | None:
        """返回路径对应的上限；``None`` 表示不限制。"""
        if self.default_max_bytes is None and not self.path_max_bytes:
            return None

        matched_limit: int | None = None
        matched_prefix_len = -1
        for prefix, limit in self.path_max_bytes.items():
            if path.startswith(prefix) and len(prefix) > matched_prefix_len:
                matched_limit = limit
                matched_prefix_len = len(prefix)

        if matched_limit is not None:
            return matched_limit
        return self.default_max_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = str(scope.get("path", ""))
        max_bytes = self.max_bytes_for_path(path)
        if max_bytes is None:
            await self.app(scope, receive, send)
            return

        received = 0

        async def limited_receive() -> Message:
            nonlocal received
            message = await receive()
            if message["type"] == "http.request":
                received += len(message.get("body", b""))
                if received > max_bytes:
                    raise ContentSizeLimitError(max_bytes, received)
            return message

        try:
            await self.app(scope, limited_receive, send)
        except ContentSizeLimitError as exc:
            response = JSONResponse(
                status_code=413,
                content={
                    "detail": (f"请求体过大（上限 {exc.limit} 字节，已读取 {exc.received} 字节）"),
                },
            )
            await response(scope, receive, send)


def parse_max_body_bytes_env(raw: str | None) -> int | None:
    """解析 ``CALC_MAX_BODY_BYTES`` 环境变量。

    空值 → 默认 1 MiB；``0`` / ``off`` / ``none`` → 不限制（仍保留路径特例）。
    """
    if raw is None or not str(raw).strip():
        return DEFAULT_MAX_BODY_BYTES

    text = str(raw).strip().lower()
    if text in {"0", "off", "none", "disabled", "false"}:
        return None

    return int(text)


__all__ = [
    "DEFAULT_MAX_BODY_BYTES",
    "PATH_MAX_BODY_BYTES",
    "ContentSizeLimitError",
    "ContentSizeLimitMiddleware",
    "parse_max_body_bytes_env",
]
