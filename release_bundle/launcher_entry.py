#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""统一启动器 exe 入口（ADR-0012 Phase 2）。

单 exe 路由入口，支持命令行参数选择运行模式：

    无参数              → 启动器 GUI
    --game endfield     → 终末地伤害计算器
    --game arknights    → 明日方舟伤害计算器
    --tool dev_toolkit  → 开发者工具箱
    --tool viewer       → 计算包查看器
    --server            → 本地 Web 搜索服务器
    --calcpack <path>   → 打开 .calcpack 文件
    --version            → 打印版本号

所有子命令共享同一 exe，实现「单 exe + 子命令」架构。
"""

from __future__ import annotations

import argparse
import os
import sys
import webbrowser
from pathlib import Path


def _setup_paths() -> None:
    """确保 exe 能导入所有包（开发模式 + PyInstaller 冻结模式）。"""
    root = Path(__file__).resolve().parent.parent

    if getattr(sys, "frozen", False):
        # PyInstaller 冻结模式：sys._MEIPASS 是解压目录
        meipass = Path(sys._MEIPASS)  # type: ignore[attr-defined]
        for p in [
            meipass,
            meipass / "framework" / "src",
            meipass / "games",
            meipass / "tools",
            meipass / "scripts",
            meipass / "web" / "backend",
        ]:
            if str(p) not in sys.path:
                sys.path.insert(0, str(p))
    else:
        # 开发模式
        for p in [
            root,
            root / "framework" / "src",
            root / "games",
            root / "tools",
            root / "scripts",
            root / "games" / "endfield",
            root / "web" / "backend",
        ]:
            if str(p) not in sys.path:
                sys.path.insert(0, str(p))


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="Game Calc Platform",
        description="游戏计算器平台 — 多游戏伤害计算框架",
    )
    parser.add_argument("--game", choices=["endfield", "arknights"], help="直接启动指定游戏计算器")
    parser.add_argument(
        "--tool", choices=["dev_toolkit", "viewer", "graph_editor", "layout_editor"], help="直接启动指定开发工具"
    )
    parser.add_argument("--server", action="store_true", help="启动本地 Web 搜索服务器")
    parser.add_argument("--calcpack", type=str, help="打开 .calcpack 文件")
    parser.add_argument("--version", action="store_true", help="显示版本号")
    return parser


def _launch_game(game: str) -> None:
    """在独立进程中启动游戏计算器。"""
    if game == "endfield":
        from games.endfield.main import main as endfield_main

        endfield_main()
    elif game == "arknights":
        from games.arknights.main import main as arknights_main

        arknights_main()


def _launch_tool(tool: str) -> None:
    """启动开发工具。"""
    if tool == "dev_toolkit":
        from calc_framework.dev_toolkit import main as toolkit_main

        toolkit_main()
    elif tool == "viewer":
        from calc_framework.ui.viewer import main as viewer_main

        viewer_main()
    elif tool == "graph_editor":
        from calc_framework.graph_editor.__main__ import main as graph_main

        graph_main()
    elif tool == "layout_editor":
        from calc_framework.editor.__main__ import main as editor_main

        editor_main()


def _launch_calcpack(path: str) -> None:
    """打开 .calcpack 文件。"""
    from calc_framework.ui.viewer import main as viewer_main

    sys.argv = [sys.argv[0], path]
    viewer_main()


def _show_version() -> None:
    """打印版本号并退出。"""
    try:
        from scripts.please_read_me import get_exe_version, get_version

        print(f"Game Calc Platform v{get_exe_version()}")
        print(f"Source version: {get_version()}")
    except ImportError:
        print("Game Calc Platform (version unknown)")
    sys.exit(0)


def _launch_server() -> None:
    """启动本地 Web 搜索服务器（uvicorn）。"""
    import uvicorn

    from web.backend.main import app

    port = int(os.getenv("PORT", "8180"))
    host = os.getenv("HOST", "127.0.0.1")
    print(f"\n  >>> 本地服务器已启动: http://{host}:{port} <<<")
    print("  关闭此窗口即可停止服务器\n")
    webbrowser.open(f"http://{host}:{port}")
    uvicorn.run(app, host=host, port=port, log_level="info")


def main() -> None:
    """统一入口：根据命令行参数路由到对应功能。"""
    try:
        # 路径设置优先
        _setup_paths()

        # 应用 Windows 兼容补丁
        try:
            from utils.platform_win32_patch import apply_platform_win32_patch

            apply_platform_win32_patch()
        except ImportError:
            pass

        parser = _build_parser()
        # 仅解析已知参数，其余透传
        args, unknown = parser.parse_known_args()

        if args.version:
            _show_version()
        elif args.server:
            _launch_server()
        elif args.game:
            if args.game == "endfield":
                from games.endfield.main import main as _game_main
            elif args.game == "arknights":
                from games.arknights.main import main as _game_main
            _game_main()
        elif args.tool:
            _launch_tool(args.tool)
        elif args.calcpack:
            _launch_calcpack(args.calcpack)
        else:
            # 默认：启动器 GUI
            from calc_framework.ui.launcher import run_gui_launcher

            run_gui_launcher()
    except Exception as exc:
        import traceback

        error_msg = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
        # 尝试写入崩溃日志到 exe 同级目录
        crash_log = Path(sys.executable).parent / "crash.log" if getattr(sys, "frozen", False) else Path("crash.log")
        try:
            crash_log.write_text(error_msg, encoding="utf-8")
        except Exception:
            pass
        print(f"\n!!! 启动失败: {exc}\n详情已写入: {crash_log}\n", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
