#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""配置包设计器 — 根入口。

用法::

    python main_pack_designer.py

实际代码位于: tools/designer/app.py
"""
from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _path_setup import ensure_root
ensure_root()

from tools.designer.app import main

if __name__ == "__main__":
    main()
