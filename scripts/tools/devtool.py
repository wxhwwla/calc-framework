#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""
终末地计算器 — 开发者工具箱 CLI

整合日常开发维护所需的 CLI 工具，统一入口避免根目录散落文件。

用法::

    python scripts/tools/devtool.py check-deps              # 依赖自检
    python scripts/tools/devtool.py check-layout            # 代码布局门禁
    python scripts/tools/devtool.py sync-bwiki              # BWIKI 数据同步（预览）
    python scripts/tools/devtool.py sync-bwiki --apply      # BWIKI 数据同步（写入）
    python scripts/tools/devtool.py launcher                # 框架游戏选择器（交互）
    python scripts/tools/devtool.py launcher endfield       # 框架游戏选择器（直接启动）
    python scripts/tools/devtool.py hub                     # 启动 Calc Hub 社区市场
    python scripts/tools/devtool.py plugin build <dir>      # 打包插件为 .calcplugin
    python scripts/tools/devtool.py plugin install <file>   # 安装 .calcplugin
    python scripts/tools/devtool.py plugin rebuild-catalog  # 重建插件目录 JSON
    python scripts/tools/devtool.py framework build         # 构建 framework PyPI wheel
    python scripts/tools/devtool.py framework publish       # 构建+发布 framework 到 PyPI
    python scripts/tools/devtool.py check-origin            # AI 代码来源/版权检测
    python scripts/tools/devtool.py installer build         # 构建 NSIS 安装包
    python scripts/tools/devtool.py installer check         # 检查安装包构建环境
    python scripts/tools/devtool.py hub start               # 启动 Calc Hub 在线市场服务
    python scripts/tools/devtool.py hub status              # 查看 Hub 市场状态
    python scripts/tools/devtool.py scaffold <game>         # 新游戏适配脚手架（从模板生成）
    python scripts/tools/devtool.py scaffold <game> --force # 覆盖已存在的游戏目录
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _path_setup import ensure_root

ensure_root()


def _add_path() -> None:
    """将项目根目录加入 sys.path。"""
    repo_root = Path(__file__).resolve().parent.parent.parent
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))


def _sub_args() -> list[str]:
    """提取子命令的剩余参数（去除已解析的 flags）。"""
    rest = sys.argv[1:]
    for i, a in enumerate(rest):
        if not a.startswith("-"):
            return rest[i + 1 :]
    return []


def _cmd_check_deps(args: argparse.Namespace) -> int:
    """执行依赖自检。"""
    _add_path()
    from tools.quality.check_optional_deps import main

    return main()


def _cmd_check_layout(args: argparse.Namespace) -> int:
    """执行代码布局门禁检查。"""
    _add_path()
    from tools.quality.check_layout import main

    sys.argv = [sys.argv[0], *_sub_args()]
    return main()


def _cmd_sync_bwiki(args: argparse.Namespace) -> int:
    """同步 BWIKI 数据。"""
    _add_path()
    from tools.bwiki_scout.sync_all import main

    sys.argv = [sys.argv[0], *_sub_args()]
    return main()


def _cmd_launcher(args: argparse.Namespace) -> None:
    """启动框架游戏选择器。"""
    framework_src = Path(__file__).resolve().parent.parent.parent / "framework" / "src"
    if str(framework_src) not in sys.path:
        sys.path.insert(0, str(framework_src))
    from calc_framework.launcher import run_launcher

    passthrough = _sub_args()
    adapter = passthrough[0] if passthrough else None
    run_launcher(adapter)


def _cmd_framework(args: argparse.Namespace) -> int:
    """构建或发布 framework PyPI 包。"""
    from tools.publish.framework_publish import main as fw_main

    passthrough = _sub_args()
    sys.argv = [sys.argv[0], *passthrough] if passthrough else [sys.argv[0], "--help"]
    result = fw_main()
    return result if result is not None else 0


