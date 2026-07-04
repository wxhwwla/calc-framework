# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""
纯 Python 级联过滤模型：类型/星级/名称/等级四级联动的数据过滤逻辑。

从 qt_panel.py 提取，不依赖 PySide6，可被 Web/CLI/测试复用。
"""

from __future__ import annotations

from typing import Any


def filter_by_type(
    data_list: list[dict[str, Any]],
    type_name: str,
) -> list[dict[str, Any]]:
    """按类型过滤数据列表。"""
    return [item for item in data_list if item.get("类型") == type_name]


def extract_stars(filtered: list[dict[str, Any]]) -> list[str]:
    """从过滤后的列表中提取去重排序的星级列表。"""
    return sorted(
        {str(item["星级"]) for item in filtered if "星级" in item},
        key=int,
    )


def filter_by_star(
    filtered: list[dict[str, Any]],
    star_str: str,
) -> list[dict[str, Any]]:
    """在已按类型过滤的列表中进一步按星级过滤。"""
    return [item for item in filtered if str(item.get("星级", "")) == star_str]


def extract_names(filtered: list[dict[str, Any]]) -> list[str]:
    """从过滤后的列表中提取名称列表。"""
    return [item["名称"] for item in filtered if "名称" in item]


def resolve_selected_entity(
    data_list: list[dict[str, Any]],
    name: str,
) -> dict[str, Any] | None:
    """按名称查找实体条目。"""
    return next(
        (item for item in data_list if item.get("名称") == name),
        None,
    )


def extract_max_level(entity: dict[str, Any]) -> int:
    """从实体条目中提取最大等级（等级数组长度）。"""
    return len(entity.get("等级", []))


def extract_types(data_list: list[dict[str, Any]]) -> list[str]:
    """从完整数据列表中提取去重排序的类型列表。"""
    return sorted({item["类型"] for item in data_list if "类型" in item})
