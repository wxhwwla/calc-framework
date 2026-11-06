# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""viewer_evaluator — CalcPackViewer 纯逻辑提取（无 PySide6 依赖）。

从 viewer_render.py 的 _build_current_context() 提取的纯函数：
将实体数据 + 等级 + 变量声明组装为 DAG context 字典。
可被 Web / CLI / 测试直接复用。
"""

from __future__ import annotations

from typing import Any

from .viewer_pack_utils import _FALLBACK_DEFAULTS, build_context_from_entity


def build_viewer_context(
    entity_selectors: dict[str, Any],
    entity_data: dict[str, dict[str, dict[str, Any]]],
    variables: dict[str, Any],
    level: int = 90,
) -> dict[str, Any]:
    """根据当前选中的实体和等级构建 DAG context，缺失变量使用默认值。

    从 viewer_render.py CalcPackViewerRenderMixin._build_current_context() 提取。
    不依赖任何 PySide6 类型。

    参数：
        entity_selectors: {source_prefix: selected_name} 当前选中的实体名称。
        entity_data: {source_prefix: {name: entity_dict}} 全量实体数据。
        variables: DAG 变量声明字典（path → DAGVariable）。
        level: 等级，默认 90。

    返回：
        DAG context 字典，如 {"character": {"攻击力": 123}, "weapon": {...}}。
    """
    ctx: dict[str, Any] = {}

    for source_prefix, name in entity_selectors.items():
        entity = entity_data.get(source_prefix, {}).get(name)
        if entity:
            ns = source_prefix
            ns_ctx = build_context_from_entity(entity, ns, level)
            ctx[ns] = ns_ctx

    for path, var in variables.items():
        parts = path.split(".", 1)
        if len(parts) != 2:
            continue
        ns, key = parts
        if ns not in ctx:
            ctx[ns] = {}
        if isinstance(ctx.get(ns), dict) and key not in ctx[ns]:
            default = var.default if var.default is not None else _FALLBACK_DEFAULTS.get(key, 0.0)
            ctx[ns][key] = default

    return ctx


def build_entity_status_text(
    entity_selectors: dict[str, Any],
    selected_names: dict[str, str],
    level: int | None = None,
) -> str:
    """构建实体选择状态文案（用于状态栏显示）。

    参数：
        entity_selectors: {source_prefix: selected_name} 当前选中的实体。
        selected_names: 已选中的 {source: name} 映射。
        level: 当前等级；``None`` 表示该计算包没有等级概念，状态栏不显示 Lv。

    返回：
        如 "character=艾拉, weapon=天弓 Lv.90" 或 "weapon=…" 的状态文案。
    """
    selected = []
    for src, name in entity_selectors.items():
        if name:
            selected.append(f"{src}={name}")
    suffix = f" Lv.{level}" if level is not None else ""
    return f"已求值 — {', '.join(selected) if selected else '自定义输入'}{suffix}"
