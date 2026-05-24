#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GUI 偏好读取：启动页策略与上次页面。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from utils.path_utils import get_application_dir

UI_PREFERENCES_FILE = "ui_preferences.json"
PAGE_MAIN = "计算页"
PAGE_ADVANCED = "高级页"
STARTUP_MODE_ALWAYS_MAIN = "always_main"
STARTUP_MODE_REMEMBER_LAST = "remember_last"


def _default_preferences() -> dict[str, Any]:
    return {
        "startup_page_mode": STARTUP_MODE_ALWAYS_MAIN,
        "last_page": PAGE_MAIN,
    }


def _preferences_path(*, base_dir: Path | None = None) -> Path:
    root = base_dir if base_dir is not None else get_application_dir()
    return root / UI_PREFERENCES_FILE


def load_ui_preferences(*, base_dir: Path | None = None) -> dict[str, Any]:
    """读取 GUI 偏好；文件缺失/损坏时返回默认值。"""
    defaults = _default_preferences()
    path = _preferences_path(base_dir=base_dir)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return defaults
    except Exception:
        return defaults
    mode = str(data.get("startup_page_mode", STARTUP_MODE_ALWAYS_MAIN))
    if mode not in (STARTUP_MODE_ALWAYS_MAIN, STARTUP_MODE_REMEMBER_LAST):
        mode = STARTUP_MODE_ALWAYS_MAIN
    page = str(data.get("last_page", PAGE_MAIN))
    if page not in (PAGE_MAIN, PAGE_ADVANCED):
        page = PAGE_MAIN
    return {
        "startup_page_mode": mode,
        "last_page": page,
    }


def save_ui_preferences(
    preferences: dict[str, Any], *, base_dir: Path | None = None
) -> None:
    """持久化 GUI 偏好；失败时静默忽略（不阻塞主流程）。"""
    path = _preferences_path(base_dir=base_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "startup_page_mode": str(preferences.get("startup_page_mode", STARTUP_MODE_ALWAYS_MAIN)),
        "last_page": str(preferences.get("last_page", PAGE_MAIN)),
    }
    try:
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        return


def resolve_startup_page(preferences: dict[str, Any]) -> str:
    """根据启动策略决定启动页。"""
    mode = str(preferences.get("startup_page_mode", STARTUP_MODE_ALWAYS_MAIN))
    if mode == STARTUP_MODE_REMEMBER_LAST:
        page = str(preferences.get("last_page", PAGE_MAIN))
        if page in (PAGE_MAIN, PAGE_ADVANCED):
            return page
    return PAGE_MAIN


def record_last_page(preferences: dict[str, Any], *, page: str) -> dict[str, Any]:
    """更新内存中的 last_page，返回新字典。"""
    normalized_page = page if page in (PAGE_MAIN, PAGE_ADVANCED) else PAGE_MAIN
    updated = dict(preferences)
    updated["last_page"] = normalized_page
    return updated

