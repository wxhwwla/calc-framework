# SPDX-License-Identifier: AGPL-3.0
"""节点值格式化 — 将 DAG 节点值按格式说明渲染为展示字符串。"""

from __future__ import annotations

from typing import Any


def format_node_value(value: Any, format_spec: str | None = None) -> str:
    if value is None:
        return "N/A"
    if not format_spec:
        return str(value)
    try:
        return f"{value:{format_spec}}"
    except (ValueError, TypeError):
        return str(value)
