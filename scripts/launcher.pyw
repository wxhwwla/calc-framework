# SPDX-License-Identifier: AGPL-3.0
"""
终末地伤害计算器 — Web 服务器启动器

💡 已整合到「游戏计算器启动器」中。

推荐使用：
    python scripts/启动游戏.bat          # 桌面启动器 → 可启动 Web 服务器
    python scripts/main_launcher.py      # 同上

直接运行此文件也可打开桌面启动器（其中包含 Web 服务器控制区）。
"""
from __future__ import annotations

import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parent

sys.path.insert(0, str(_REPO))
from _path_setup import ensure_root

ensure_root()

if __name__ == "__main__":
    print("=" * 60)
    print("  💡 提示：Web 服务器启动器已整合到「游戏计算器启动器」")
    print()
    print("  推荐使用：")
    print("    python scripts/启动游戏.bat")
    print("    python scripts/main_launcher.py")
    print()
    print("  即将自动打开启动器…")
    print("=" * 60)
    print()

    import subprocess
    subprocess.Popen(
        [sys.executable, str(_REPO / "main_launcher.py")],
        creationflags=getattr(subprocess, "CREATE_NEW_CONSOLE", 0),
    )
