#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""装备列表按套装筛选（GUI 固定配装用）。"""

from __future__ import annotations

from typing import Any

SET_FILTER_ALL = "全部"
SET_FILTER_LOOSE = "仅散件"


def list_set_filter_options(rows: list[dict[str, Any]]) -> list[str]:
    """生成套装筛选项：全部、各套装名、仅散件（若有散件）。"""
    options = [SET_FILTER_ALL]
    seen: set[str] = set()
    has_loose = False
    for row in rows:
        set_name = str(row.get("套装") or "").strip()
        if set_name:
            if set_name not in seen:
                options.append(set_name)
                seen.add(set_name)
        else:
            has_loose = True
    if has_loose:
        options.append(SET_FILTER_LOOSE)
    return options


def filter_rows_by_set_label(
    rows: list[dict[str, Any]],
    set_label: str,
) -> list[dict[str, Any]]:
    """按套装筛选项过滤装备行。"""
    label = (set_label or "").strip()
    if label in ("", SET_FILTER_ALL):
        return list(rows)
    if label == SET_FILTER_LOOSE:
        return [row for row in rows if not str(row.get("套装") or "").strip()]
    return [row for row in rows if str(row.get("套装") or "").strip() == label]


def equipment_names_from_rows(rows: list[dict[str, Any]]) -> list[str]:
    names: list[str] = []
    for row in rows:
        name = str(row.get("名称") or "").strip()
        if name:
            names.append(name)
    return names
