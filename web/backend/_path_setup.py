# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""Web backend path setup -- centralized sys.path configuration."""

import sys
from pathlib import Path


def setup_paths() -> None:
    """将框架源码和仓库根目录加入 sys.path。"""
    _REPO_ROOT = Path(__file__).resolve().parents[2]
    _FRAMEWORK_SRC = _REPO_ROOT / "framework" / "src"
    for _p in [str(_FRAMEWORK_SRC), str(_REPO_ROOT)]:
        if _p not in sys.path:
            sys.path.insert(0, _p)


setup_paths()
