#!/usr/bin/env python3
"""
数据设计器 — 根入口

启动数据维护 GUI（公式反推 / 数据编辑 / 数据浏览）。

使用方式：
    python main_designer.py
"""

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

_TOOLS = _REPO_ROOT / "tools"
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

from endfield_designer.designer_main import main

if __name__ == "__main__":
    main()
