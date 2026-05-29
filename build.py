#!/usr/bin/env python3
"""终末地计算器打包脚本 — 根入口。

用法::

    python build.py
    python build.py --target designer

实际代码位于: games/endfield/build.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_GAMES = Path(__file__).resolve().parent / "games" / "endfield"
if str(_GAMES) not in sys.path:
    sys.path.insert(0, str(_GAMES))

from build import main

if __name__ == "__main__":
    main()
