# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""开发者工具箱页面 — 仓库路径与共享工具。

页面模块需要把仓库根目录放在 ``sys.path`` 最前面，才能导入
``tools.designer`` / ``tools.generator`` 等非包内模块。
"""

from __future__ import annotations

import sys
from pathlib import Path

from calc_framework.logging import get_logger

logger = get_logger(__name__)


def _find_repo_root() -> Path:
    """从当前模块向上查找包含 framework/ 和 tools/ 的仓库根目录。"""
    cur = Path(__file__).resolve().parent
    for _ in range(6):
        if (cur / "framework").is_dir() and (cur / "tools").is_dir():
            return cur
        cur = cur.parent
    # 回退：parents[4]（framework/src/calc_framework/dev_toolkit/pages_common.py → 根）
    return Path(__file__).resolve().parents[4]


_REPO_ROOT = _find_repo_root()
_REPO_ROOT_STR = str(_REPO_ROOT)

# 确保仓库根目录在 sys.path 最前面（Qt 初始化可能修改 sys.path）
if _REPO_ROOT_STR in sys.path:
    sys.path.remove(_REPO_ROOT_STR)
sys.path.insert(0, _REPO_ROOT_STR)


def _ensure_repo_on_path() -> None:
    """确保仓库根目录在 sys.path 最前面（防止 scripts/tools/ 遮蔽 tools/）。"""
    # 移除所有旧的仓库根目录条目
    while _REPO_ROOT_STR in sys.path:
        sys.path.remove(_REPO_ROOT_STR)
    # 插入到最前面
    sys.path.insert(0, _REPO_ROOT_STR)
