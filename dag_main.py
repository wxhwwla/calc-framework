#!/usr/bin/env python3
"""终末地 DAG 工具 — 根入口。

用法::

    python dag_main.py                          # 重新生成 DAG
    python dag_main.py --debug                  # 启动 DAG 分步调试器

实际代码位于: games/endfield/dag_main.py
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

_GAMES = Path(__file__).resolve().parent / "games" / "endfield"
if str(_GAMES) not in sys.path:
    sys.path.insert(0, str(_GAMES))

main = importlib.import_module("dag_main").main

if __name__ == "__main__":
    main()
