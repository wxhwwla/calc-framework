#!/usr/bin/env python3
"""数据设计器 — 根入口。

用法::

    python designer_main.py

实际代码位于: games/endfield/designer_main.py
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

_GAMES = Path(__file__).resolve().parent / "games" / "endfield"
if str(_GAMES.parent) not in sys.path:
    sys.path.insert(0, str(_GAMES))

main = importlib.import_module("designer_main").main

if __name__ == "__main__":
    main()
