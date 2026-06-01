#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""启动器 — 根入口。

提供便捷界面运行计算器、数据设计器、打包工具等子功能。
"""
from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _path_setup import ensure_root
ensure_root()

from calc_framework.ui.viewer import main as viewer_main

if __name__ == "__main__":
    viewer_main()
