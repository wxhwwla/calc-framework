#!/usr/bin/env python3
"""游戏选择器启动器 — 命令行选择适配包并启动 ComputeSheet。

用法::

    python launcher.py                    # 交互选择
    python launcher.py <适配器名>         # 直接启动（如 endfield）

等价命令：cd framework && python -m calc_framework.launcher
"""

from __future__ import annotations

import sys
from pathlib import Path

_FRAMEWORK_SRC = Path(__file__).resolve().parent / "framework" / "src"
if str(_FRAMEWORK_SRC) not in sys.path:
    sys.path.insert(0, str(_FRAMEWORK_SRC))

from calc_framework.launcher import run_launcher

if __name__ == "__main__":
    adapter = sys.argv[1] if len(sys.argv) > 1 else None
    run_launcher(adapter)
