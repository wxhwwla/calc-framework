#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""数据设计器 — 桌面 GUI 入口（数据设计器）。

用法::

    python scripts/main_designer.py

实际代码位于: tools/endfield_designer/designer_main.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _path_setup import ensure_root

ensure_root()

from tools.endfield_designer.designer_main import main

if __name__ == "__main__":
    main()
