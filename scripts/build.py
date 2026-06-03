#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""终末地计算器打包脚本 — 根入口。

💡 提示：此文件已整合到 main_build.py

推荐用法::

    python main_build.py                     # 默认打包全部目标
    python main_build.py --target designer   # 仅打包设计器
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

if __name__ == "__main__":
    print("=" * 60)
    print("  💡 提示：build.py 已整合到 main_build.py")
    print()
    print("  推荐直接使用：")
    print("    python main_build.py [参数]")
    print()
    print("  正在自动转发到 main_build.py …")
    print("=" * 60)
    print()

    _REPO = Path(__file__).resolve().parent.parent
    target = _REPO / "scripts" / "main_build.py"
    args = sys.argv[1:]  # 转发原始参数
    cmd = [sys.executable, str(target)] + args
    proc = subprocess.run(cmd)
    sys.exit(proc.returncode)
