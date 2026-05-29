#!/usr/bin/env python3
"""依赖自检工具 — 列出 GUI / 开发可选依赖是否已安装。

用法::

    python check_deps.py

等价命令：python tools/check_optional_deps.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parent
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from tools.check_optional_deps import main

if __name__ == "__main__":
    sys.exit(main())
