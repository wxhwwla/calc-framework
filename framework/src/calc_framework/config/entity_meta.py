# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""``meta.entity_detail`` 与 ``meta.entity_input_rules`` 归一化。

两个配置都是可选的查看器增强：

- ``entity_detail``：在左侧显示选中实体的字段明细（支持分组与多列）。
- ``entity_input_rules``：按实体字段值禁用无关的 ``user_input`` 控件，
  例如「不需要母舰」时灰显母舰加成、「能量武器」时灰显物理护甲。

本模块保持纯逻辑（无 PySide6 依赖），查看器、MCP 校验与测试共用。
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

__all__ = [
    "EntityMetaError",
    "format_detail_value",
    "normalize_entity_detail",
    "normalize_entity_input_rules",
    "rule_matches",
]

_DETAIL_KEYS = frozenset({"source", "title", "sections"})
_DETAIL_SECTION_KEYS = frozenset({"title", "fields", "columns"})
_DETAIL_FIELD_KEYS = frozenset({"field", "label", "format"})
_RULE_KEYS = frozenset({"source", "field", "equals", "disable", "reason"})
_MAX_DETAIL_COLUMNS = 3


class EntityMetaError(ValueError):
    """``entity_detail`` / ``entity_input_rules`` 配置不合法。"""


def normalize_entity_detail(
    raw: Any,
    data_files: Mapping[str, list[dict[str, Any]]] | None = None,
) -> dict[str, Any] | None:
    """校验并归一化 ``meta.entity_detail``。

    Args:
        raw: 原始配置；``None`` 表示不启用详情面板。
        data_files: ``{实体来源: 记录列表}``，提供时校验来源与字段存在。

    Returns:
        归一化配置：``{source, title, sections: [{title, columns, fields}]}``；
        ``raw`` 为 ``None`` 时返回 ``None``。

    Raises:
        EntityMetaError: 结构非法、来源无数据或字段不存在。
    """
    if raw is None:
        return None
    if not isinstance(raw, Mapping):
        raise EntityMetaError("entity_detail 必须是对象")

    _reject_unknown(raw, _DETAIL_KEYS, "entity_detail")
    source = _required_text(raw.get("source"), "entity_detail.source")
    records = _source_records(data_files, source, "entity_detail")

    raw_sections = raw.get("sections")
    if not _is_sequence(raw_sections) or not raw_sections:
        raise EntityMetaError("entity_detail.sections 必须是非空数组")

    sections = [
        _normalize_detail_section(item, f"entity_detail.sections[{index}]", records) for index, item in enumerate(raw_sections)
    ]
    title = _optional_text(raw.get("title")) or "实体数据"
    return {"source": source, "title": title, "sections": sections}


def normalize_entity_input_rules(
    raw: Any,
    *,
    data_files: Mapping[str, list[dict[str, Any]]] | None = None,
    user_input_paths: Sequence[str] | None = None,
) -> list[dict[str, Any]]:
    """校验并归一化 ``meta.entity_input_rules``。

    Args:
        raw: 规则数组；``None`` 或空数组返回 ``[]``。
        data_files: ``{实体来源: 记录列表}``，提供时校验来源与字段存在。
        user_input_paths: 允许被禁用的 ``user_input.*`` 路径；提供时严格校验。

    Returns:
        归一化规则列表，每项含 ``source``/``field``/``equals``/``disable``，
        可选 ``reason``。

    Raises:
        EntityMetaError: 结构非法、来源/字段不存在或 disable 路径无效。
    """
    if raw is None:
        return []
    if not _is_sequence(raw):
        raise EntityMetaError("entity_input_rules 必须是对象数组")

    allowed_paths = set(user_input_paths) if user_input_paths is not None else None
    rules: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for index, item in enumerate(raw):
        rule = _normalize_input_rule(item, index, data_files, allowed_paths)
        key = (rule["source"], rule["field"], repr(rule["equals"]))
        if key in seen:
            raise EntityMetaError(
                f"entity_input_rules[{index}] 与前面的规则重复: {rule['source']}.{rule['field']} == {rule['equals']!r}"
            )
        seen.add(key)
        rules.append(rule)
    return rules


def rule_matches(rule: Mapping[str, Any], record: Mapping[str, Any]) -> bool:
    """判断规则是否命中记录。

    字段缺失或为空视为「未知」，不命中——这样查看器会保留输入可编辑，
    而不是把不确定的情况误判为禁用。
    """
    field = str(rule.get("field") or "")
    if field not in record:
        return False
    return _value_equals(record.get(field), rule.get("equals"))


def format_detail_value(value: Any, format_spec: str = "") -> str:
    """把实体字段值格式化为详情面板文本。"""
    if value is None:
        return "—"
    if isinstance(value, list | tuple):
        return "、".join(format_detail_value(item, format_spec) for item in value)
    if isinstance(value, bool):
        return "是" if value else "否"
    if isinstance(value, int | float):
        if format_spec:
            try:
                return f"{value:{format_spec}}"
            except (ValueError, TypeError):
                pass
        if float(value).is_integer():
            return str(int(value))
        return f"{float(value):.2f}".rstrip("0").rstrip(".")
    text = str(value)
    return text if text.strip() else "—"


