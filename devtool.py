#!/usr/bin/env python3
"""
终末地计算器 — 开发者工具箱

整合日常开发维护所需的 CLI 工具，统一入口避免根目录散落文件。

用法::

    python devtool.py check-deps              # 依赖自检
    python devtool.py check-layout            # 代码布局门禁
    python devtool.py sync-bwiki              # BWIKI 数据同步（预览）
    python devtool.py sync-bwiki --apply      # BWIKI 数据同步（写入）
    python devtool.py launcher                # 框架游戏选择器（交互）
    python devtool.py launcher endfield       # 框架游戏选择器（直接启动）
"""

from __future__ import annotations

import sys
import argparse
from pathlib import Path


def _add_path() -> None:
    _REPO = Path(__file__).resolve().parent
    if str(_REPO) not in sys.path:
        sys.path.insert(0, str(_REPO))


def _sub_args() -> list[str]:
    """返回子命令后的剩余参数（绕过 argparse 对 --flags 的拦截）。"""
    cmd = sys.argv[0]
    rest = sys.argv[1:]
    # 找到子命令位置
    for i, a in enumerate(rest):
        if not a.startswith("-"):
            return rest[i + 1:]
    return []


def _cmd_check_deps(args: argparse.Namespace) -> int:
    _add_path()
    from tools.check_optional_deps import main
    return main()


def _cmd_check_layout(args: argparse.Namespace) -> int:
    _add_path()
    from tools.check_layout import main
    sys.argv = [sys.argv[0]] + _sub_args()
    return main()


def _cmd_sync_bwiki(args: argparse.Namespace) -> int:
    _add_path()
    from tools.bwiki_scout.sync_all import main
    sys.argv = [sys.argv[0]] + _sub_args()
    return main()


def _cmd_launcher(args: argparse.Namespace) -> None:
    _FRAMEWORK_SRC = Path(__file__).resolve().parent / "framework" / "src"
    if str(_FRAMEWORK_SRC) not in sys.path:
        sys.path.insert(0, str(_FRAMEWORK_SRC))

    from calc_framework.launcher import run_launcher
    passthrough = _sub_args()
    adapter = passthrough[0] if passthrough else None
    run_launcher(adapter)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="终末地计算器 — 开发者工具箱",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    sub = parser.add_subparsers(dest="command", help="可用子命令")

    sub.add_parser("check-deps", help="依赖自检", add_help=False)
    sub.add_parser("check-layout", help="代码布局门禁", add_help=False)
    sub.add_parser("sync-bwiki", help="BWIKI 数据同步", add_help=False)
    sub.add_parser("launcher", help="框架游戏选择器", add_help=False)

    # 用 parse_known_args 避免 --flags 被 argparse 拦截
    args, _ = parser.parse_known_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    funcs = {
        "check-deps": _cmd_check_deps,
        "check-layout": _cmd_check_layout,
        "sync-bwiki": _cmd_sync_bwiki,
        "launcher": _cmd_launcher,
    }
    result = funcs[args.command](args)
    if isinstance(result, int):
        sys.exit(result)


if __name__ == "__main__":
    main()
