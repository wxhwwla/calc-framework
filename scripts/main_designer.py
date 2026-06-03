#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""数据设计器 — 已整合到开发者工具箱。

用法::

    推荐：python scripts/启动开发者工具箱.bat
    或：   python scripts/main_dev_toolkit.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _path_setup import ensure_root

ensure_root()

if __name__ == "__main__":
    print("=" * 60)
    print("  💡 提示：数据设计器已整合到「开发者工具箱」")
    print()
    print("  推荐入口：")
    print("    python scripts/启动开发者工具箱.bat")
    print("    python scripts/main_dev_toolkit.py")
    print()
    print("  即将自动打开开发者工具箱…")
    print("=" * 60)
    print()

    import subprocess
    subprocess.Popen(
        [sys.executable, str(Path(__file__).parent / "main_dev_toolkit.py")],
        creationflags=getattr(subprocess, "CREATE_NEW_CONSOLE", 0),
    )
