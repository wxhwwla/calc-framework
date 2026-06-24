#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0

# -*- coding: utf-8 -*-

# SPDX-License-Identifier: AGPL-3.0
"""将 games/endfield 包加入 sys.path（BWIKI 工具调用反推/录入用）。"""

from __future__ import annotations


import sys

from pathlib import Path


_REPO_ROOT = Path(__file__).resolve().parent.parent.parent

_PKG = _REPO_ROOT / "games" / "endfield"


def ensure_package_path() -> Path:
    """将 games/endfield 包加入 sys.path 并返回包路径。"""
    if str(_PKG) not in sys.path:
        sys.path.insert(0, str(_PKG))

    return _PKG
