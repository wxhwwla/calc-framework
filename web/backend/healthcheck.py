# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""容器健康检查：状态目录可写 + ``/api/health`` 可响应。

Dockerfile 的 ``HEALTHCHECK`` 调用本脚本。仅检查进程存活不足以发现
数据卷只读、权限错误或磁盘写满等运维故障，因此逐个状态目录做一次
写入-删除探针。

环境变量：
    CALC_STATE_DIRS: 状态目录列表，使用 ``os.pathsep`` 分隔；
        默认 ``/app/web/backend/data/hub``、``/app/web/backend/.data``、
        ``/app/web/backend/api/data``。
    CALC_HEALTH_URL: 健康检查 URL，默认 ``http://127.0.0.1:8000/api/health``。
"""

from __future__ import annotations

import os
import sys
import urllib.request
from collections.abc import Iterable
from pathlib import Path

_DEFAULT_STATE_DIRS = (
    "/app/web/backend/data/hub",
    "/app/web/backend/.data",
    "/app/web/backend/api/data",
)
_DEFAULT_HEALTH_URL = "http://127.0.0.1:8000/api/health"


def check_state_dirs(dirs: Iterable[Path]) -> bool:
    """逐个验证状态目录可创建、可写入、可删除。

    Args:
        dirs: 需要验证的目录。

    Returns:
        全部目录可写返回 True，任意目录失败返回 False。
    """
    for directory in dirs:
        try:
            directory.mkdir(parents=True, exist_ok=True)
            probe = directory / ".healthcheck"
            probe.write_text("ok", encoding="utf-8")
            probe.unlink()
        except OSError as exc:
            print(f"状态目录不可写: {directory}: {exc}", file=sys.stderr)
            return False
    return True


def check_http(url: str, timeout: float = 3.0) -> bool:
    """请求健康检查端点并校验 HTTP 200。

    Args:
        url: 完整健康检查 URL。
        timeout: 请求超时（秒）。

    Returns:
        返回 200 时为 True，网络错误或非 200 时返回 False。
    """
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            if response.status != 200:
                print(f"健康检查端点返回 {response.status}: {url}", file=sys.stderr)
                return False
    except OSError as exc:
        print(f"健康检查端点不可用: {url}: {exc}", file=sys.stderr)
        return False
    return True


def _state_dirs_from_env() -> tuple[Path, ...]:
    raw = os.environ.get("CALC_STATE_DIRS", "").strip()
    if not raw:
        return tuple(Path(p) for p in _DEFAULT_STATE_DIRS)
    return tuple(Path(p) for p in raw.split(os.pathsep) if p)


def main() -> int:
    """运行全部健康检查。

    Returns:
        0 表示健康，1 表示任一检查失败。
    """
    dirs = _state_dirs_from_env()
    url = os.environ.get("CALC_HEALTH_URL", _DEFAULT_HEALTH_URL).strip() or _DEFAULT_HEALTH_URL
    if not check_state_dirs(dirs):
        return 1
    if not check_http(url):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
