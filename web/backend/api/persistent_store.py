# SPDX-License-Identifier: AGPL-3.0
"""Web 后端 JSON 文件持久化（PA WSGI 进程重启后仍保留）。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_STORE_DIR = Path(__file__).resolve().parents[1] / "data"


def _path(name: str) -> Path:
    _STORE_DIR.mkdir(parents=True, exist_ok=True)
    return _STORE_DIR / f"{name}.json"


def load_list(name: str) -> list[dict[str, Any]]:
    path = _path(name)
    if not path.is_file():
        return []
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def save_list(name: str, items: list[dict[str, Any]]) -> None:
    path = _path(name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
