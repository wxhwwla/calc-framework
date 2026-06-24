# -*- coding: utf-8 -*-
"""UI 布局生成器 — 从属性/输出列表生成 layout.json。"""

from __future__ import annotations

import json
from typing import Any


def build_layout(
    name: str,
    input_variables: list[str],
    output_names: list[str],
    *,
    description: str = "",
) -> dict[str, Any]:
    """构建 UI layout JSON。

    Args:
        name: 计算表名称
        input_variables: 用户输入变量列表（如 ["user_input.skill_mult"]）
        output_names: 输出名称列表（引用 DAG outputs 的 key）
        description: 可选描述

    Returns:
        layout JSON dict
    """
    sections: list[dict[str, Any]] = []

    if input_variables:
        sections.append(
            {
                "id": "inputs",
                "type": "inputs",
                "title": "输入参数",
                "variables": input_variables,
            }
        )

    if output_names:
        sections.append(
            {
                "id": "results",
                "type": "outputs",
                "title": "计算结果",
                "outputs": output_names,
            }
        )

    layout: dict[str, Any] = {
        "schema_version": "ui-v1",
        "name": name,
        "sections": sections,
    }
    if description:
        layout["description"] = description
    return layout


def layout_to_json(
    name: str,
    input_variables: list[str],
    output_names: list[str],
    *,
    description: str = "",
) -> str:
    """生成格式化的 layout.json 字符串。"""
    return json.dumps(
        build_layout(name, input_variables, output_names, description=description),
        ensure_ascii=False,
        indent=2,
    )