def _normalize_detail_section(
    item: Any,
    location: str,
    records: list[dict[str, Any]] | None,
) -> dict[str, Any]:
    if not isinstance(item, Mapping):
        raise EntityMetaError(f"{location} 必须是对象")
    _reject_unknown(item, _DETAIL_SECTION_KEYS, location)

    raw_fields = item.get("fields")
    if not _is_sequence(raw_fields) or not raw_fields:
        raise EntityMetaError(f"{location}.fields 必须是非空数组")

    fields = [
        _normalize_detail_field(raw_field, f"{location}.fields[{index}]", records) for index, raw_field in enumerate(raw_fields)
    ]

    columns = item.get("columns", 1)
    if isinstance(columns, bool) or not isinstance(columns, int):
        raise EntityMetaError(f"{location}.columns 必须是整数")
    if not 1 <= columns <= _MAX_DETAIL_COLUMNS:
        raise EntityMetaError(f"{location}.columns 必须在 1–{_MAX_DETAIL_COLUMNS} 之间")

    if "title" in item and not _optional_text(item.get("title")):
        raise EntityMetaError(f"{location}.title 不能为空")
    title = _optional_text(item.get("title")) or "基础"
    return {"title": title, "columns": columns, "fields": fields}


def _normalize_detail_field(
    item: Any,
    location: str,
    records: list[dict[str, Any]] | None,
) -> dict[str, Any]:
    if not isinstance(item, Mapping):
        raise EntityMetaError(f"{location} 必须是对象")
    _reject_unknown(item, _DETAIL_FIELD_KEYS, location)

    field = _required_text(item.get("field"), f"{location}.field")
    if records is not None and not _has_field_value(records, field):
        raise EntityMetaError(f"{location}.field 在实体记录中不存在: {field!r}")

    result: dict[str, Any] = {"field": field, "label": _optional_text(item.get("label")) or field}
    format_spec = _optional_text(item.get("format"))
    if format_spec:
        result["format"] = format_spec
    return result


def _normalize_input_rule(
    item: Any,
    index: int,
    data_files: Mapping[str, list[dict[str, Any]]] | None,
    allowed_paths: set[str] | None,
) -> dict[str, Any]:
    location = f"entity_input_rules[{index}]"
    if not isinstance(item, Mapping):
        raise EntityMetaError(f"{location} 必须是对象")
    _reject_unknown(item, _RULE_KEYS, location)

    source = _required_text(item.get("source"), f"{location}.source")
    records = _source_records(data_files, source, location)
    field = _required_text(item.get("field"), f"{location}.field")
    if records is not None and not _has_field_value(records, field):
        raise EntityMetaError(f"{location}.field 在 {source!r} 记录中不存在: {field!r}")

    if "equals" not in item:
        raise EntityMetaError(f"{location}.equals 不能为空")
    equals = item.get("equals")
    if not isinstance(equals, str | int | float | bool) or equals is None:
        raise EntityMetaError(f"{location}.equals 必须是字符串、数字或布尔值")
    if isinstance(equals, int | float) and not isinstance(equals, bool):
        equals = float(equals)

    raw_disable = item.get("disable")
    if not _is_sequence(raw_disable) or not raw_disable:
        raise EntityMetaError(f"{location}.disable 必须是非空字符串数组")
    disable: list[str] = []
    for disable_index, value in enumerate(raw_disable):
        path = _required_text(value, f"{location}.disable[{disable_index}]")
        if not path.startswith("user_input."):
            raise EntityMetaError(f"{location}.disable 只能包含 user_input.* 路径: {path!r}")
        if allowed_paths is not None and path not in allowed_paths:
            raise EntityMetaError(f"{location}.disable 引用了未声明的 user_input 变量: {path!r}")
        if path not in disable:
            disable.append(path)

    rule: dict[str, Any] = {
        "source": source,
        "field": field,
        "equals": equals,
        "disable": disable,
    }
    raw_reason = item.get("reason")
    if raw_reason is not None and not isinstance(raw_reason, str):
        raise EntityMetaError(f"{location}.reason 必须是字符串")
    reason = _optional_text(raw_reason)
    if reason:
        rule["reason"] = reason
    return rule


def _source_records(
    data_files: Mapping[str, list[dict[str, Any]]] | None,
    source: str,
    location: str,
) -> list[dict[str, Any]] | None:
    if data_files is None:
        return None
    records = data_files.get(source)
    if not records:
        raise EntityMetaError(f"{location} 的来源 {source!r} 没有可用的数据记录")
    return records


def _has_field_value(records: list[dict[str, Any]], field: str) -> bool:
    for record in records:
        if not isinstance(record, Mapping) or field not in record:
            continue
        value = record.get(field)
        if isinstance(value, list | tuple):
            if any(str(item).strip() for item in value if item is not None):
                return True
        elif value is not None and str(value).strip():
            return True
    return False


def _value_equals(value: Any, expected: Any) -> bool:
    if isinstance(value, list | tuple):
        return any(_value_equals(item, expected) for item in value)
    if isinstance(value, bool) or isinstance(expected, bool):
        return value == expected
    if isinstance(value, int | float) and isinstance(expected, int | float):
        return float(value) == float(expected)
    return str(value).strip() == str(expected).strip()


def _reject_unknown(item: Mapping[str, Any], allowed: frozenset[str], location: str) -> None:
    unknown = sorted(set(item) - allowed)
    if unknown:
        raise EntityMetaError(f"{location} 包含未知字段: {', '.join(unknown)}")


def _required_text(value: Any, location: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise EntityMetaError(f"{location} 不能为空")
    return text


def _optional_text(value: Any) -> str:
    return str(value).strip() if value is not None else ""


def _is_sequence(value: Any) -> bool:
    return isinstance(value, Sequence) and not isinstance(value, str | bytes)
