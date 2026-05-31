#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""JSON 读取器：从 JSON 文件中读取记录。

支持两种格式：
1. 标准列表格式：``[{...}, {...}]``
2. 旧终末地格式：需要配合 ``from_legacy_endfield`` 转换器
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, List

from ..schema import RawRecord


def read_json(path: str | Path, *, encoding: str = "utf-8") -> List[RawRecord]:
    """读取 JSON 文件返回记录列表。

    Args:
        path: JSON 文件路径
        encoding: 编码，默认 utf-8

    Returns:
        记录列表（字典）

    Raises:
        ValueError: JSON 顶层不是数组
    """
    with open(path, encoding=encoding) as f:
        data = json.load(f)

    if isinstance(data, dict):
        return [data]
    if isinstance(data, list):
        if not data:
            return []
        if isinstance(data[0], dict):
            return data

    raise ValueError(
        f"不支持的 JSON 格式：顶层须为对象或对象数组，"
        f"实际类型 {type(data).__name__}"
    )
