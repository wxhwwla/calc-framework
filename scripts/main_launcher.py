#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""统一启动器 — 根入口（ADR-0012 Phase 1）。

默认打开 PySide6 启动器：列出已安装适配器、工具入口、打开 .calcpack。
若命令行传入 ``*.calcpack`` 路径则直接进入 CalcPackViewer。

用法::

  python scripts/main_launcher.py
  python scripts/main_launcher.py path/to/game.calcpack

完整桌面计算器也可从启动器内启动，或直接::

  python scripts/main.py          # 终末地
  python scripts/main_arknights.py  # 明日方舟
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _path_setup import ensure_framework_src, ensure_root

ensure_root()
ensure_framework_src()


def _open_calcpack_viewer(path: str) -> None:
    """打开 CalcPack 文件查看器。"""
    from calc_framework.ui.viewer import main as viewer_main

    sys.argv = [sys.argv[0], path]
    viewer_main()


def main() -> None:
    """CLI 入口。打开启动器或直接进入 CalcPackViewer。"""
    arg = sys.argv[1] if len(sys.argv) > 1 else None
    if arg and Path(arg).suffix.lower() == ".calcpack":
        _open_calcpack_viewer(arg)
        return
    from calc_framework.ui.launcher import run_gui_launcher

    run_gui_launcher()


if __name__ == "__main__":
    main()
