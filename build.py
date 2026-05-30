#!/usr/bin/env python3
"""终末地计算器打包脚本 — 根入口。

用法::

    python build.py                     # 默认打包全部目标
    python build.py --target designer   # 仅打包设计器

实际代码位于: main_build.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parent
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from main_build import main

if __name__ == "__main__":
    main()
