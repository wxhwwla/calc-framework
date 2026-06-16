#!/usr/bin/env python3

# SPDX-License-Identifier: AGPL-3.0
"""GUI 偏好读取：启动页策略与上次页面。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from utils.path_utils import get_application_dir

from games.endfield.framework_bridge import get_logger

_logger = get_logger(__name__)

UI_PREFERENCES_FILE = "ui_preferences.json"

PAGE_MAIN = "计算页"

PAGE_ADVANCED = "高级页"

STARTUP_MODE_ALWAYS_MAIN = "always_main"

STARTUP_MODE_REMEMBER_LAST = "remember_last"


def _default_preferences() -> dict[str, Any]:
    return {
        "startup_page_mode": STARTUP_MODE_ALWAYS_MAIN,
        "last_page": PAGE_MAIN,
        # 角色/武器侧「技能/武器技能」折叠：无记录时默认展开
        "char_advanced_expanded": True,
        "weapon_advanced_expanded": True,
    }
    """default preferences。"""


def _preferences_path(*, base_dir: Path | None = None) -> Path:
    root = base_dir if base_dir is not None else get_application_dir()

    """preferences path。"""
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
        _logger.warning("读取偏好文件失败，使用默认值: %s", path)
        return defaults

    mode = str(data.get("startup_page_mode", STARTUP_MODE_ALWAYS_MAIN))

    if mode not in (STARTUP_MODE_ALWAYS_MAIN, STARTUP_MODE_REMEMBER_LAST):
        mode = STARTUP_MODE_ALWAYS_MAIN

    page = str(data.get("last_page", PAGE_MAIN))

    if page not in (PAGE_MAIN, PAGE_ADVANCED):
        page = PAGE_MAIN

    char_raw = data.get("char_advanced_expanded")

    if char_raw is None:
        char_expanded = bool(defaults["char_advanced_expanded"])

    else:
        char_expanded = bool(char_raw)

    weapon_raw = data.get("weapon_advanced_expanded")

    if weapon_raw is None:
        weapon_expanded = bool(defaults["weapon_advanced_expanded"])

    else:
        weapon_expanded = bool(weapon_raw)

    return {
        "startup_page_mode": mode,
        "last_page": page,
        "char_advanced_expanded": char_expanded,
        "weapon_advanced_expanded": weapon_expanded,
    }


def save_ui_preferences(preferences: dict[str, Any], *, base_dir: Path | None = None) -> None:
    """持久化 GUI 偏好；失败时静默忽略（不阻塞主流程）。"""

    defaults = _default_preferences()

    path = _preferences_path(base_dir=base_dir)

    path.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "startup_page_mode": str(preferences.get("startup_page_mode", STARTUP_MODE_ALWAYS_MAIN)),
        "last_page": str(preferences.get("last_page", PAGE_MAIN)),
        "char_advanced_expanded": bool(preferences.get("char_advanced_expanded", defaults["char_advanced_expanded"])),
        "weapon_advanced_expanded": bool(
            preferences.get("weapon_advanced_expanded", defaults["weapon_advanced_expanded"])
        ),
    }

    try:
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    except Exception:
        _logger.warning("保存偏好文件失败: %s", path)


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


def record_char_advanced_expanded(preferences: dict[str, Any], *, expanded: bool) -> dict[str, Any]:
    """更新内存中的角色「技能等级」折叠展开态。"""

    updated = dict(preferences)

    updated["char_advanced_expanded"] = bool(expanded)

    return updated


def record_weapon_advanced_expanded(preferences: dict[str, Any], *, expanded: bool) -> dict[str, Any]:
    """更新内存中的武器「武器技能」折叠展开态。"""

    updated = dict(preferences)

    updated["weapon_advanced_expanded"] = bool(expanded)

    return updated
