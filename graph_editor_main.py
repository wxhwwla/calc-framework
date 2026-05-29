#!/usr/bin/env python3
"""公式计算图编辑器 — 根入口。

用法::

    python graph_editor_main.py                      # 启动编辑器
    python graph_editor_main.py path/to/graph.json   # 打开已有文件

实际代码位于: games/endfield/graph_editor_main.py
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

_GAMES = Path(__file__).resolve().parent / "games" / "endfield"
if str(_GAMES) not in sys.path:
    sys.path.insert(0, str(_GAMES))

main = importlib.import_module("graph_editor_main").main

if __name__ == "__main__":
    main()
