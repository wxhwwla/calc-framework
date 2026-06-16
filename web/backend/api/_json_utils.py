# SPDX-License-Identifier: AGPL-3.0
"""JSON 工具函数与路径常量。"""

import json
from pathlib import Path
from typing import Any


def load_json(path: Path) -> Any:
    """加载并解析 JSON 文件，文件不存在时返回 None。

    参数:
        path: JSON 文件路径。

    返回:
        解析后的 Python 对象，文件不存在时返回 None。
    """
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return None


# ── 路径常量 ──────────────────────────────────────────

import sys as _sys

if getattr(_sys, "frozen", False):
    # PyInstaller 冻结模式：_MEIPASS 是解压目录
    _BASE_DIR = Path(_sys._MEIPASS)
else:
    _BASE_DIR = Path(__file__).resolve().parents[3]

_REPO_ROOT = _BASE_DIR
REPO_ROOT = _REPO_ROOT
FRAMEWORK_SRC = _REPO_ROOT / "framework" / "src"
ADAPTER_ROOT = _REPO_ROOT / "framework" / "adapters"
ENDFIELD_GAME_ROOT = _REPO_ROOT / "games" / "endfield"
ENDFIELD_DATA_ROOT = ENDFIELD_GAME_ROOT / "data"
