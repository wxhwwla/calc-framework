# -*- coding: utf-8 -*-
"""attr_schema 生成器 — 从属性列表生成 attr_schema.json。"""

from __future__ import annotations

import json
from typing import Any


def build_attr_schema(attributes: list[dict[str, Any]]) -> dict[str, Any]:
    """从属性列表生成 attr_schema JSON。

    Args:
        attributes: 属性列表，每项 {name, type, source, default, description}

    Returns:
        {"attributes": [...]}
    """
    return {"attributes": attributes}


def attr_schema_to_json(attributes: list[dict[str, Any]]) -> str:
    """生成格式化的 attr_schema.json 字符串。"""
    return json.dumps(build_attr_schema(attributes), ensure_ascii=False, indent=2)
