# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""``meta.entity_selectors`` 归一化与校验。

查看器用该配置把普通实体下拉替换为多级级联选择器。最后一级的 ``field``
必须是 ``名称``，其值会作为实体标识注入 DAG 命名空间；其他级只负责过滤。
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from tools.generator.data_files import DATA_FILE_BY_SOURCE, NAME_KEY

__all__ = ["SelectorError", "normalize_entity_selectors"]

_ITEM_KEYS = frozenset({"source", "data_file", "steps"})
_STEP_KEYS = frozenset({"field", "label", "display_field"})


class SelectorError(ValueError):
    """``entity_selectors`` 配置不合法。"""


def normalize_entity_selectors(
    raw: Any,
    data_files: Mapping[str, list[dict[str, Any]]] | None = None,
) -> list[dict[str, Any]]:
    """校验并归一化 ``meta.entity_selectors``。

    Args:
        raw: 选择器配置列表；每项含 ``source``、可选 ``data_file`` 与 ``steps``。
        data_files: 已归一化的数据文件映射，用于校验来源已绑定且字段存在。

    Returns:
        归一化后的选择器列表；``raw`` 为 None 时返回 ``[]``。

    Raises:
        SelectorError: 结构非法、来源无数据、字段不存在或末级不是 ``名称``。
    """
    if raw is None:
        return []
    if not isinstance(raw, Sequence) or isinstance(raw, str | bytes):
        raise SelectorError("entity_selectors 必须是对象数组")

    files = data_files or {}
    seen_sources: set[str] = set()
    selectors: list[dict[str, Any]] = []
    for index, item in enumerate(raw):
        selectors.append(_normalize_selector(index, item, files, seen_sources))
    return selectors


def _normalize_selector(
    index: int,
    item: Any,
    files: Mapping[str, list[dict[str, Any]]],
    seen_sources: set[str],
) -> dict[str, Any]:
    location = f"entity_selectors[{index}]"
    if not isinstance(item, Mapping):
        raise SelectorError(f"{location} 必须是对象")

    unknown = sorted(set(item) - _ITEM_KEYS)
    if unknown:
        raise SelectorError(f"{location} 包含未知字段: {', '.join(unknown)}")

    raw_source = item.get("source")
    source = raw_source.strip() if isinstance(raw_source, str) else ""
    if source not in DATA_FILE_BY_SOURCE:
        allowed = ", ".join(DATA_FILE_BY_SOURCE)
        raise SelectorError(f"{location}.source 无效: {raw_source!r}（允许: {allowed}）")
    if source in seen_sources:
        raise SelectorError(f"entity_selectors 中来源重复: {source!r}")
    seen_sources.add(source)

    records = files.get(source) or []
    if not records:
        raise SelectorError(f"{location} 的来源 {source!r} 没有非空 data_files 记录，无法生成级联选择器")

    expected_stem = Path(DATA_FILE_BY_SOURCE[source]).stem
    data_file = _normalize_data_file(item.get("data_file"), expected_stem, source, location)

    raw_steps = item.get("steps")
    if not isinstance(raw_steps, Sequence) or isinstance(raw_steps, str | bytes) or not raw_steps:
        raise SelectorError(f"{location}.steps 必须是非空数组")

    steps = [
        _normalize_step(raw_step, f"{location}.steps[{step_index}]", source, records)
        for step_index, raw_step in enumerate(raw_steps)
    ]
    if steps[-1]["field"] != NAME_KEY:
        raise SelectorError(f"{location}.steps 最后一级的 field 必须是 {NAME_KEY!r}")

    return {"source": source, "data_file": data_file, "steps": steps}


def _normalize_data_file(raw: Any, expected_stem: str, source: str, location: str) -> str:
    if raw is None or (isinstance(raw, str) and not raw.strip()):
        return expected_stem
    if not isinstance(raw, str):
        raise SelectorError(f"{location}.data_file 必须是字符串")

    text = raw.strip()
    if "\\" in text:
        raise SelectorError(f"{location}.data_file 不能包含反斜杠: {raw!r}")
    name = text.rsplit("/", 1)[-1]
    if name.endswith(".json"):
        name = name[:-5]
    if name != expected_stem:
        raise SelectorError(f"{location}.data_file 必须是 {expected_stem!r}（与 source {source!r} 的约定文件一致）")
    return name


def _normalize_step(
    raw: Any,
    location: str,
    source: str,
    records: list[dict[str, Any]],
) -> dict[str, Any]:
    if not isinstance(raw, Mapping):
        raise SelectorError(f"{location} 必须是对象")

    unknown = sorted(set(raw) - _STEP_KEYS)
    if unknown:
        raise SelectorError(f"{location} 包含未知字段: {', '.join(unknown)}")

    field = str(raw.get("field") or "").strip()
    if not field:
        raise SelectorError(f"{location}.field 不能为空")
    if not _has_field_value(records, field):
        raise SelectorError(f"{location}.field 在 {source!r} 数据记录中不存在: {field!r}")

    step: dict[str, Any] = {"field": field}
    label = str(raw.get("label") or "").strip()
    if label:
        step["label"] = label

    display_field = str(raw.get("display_field") or "").strip()
    if display_field:
        if not _has_field_value(records, display_field):
            raise SelectorError(f"{location}.display_field 在 {source!r} 数据记录中不存在: {display_field!r}")
        step["display_field"] = display_field
    return step


def _has_field_value(records: list[dict[str, Any]], field: str) -> bool:
    for record in records:
        if not isinstance(record, Mapping):
            continue
        value = record.get(field)
        if isinstance(value, list | tuple):
            if any(str(item).strip() for item in value if item is not None):
                return True
        elif value is not None and str(value).strip():
            return True
    return False
