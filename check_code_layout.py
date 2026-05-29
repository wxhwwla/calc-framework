#!/usr/bin/env python3
"""代码布局规范检查工具 — 目录宽度 ≤10、业务 .py ≤400 行。

用法::

    python check_code_layout.py
    python check_code_layout.py --max-lines 400

等价命令：python tools/check_layout.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parent
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from tools.check_layout import main

if __name__ == "__main__":
    sys.exit(main())
