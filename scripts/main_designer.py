#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""数据设计器 — 根入口。

启动数据维护 GUI（公式反推 / 数据编辑 / 数据浏览）。

Usage::

    python main_designer.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _path_setup import ensure_root, ensure_tools

ensure_root()
ensure_tools()

from endfield_designer.designer_main import main

if __name__ == "__main__":
    main()
