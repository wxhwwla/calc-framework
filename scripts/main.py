#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""终末地伤害计算器 — 根入口（推荐使用启动器选择游戏）。

用法::

    python scripts/main_launcher.py       # ← 推荐：启动器中选择游戏
    python scripts/main.py                # 直接启动终末地
    python scripts/main_arknights.py      # 直接启动明日方舟

实际代码位于: games/endfield/main.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _path_setup import ensure_root

ensure_root()

from games.endfield.main import main

if __name__ == "__main__":
    print("=" * 60)
    print("  ⚠️ 注意：此入口已弃用，将在未来版本中移除。")
    print("  推荐使用启动器选择游戏：")
    print("    python scripts/启动.bat 游戏")
    print("    python scripts/main_launcher.py")
    print("=" * 60)
    print()
    main()
