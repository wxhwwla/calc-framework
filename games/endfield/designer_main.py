#!/usr/bin/env python3
"""
终末地设计器 — 根入口文件

启动数据维护 GUI（公式反推 / 数据编辑 / 数据浏览）。

使用方式：
    python designer_main.py
或  python -m designer

打包入口：python build.py --target designer
"""

import sys
from pathlib import Path

# 确保 repo 根在 sys.path 上（共享 utils/、release_bundle/ 等）
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# 确保包路径正确
_PKG_DIR = Path(__file__).resolve().parent
if str(_PKG_DIR) not in sys.path:
    sys.path.insert(0, str(_PKG_DIR))

from designer.designer_main import main

if __name__ == "__main__":
    main()
