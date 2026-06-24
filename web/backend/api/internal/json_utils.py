# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""JSON 工具函数与路径常量。"""

from __future__ import annotations

import asyncio
import json
import sys as _sys
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


def _validate_path_no_traversal(path: Path) -> None:
    """校验路径不含 ``..`` 或其他穿越标记。

    此检查防止调用方使用 ``../etc/passwd`` 等路径穿越攻击。

    Raises:
        ValueError: 路径含 ``..`` 等穿越标记。
    """
    if ".." in str(path):
        raise ValueError(f"禁止路径穿越: {path}")


def save_json(path: Path, data: Any) -> None:
    """将对象写入 JSON 文件（同步）。

    Raises:
        ValueError: 路径含穿越标记。
    """
    _validate_path_no_traversal(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


async def aload_json(path: Path) -> Any:
    """在线程池中加载 JSON，避免阻塞事件循环。"""
    return await asyncio.to_thread(load_json, path)


async def asave_json(path: Path, data: Any) -> None:
    """在线程池中写入 JSON，避免阻塞事件循环。

    Raises:
        ValueError: 路径含穿越标记。
    """
    await asyncio.to_thread(save_json, path, data)


# ── 路径常量 ──────────────────────────────────────────

if getattr(_sys, "frozen", False):
    # PyInstaller 冻结模式：_MEIPASS 是解压目录
    _BASE_DIR = Path(_sys._MEIPASS)
else:
    _BASE_DIR = Path(__file__).resolve().parents[4]

_REPO_ROOT = _BASE_DIR
REPO_ROOT = _REPO_ROOT
FRAMEWORK_SRC = _REPO_ROOT / "framework" / "src"
ADAPTER_ROOT = _REPO_ROOT / "framework" / "adapters"
ENDFIELD_GAME_ROOT = _REPO_ROOT / "games" / "endfield"
ENDFIELD_DATA_ROOT = ENDFIELD_GAME_ROOT / "data"
