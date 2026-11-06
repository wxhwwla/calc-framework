# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""``python -m tools.calc_mcp`` 入口。"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from .safety import ScopeError


def _bootstrap_framework(project_dir: Path) -> None:
    """把 ``<project>/framework/src`` 加入 sys.path，方便未安装框架的克隆仓库运行。"""
    src = (project_dir / "framework" / "src").resolve()
    if src.is_dir() and str(src) not in sys.path:
        sys.path.insert(0, str(src))


def main(argv: list[str] | None = None) -> int:
    """解析参数并启动 stdio 服务器。

    Args:
        argv: 可选的参数列表，默认读取 ``sys.argv``。

    Returns:
        进程退出码。
    """
    parser = argparse.ArgumentParser(prog="python -m tools.calc_mcp", description="Calc Framework MCP 构建服务器")
    parser.add_argument("--project-dir", default=".", help="项目根目录（所有文件操作限制在此目录内）")
    parser.add_argument("--adapters-dir", default=None, help="适配器目录（默认 <project>/framework/adapters）")
    parser.add_argument("--log-level", default="INFO", help="日志级别（输出到 stderr）")
    args = parser.parse_args(argv)

    logging.basicConfig(
        stream=sys.stderr,
        level=getattr(logging, str(args.log_level).upper(), logging.INFO),
        format="[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
    )

    project_dir = Path(args.project_dir).resolve()
    _bootstrap_framework(project_dir)

    from .server import build_server

    try:
        server = build_server(project_dir, args.adapters_dir)
    except ScopeError as exc:
        logging.getLogger(__name__).error("初始化失败: %s", exc)
        return 2

    server.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
