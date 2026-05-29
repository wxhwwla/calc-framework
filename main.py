#!/usr/bin/env python3
"""终末地伤害计算器 — 根入口。

用法::

    python main.py

实际代码位于: games/endfield/main.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_GAMES = Path(__file__).resolve().parent / "games" / "endfield"
if str(_GAMES) not in sys.path:
    sys.path.insert(0, str(_GAMES))

from main import main

if __name__ == "__main__":
    main()
