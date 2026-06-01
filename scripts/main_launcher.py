#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""启动器 — 根入口。

打开 CalcPackViewer：浏览/验证 `.calcpack` 配置包（任意游戏 adapter）。
用法:
  python scripts/main_launcher.py
  python scripts/main_launcher.py path/to/game.calcpack

桌面完整计算器请用 `scripts/main.py`（终末地）或 `scripts/main_arknights.py`（明日方舟）。
"""
from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _path_setup import ensure_root, ensure_framework_src
ensure_root()
ensure_framework_src()

from calc_framework.ui.viewer import main as viewer_main

if __name__ == "__main__":
    viewer_main()