def _cmd_plugin(args: argparse.Namespace) -> int:
    """插件打包、安装或目录重建。"""
    passthrough = _sub_args()
    if not passthrough:
        print("用法: python devtool.py plugin <build|install|rebuild-catalog> [...]")
        return 1
    cmd = passthrough[0]
    rest = passthrough[1:]
    if cmd == "build":
        from tools.publish.plugin_pack import _demo_build

        return _demo_build(rest)
    if cmd == "install":
        from tools.publish.plugin_pack import _demo_install

        return _demo_install(rest)
    if cmd == "rebuild-catalog":
        from web.hub.build_plugin_catalog import build_plugin_catalog

        repo = Path(__file__).resolve().parent.parent.parent
        output = repo / "web" / "hub" / "plugins_catalog.json"
        build_plugin_catalog(output)
        return 0
    print(f"未知的子命令: {cmd}", file=sys.stderr)
    print("可用子命令: build, install, rebuild-catalog")
    return 1


def _cmd_check_origin(args: argparse.Namespace) -> int:
    """执行 AI 代码来源与版权检测。"""
    _add_path()
    from tools.check_code_origin import main

    sys.argv = [sys.argv[0], *_sub_args()]
    main()
    return 0


def _cmd_installer(args: argparse.Namespace) -> int:
    """构建或检查 NSIS 安装包。"""
    passthrough = _sub_args()
    if not passthrough:
        print("用法: python devtool.py installer <build|check> [...]")
        return 1
    rest = passthrough[1:]
    sys.argv = [sys.argv[0], *rest]
    from installer.build_installer import main as installer_main

    return installer_main() if installer_main is not None else 0


def _cmd_scaffold(args: argparse.Namespace) -> int:
    """从模板生成新游戏适配脚手架。"""
    _add_path()
    from tools.scaffold import main

    argv = _sub_args()
    return main(argv)


def _cmd_hub(args: argparse.Namespace) -> int:
    """启动或查询 Calc Hub 市场服务。"""
    passthrough = _sub_args()
    if not passthrough:
        print("用法: python devtool.py hub <start|status> [...]")
        return 1
    sub = passthrough[0]
    if sub == "start":
        import subprocess

        root = Path(__file__).resolve().parent.parent.parent
        cmd = ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8520", "--reload"]
        print("启动 Calc Hub 服务: http://localhost:8520/api/hub")
        print("API 文档: http://localhost:8520/api/docs")
        subprocess.run(cmd, cwd=str(root / "web" / "backend"))
        return 0
    elif sub == "status":
        import json
        import urllib.request

        try:
            resp = urllib.request.urlopen("http://localhost:8520/api/hub/stats", timeout=3)
            data = json.loads(resp.read())
            print("Calc Hub 状态:")
            print(f"  数据库: {data.get('db_path', '?')}")
            print(f"  配置包数: {data.get('total_packs', '?')}")
        except Exception as e:
            print(f"Calc Hub 服务未运行: {e}")
            return 1
        return 0
    else:
        print(f"未知子命令: {sub}")
        return 1


def main() -> None:
    """CLI 入口。解析子命令并分派到对应处理函数。"""
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
    hub_parser = sub.add_parser("hub", help="启动 Calc Hub 社区市场", add_help=False)
    hub_parser.add_argument("--port", type=int, default=8080, help="端口 (默认 8080)")
    sub.add_parser("framework", help="构建/发布 framework PyPI 包", add_help=False)
    sub.add_parser("plugin", help="插件打包/安装/目录管理", add_help=False)
    sub.add_parser("check-origin", help="AI 代码来源/版权检测", add_help=False)
    sub.add_parser("installer", help="NSIS 安装包构建/检查", add_help=False)
    sub.add_parser("scaffold", help="新游戏适配脚手架", add_help=False)

    args, _ = parser.parse_known_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    funcs = {
        "check-deps": _cmd_check_deps,
        "check-layout": _cmd_check_layout,
        "sync-bwiki": _cmd_sync_bwiki,
        "launcher": _cmd_launcher,
        "hub": _cmd_hub,
        "framework": _cmd_framework,
        "plugin": _cmd_plugin,
        "check-origin": _cmd_check_origin,
        "installer": _cmd_installer,
        "scaffold": _cmd_scaffold,
    }
    result = funcs[args.command](args)
    if isinstance(result, int):
        sys.exit(result)


if __name__ == "__main__":
    main()
