# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""静态文件挂载：未知前端路由回退到 ``index.html``（SPA 深链接）。"""

from __future__ import annotations

from pathlib import PurePosixPath

from starlette.exceptions import HTTPException
from starlette.responses import Response
from starlette.staticfiles import StaticFiles
from starlette.types import Scope

__all__ = ["SPAStaticFiles"]


class SPAStaticFiles(StaticFiles):
    """静态文件服务；不存在的非 API 路径回退到 ``index.html``。

    ``StaticFiles(html=True)`` 只对目录请求返回 ``index.html``，直接访问
    ``/wjdlglr``、``/compute`` 等前端路由会 404。此子类在 404 时按 SPA
    规则回退，同时保留缺失静态资源（带扩展名）与未知 ``/api/`` 路径的 404。

    用法与 ``StaticFiles`` 相同，挂在根路径::

        app.mount("/", SPAStaticFiles(directory=dist, html=True))
    """

    async def get_response(self, path: str, scope: Scope) -> Response:
        try:
            return await super().get_response(path, scope)
        except HTTPException as exc:
            # Starlette 在 Windows 上把路径规整为 ``api\\unknown``，先统一分隔符。
            normalized = path.replace("\\", "/")
            if (
                exc.status_code == 404
                and scope.get("method") in {"GET", "HEAD"}
                and not normalized.startswith("api/")
                and "." not in PurePosixPath(normalized).name
            ):
                return await super().get_response("index.html", scope)
            raise
