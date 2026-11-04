# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""适配器实体数据文件 — 归一化、校验、序列化与绑定告警。"""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from typing import Any

# 实体来源 -> 适配包内数据文件相对路径
DATA_FILE_BY_SOURCE: dict[str, str] = {
    "character": "data/characters.json",
    "weapon": "data/weapons.json",
    "equipment": "data/equipments.json",
    "enemy": "data/enemies.json",
}

# 单个数据文件上限（与 ProjectScope.write_text 的兜底限制一致）
MAX_DATA_FILE_BYTES = 512 * 1024

# 查看器用于识别实体的名称字段
NAME_KEY = "名称"

_NON_ENTITY_SOURCES = frozenset({"user_input", "input", "computed"})


class DataFileError(ValueError):
    """data_files 声明不合法。"""


def serialize_data_file(records: list[dict[str, Any]]) -> str:
    """把实体记录列表序列化为 UTF-8 友好的 JSON 文本。"""
    return json.dumps(records, ensure_ascii=False, indent=2)


def normalize_data_files(
    raw: Any,
) -> tuple[dict[str, list[dict[str, Any]]], list[str]]:
    """校验并归一化 data_files 声明。

    Args:
        raw: ``{source: [记录, ...]}``；source 仅允许 character/weapon/equipment/enemy。

    Returns:
        ``(归一化后的映射, 告警列表)``；``raw`` 为 None 时返回 ``({}, [])``。

    Raises:
        DataFileError: 来源非法、记录结构错误、名称为空/重复、不可序列化或文件过大。
    """
    if raw is None:
        return {}, []
    if not isinstance(raw, Mapping):
        raise DataFileError("data_files 必须是 {source: [记录]} 映射")

    normalized: dict[str, list[dict[str, Any]]] = {}
    warnings: list[str] = []
    for source, records in raw.items():
        if source not in DATA_FILE_BY_SOURCE:
            allowed = ", ".join(DATA_FILE_BY_SOURCE)
            raise DataFileError(f"不支持的 data_files 来源: {source!r}（允许: {allowed}）")
        if not isinstance(records, list):
            raise DataFileError(f"data_files[{source!r}] 必须是记录列表")
        if not records:
            warnings.append(f"数据文件 {DATA_FILE_BY_SOURCE[source]} 为空列表")
            normalized[source] = []
            continue

        names: set[str] = set()
        cleaned: list[dict[str, Any]] = []
        for index, record in enumerate(records):
            if not isinstance(record, dict):
                raise DataFileError(f"data_files[{source!r}][{index}] 必须是对象")
            name = record.get(NAME_KEY)
            if not isinstance(name, str) or not name.strip():
                raise DataFileError(f"data_files[{source!r}][{index}] 缺少非空字符串 {NAME_KEY!r}")
            if name in names:
                raise DataFileError(f"data_files[{source!r}] 中 {NAME_KEY} 重复: {name!r}")
            if any(not isinstance(key, str) for key in record):
                raise DataFileError(f"data_files[{source!r}][{index}] 的记录键必须是字符串")
            names.add(name)
            cleaned.append(dict(record))

        try:
            payload = serialize_data_file(cleaned)
        except (TypeError, ValueError) as e:
            raise DataFileError(f"data_files[{source!r}] 无法序列化为 JSON: {e}") from e
        size = len(payload.encode("utf-8"))
        if size > MAX_DATA_FILE_BYTES:
            raise DataFileError(
                f"数据文件 {DATA_FILE_BY_SOURCE[source]} 过大: {size} 字节（上限 {MAX_DATA_FILE_BYTES}）"
            )
        normalized[source] = cleaned
    return normalized, warnings


def bound_entity_sources(data_files: Mapping[str, list[dict[str, Any]]]) -> frozenset[str]:
    """返回真正绑定了实体记录的来源（空列表视为未绑定）。"""
    return frozenset(source for source, records in data_files.items() if records)


def binding_warnings(
    variable_sources: Iterable[str],
    data_files: Mapping[str, list[dict[str, Any]]],
) -> list[str]:
    """生成变量来源与数据文件绑定的说明性告警。

    空列表的数据文件不会提供任何实体选项，因此按「未绑定」处理；
    对应变量会被改写为 ``user_input``，避免在 UI 中无法编辑。
    """
    sources = list(variable_sources)
    bound = bound_entity_sources(data_files)
    warnings: list[str] = []
    for source in sorted(set(sources)):
        if source in _NON_ENTITY_SOURCES:
            continue
        if source in bound:
            warnings.append(f"来源 {source!r} 已绑定数据文件，其变量由实体选择提供、不出现在输入区")
        elif source in data_files:
            warnings.append(f"来源 {source!r} 的数据文件为空，按未绑定处理，其变量已改写为 user_input 输入")
        else:
            warnings.append(f"来源 {source!r} 未绑定数据文件，其变量已改写为 user_input 输入")
    for source in sorted(data_files):
        if source not in sources:
            warnings.append(f"数据文件 {DATA_FILE_BY_SOURCE[source]} 没有对应来源的变量使用")
    return warnings
