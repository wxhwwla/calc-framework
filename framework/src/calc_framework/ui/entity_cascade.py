# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""级联实体选择器 — 纯逻辑（无 PySide6 依赖）。

``meta.json`` 可选 ``entity_selectors`` 配置::

    [
      {
        "source": "weapon",
        "data_file": "weapons",
        "steps": [
          {"field": "舰船分类", "label": "舰船种类"},
          {"field": "舰船", "label": "舰船"},
          {"field": "名称", "label": "武器", "display_field": "武器标签"}
        ]
      }
    ]

后续步骤的选项由前面步骤的选中值过滤；列表字段（如 ``舰船分类``）中的
任一值都可作为筛选条件。最后一级的值会作为实体 ``名称`` 注入 DAG 命名空间。
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

__all__ = [
    "field_values",
    "matching_records",
    "option_displays",
    "step_options",
]


def _text(value: Any) -> str:
    """把字段值规范化为非空字符串；None/空串返回空字符串。"""
    if value is None:
        return ""
    return str(value).strip()


def field_values(record: dict[str, Any], field: str) -> tuple[str, ...]:
    """读取记录中某个选择步骤的候选值。

    标量字段返回单元素元组；列表字段展开为多个值（用于一个舰船同属
    多个舰船种类的情况）；字段缺失或为空时返回空元组。

    Args:
        record: 实体记录字典。
        field: 字段名。

    Returns:
        规范化后的非空字符串元组，保留记录中的原始顺序。
    """
    value = record.get(field)
    if isinstance(value, list | tuple):
        return tuple(text for item in value if (text := _text(item)))
    text = _text(value)
    return (text,) if text else ()


def matching_records(
    records: Sequence[dict[str, Any]],
    steps: Sequence[dict[str, Any]],
    selections: Sequence[str | None],
) -> list[dict[str, Any]]:
    """按已选步骤过滤记录。

    Args:
        records: 全量实体记录。
        steps: 选择步骤配置。
        selections: 每个步骤的选中值；``None`` 表示尚未选择，遇到后停止过滤。

    Returns:
        匹配全部已选条件的记录列表。
    """
    matched = list(records)
    for index, step in enumerate(steps):
        selection = selections[index] if index < len(selections) else None
        if selection is None:
            break
        field = _text(step.get("field"))
        if not field:
            continue
        matched = [record for record in matched if selection in field_values(record, field)]
    return matched


def step_options(
    records: Sequence[dict[str, Any]],
    steps: Sequence[dict[str, Any]],
    selections: Sequence[str | None],
    index: int,
) -> list[str]:
    """计算第 ``index`` 级下拉的候选值。

    候选顺序按记录顺序去重，因此数据文件的排序决定界面排序。

    Args:
        records: 全量实体记录。
        steps: 选择步骤配置。
        selections: 每个步骤的选中值。
        index: 要计算的下标（0-based）。

    Returns:
        去重后的候选字符串列表；下标或字段无效时返回空列表。
    """
    if index < 0 or index >= len(steps):
        return []
    field = _text(steps[index].get("field"))
    if not field:
        return []

    options: list[str] = []
    seen: set[str] = set()
    for record in matching_records(records, steps[:index], selections[:index]):
        for value in field_values(record, field):
            if value not in seen:
                seen.add(value)
                options.append(value)
    return options


def option_displays(
    records: Sequence[dict[str, Any]],
    steps: Sequence[dict[str, Any]],
    selections: Sequence[str | None],
    index: int,
) -> dict[str, str]:
    """计算候选值到显示文案的映射。

    若步骤配置了 ``display_field``，用该字段的值作为下拉显示文案，
    否则直接显示候选值。同一候选值只取第一条匹配记录的显示文案。

    Args:
        records: 全量实体记录。
        steps: 选择步骤配置。
        selections: 每个步骤的选中值。
        index: 要计算的下标（0-based）。

    Returns:
        ``{候选值: 显示文案}``；下标或字段无效时返回空字典。
    """
    options = step_options(records, steps, selections, index)
    if not options:
        return {}
    display_field = _text(steps[index].get("display_field"))
    displays = {value: value for value in options}
    if not display_field:
        return displays

    remaining = set(options)
    for record in matching_records(records, steps[:index], selections[:index]):
        display = _text(record.get(display_field))
        if not display:
            continue
        for value in field_values(record, _text(steps[index].get("field"))):
            if value in remaining:
                displays[value] = display
                remaining.discard(value)
        if not remaining:
            break
    return displays
