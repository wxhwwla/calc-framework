#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试用仓库路径（任意深度子目录均可 import）。"""

from __future__ import annotations

from pathlib import Path

PKG_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = PKG_ROOT.parent
TOOLS_ROOT = REPO_ROOT / "tools"
