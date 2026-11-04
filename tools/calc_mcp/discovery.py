# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""MCP 发现类能力：模板、适配器、DAG schema 与指南。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from calc_framework.dag.graph_types import VALID_VAR_SOURCES, VALID_VAR_TYPES
from calc_framework.dag.sandbox_config import list_function_specs

from tools.generator.data_files import DATA_FILE_BY_SOURCE, MAX_DATA_FILE_BYTES

from .safety import ProjectScope, ScopeError

_GUIDE_MAX_BYTES = 60_000

_GUIDES: dict[str, tuple[str, str]] = {
    "overview": ("完整制造流程", "docs/制造游戏计算器完整流程.md"),
    "adapter": ("适配新游戏指南", "docs/框架适配新游戏指南.md"),
    "dag": ("DAG 算法与架构", "docs/算法与架构.md"),
    "generator": ("AI 计算器生成指南", "docs/AI-计算器生成指南.md"),
    "quickstart": ("快速开始", "docs/quickstart.md"),
    "context": ("领域术语", "CONTEXT.md"),
    "pack_format": ("CalcPack 格式（ADR-0006）", "docs/adr/0006-calcpack-and-designer.md"),
    "adapter_layout": (
        "标准游戏包架构（ADR-0023）",
        "docs/adr/0023-standardized-game-package-architecture.md",
    ),
}

_SOURCE_DESCRIPTIONS = {
    "character": "角色/干员自身属性",
    "weapon": "武器属性",
    "equipment": "装备/圣遗物属性",
    "enemy": "敌人属性",
    "user_input": "用户在界面上填写的参数",
    "computed": "由其他节点计算得出",
}

_NODE_SCHEMAS: list[dict[str, Any]] = [
    {
        "type": "const",
        "description": "常量",
        "fields": {"value": "number（必填）", "label": "string"},
    },
    {
        "type": "var",
        "description": "读取 DAG 变量",
        "fields": {"path": "string，格式 source.field（必填）", "label": "string"},
    },
    {
        "type": "unary",
        "description": "一元运算",
        "fields": {
            "op": "neg|floor|ceil|abs|sqrt|ln|log10|sin|cos|tan|asin|acos|atan（必填）",
            "input": "节点 id（必填）",
        },
    },
    {
        "type": "binary",
        "description": "二元运算",
        "fields": {"op": "+|-|*|/|^|min|max|mod（必填）", "lhs": "节点 id（必填）", "rhs": "节点 id（必填）"},
    },
    {
        "type": "condition",
        "description": "条件选择（cond 非零取 true_val，否则 false_val）",
        "fields": {
            "cond": "节点 id（必填）",
            "true_val": "节点 id（必填）",
            "false_val": "节点 id（必填）",
        },
    },
    {
        "type": "expr",
        "description": "白名单表达式求值",
        "fields": {
            "expr": "string（必填），可用 + - * /、比较、and/or/not、三元、数学函数",
            "inputs": "对象 {表达式变量名: 节点 id}",
        },
    },
    {
        "type": "user_input",
        "description": "内嵌用户输入控件（生成器通常改用 var + variables）",
        "fields": {"default": "number", "min": "number", "max": "number", "step": "number"},
    },
    {
        "type": "call",
        "description": "调用子图",
        "fields": {"subgraph": "子图名（必填）", "bindings": "对象 {子图参数名: 节点 id}"},
    },
]

_FORMULA_STEP_SCHEMA: dict[str, Any] = {
    "ops": ["+", "-", "*", "/", "condition", "expr"],
    "aliases": {"add": "+", "sub": "-", "mul": "*", "div": "/", "if": "condition"},
    "op_fields": {
        "+ - * /": ["id", "op", "lhs", "rhs"],
        "condition": ["id", "op", "cond", "true_val", "false_val"],
        "expr": ["id", "op", "expr", "input_map"],
    },
    "common_fields": ["id", "op", "label"],
    "reference_rule": (
        "lhs/rhs/cond/true_val/false_val 以及 input_map 的值必须引用变量 name、步骤 id 或数字字面量"
        "（例如 'atk'、'damage'、'2'），不要填写 'user_input.atk' 这类完整路径"
    ),
}

_EXPRESSION_OPERATORS: dict[str, Any] = {
    "arithmetic": ["+", "-", "*", "/"],
    "comparison": ["<", "<=", ">", ">=", "==", "!="],
    "boolean": ["and", "or", "not"],
    "ternary": "三元 a if cond else b（cond 为真取 a，否则取 b）",
    "short_circuit": "and/or 按 Python 语义短路并返回操作数；三元只求值选中分支",
    "rejected": ["in", "not in", "is", "is not", "**", "~", "属性访问", "lambda", "列表/字典/集合"],
}

_VARIABLE_UI_SCHEMA: dict[str, Any] = {
    "fields": ["min", "max", "ui_control"],
    "min_max_rule": "min/max 是可选的数值范围，只对 float/int 生效；省略时控件不设业务上限",
    "ui_control": {
        "suffix": "字符串，显示在数值后的单位或百分号，例如 '%'",
        "step": "正数，控件的单步增量",
        "widget": ["spinbox", "slider", "switch", "dropdown"],
        "options": "非空字符串数组；提供时控件默认切换为 dropdown",
    },
    "percent_rule": (
        "百分比输入建议 type=float、default 使用 0-100 的数值，并在表达式中除以 100；"
        "加 ui_control.suffix='%' 显示百分号"
    ),
}

_ENTITY_SELECTOR_SCHEMA: dict[str, Any] = {
    "item_fields": ["source", "data_file", "steps"],
    "source_rule": "source 必须是 character/weapon/equipment/enemy，且 data_files 中该来源有非空记录",
    "data_file_rule": "可选，默认取来源的约定文件名（不含 data/ 与 .json），例如 weapon → weapons",
    "step_fields": ["field", "label", "display_field"],
    "rules": [
        "steps 必须是非空数组，按顺序逐级过滤记录",
        "field/display_field 必须能在该来源的记录中找到非空值",
        "最后一级的 field 必须是 '名称'，其值作为实体标识注入 DAG 命名空间",
        "同一来源只能出现一次",
    ],
}

_ENTITY_DETAIL_SCHEMA: dict[str, Any] = {
    "item_fields": ["source", "title", "sections"],
    "source_rule": "source 必须已绑定非空 data_files",
    "section_fields": ["title", "columns", "fields"],
    "field_fields": ["field", "label", "format"],
    "rules": [
        "sections 与每节的 fields 都必须是非空数组",
        "field 必须在该来源记录中存在（至少一条记录有非空值）",
        "columns 为 1-3 的整数，默认 1",
        "format 为可选的 Python 数值格式串，例如 '.1f'",
        "查看器在左侧面板显示当前实体的字段明细",
    ],
}

_ENTITY_INPUT_RULE_SCHEMA: dict[str, Any] = {
    "item_fields": ["source", "field", "equals", "disable", "reason"],
    "disable_rule": (
        "disable 是非空的 user_input.* 路径数组，且必须是生成后仍为 user_input 的变量；"
        "实体记录缺少 field 或值为空时规则不命中，对应输入保持可编辑"
    ),
    "reason_rule": "可选说明，禁用后显示为控件与标签的悬停提示",
    "example": {
        "source": "weapon",
        "field": "needs_mothership",
        "equals": 0,
        "disable": ["user_input.mothership_flight_bonus"],
        "reason": "该舰船不需要母舰",
    },
    "validation_rule": "validate_adapter 会把非法详情面板报为 ENTITY_DETAIL_INVALID，非法规则报为 INPUT_RULE_INVALID",
}

_DATA_FILE_SCHEMA: dict[str, Any] = {
    "allowed_sources": list(DATA_FILE_BY_SOURCE),
    "files": dict(DATA_FILE_BY_SOURCE),
    "record_rule": "每条记录必须是以字符串为键的对象，且含非空字符串 '名称'；同一文件内 '名称' 不得重复",
    "max_bytes_per_file": MAX_DATA_FILE_BYTES,
    "binding_rule": (
        "data_files 中提供非空记录列表的来源视为已绑定：其变量保留 source 命名空间、"
        "由查看器实体下拉提供，不出现在输入区；未绑定或列表为空的来源，"
        "其变量自动改写为 user_input.*（空列表会在 warnings 中提示）"
    ),
    "meta_rule": "生成器会把非空数据文件路径写入 meta.entry_data",
    "validation_rule": (
        "validate_adapter 校验 data/*.json：记录须含非空 '名称' 且同文件不重复；"
        "空文件与无法映射到实体来源的文件名仅告警；meta.entry_data 引用的文件必须存在"
    ),
}


class DiscoveryError(ValueError):
    """发现类工具错误。"""


def list_templates(scope: ProjectScope) -> dict[str, Any]:
    """列出可用作生成模板的适配器目录。

    Args:
        scope: 项目作用域。

    Returns:
        ``{templates: [{id, name, category, description, available}]}``。
    """
    templates: list[dict[str, Any]] = []
    if not scope.adapters_dir.is_dir():
        return {"templates": templates}

    for entry in sorted(scope.adapters_dir.iterdir()):
        if not entry.is_dir() or entry.name.startswith(("_", ".")):
            continue
        meta_path = entry / "meta.json"
        if not meta_path.is_file():
            continue
        meta = _read_meta(meta_path)
        templates.append(
            {
                "id": entry.name,
                "name": meta.get("name", entry.name),
                "category": meta.get("category", ""),
                "description": meta.get("description", ""),
                "available": True,
            }
        )
    return {"templates": templates}


def list_adapters(scope: ProjectScope) -> dict[str, Any]:
    """扫描适配器目录并返回摘要。

    Args:
        scope: 项目作用域。

    Returns:
        ``{adapters: [{id, name, game, version, description, entry_dag, has_layout}]}``。
    """
    adapters: list[dict[str, Any]] = []
    if not scope.adapters_dir.is_dir():
        return {"adapters": adapters}

    for entry in sorted(scope.adapters_dir.iterdir()):
        if not entry.is_dir() or entry.name.startswith(("_", ".")):
            continue
        meta_path = entry / "meta.json"
        if not meta_path.is_file():
            continue
        meta = _read_meta(meta_path)
        layout_ref = str(meta.get("ui_layout", ""))
        adapters.append(
            {
                "id": entry.name,
                "name": meta.get("name", entry.name),
                "game": meta.get("game", ""),
                "version": meta.get("version", ""),
                "description": meta.get("description", ""),
                "entry_dag": meta.get("entry_dag", ""),
                "has_layout": bool(layout_ref) and (entry / layout_ref).is_file(),
            }
        )
    return {"adapters": adapters}


def describe_schemas() -> dict[str, Any]:
    """返回 DAG / 生成器 / 表达式的机器可读 schema。

    Returns:
        包含变量、节点、布局、公式步骤与表达式函数说明的字典。
    """
    return {
        "variables": {
            "types": sorted(VALID_VAR_TYPES),
            "sources": sorted(VALID_VAR_SOURCES),
            "source_descriptions": dict(_SOURCE_DESCRIPTIONS),
            "path_rule": "变量以 source.name 作为 DAG 路径，例如 user_input.atk",
            "ui_fields": _VARIABLE_UI_SCHEMA,
        },
        "nodes": _NODE_SCHEMAS,
        "formula_steps": _FORMULA_STEP_SCHEMA,
        "outputs": {
            "fields": ["name", "node", "label", "format", "is_primary"],
            "note": "node 可引用变量 name 或步骤 id；为空时默认等于 name",
        },
        "expression_functions": list_function_specs(),
        "expression_operators": _EXPRESSION_OPERATORS,
        "data_files": _DATA_FILE_SCHEMA,
        "entity_selectors": _ENTITY_SELECTOR_SCHEMA,
        "entity_detail": _ENTITY_DETAIL_SCHEMA,
        "entity_input_rules": _ENTITY_INPUT_RULE_SCHEMA,
        "layout": {
            "schema_version": "ui-v1",
            "section_types": ["inputs", "outputs", "widget"],
            "widget_types": ["donation"],
            "section_fields": [
                "id",
                "type",
                "title",
                "variables",
                "outputs",
                "columns",
                "widget_type",
                "widget_config",
                "tab",
            ],
            "tab_rule": "tab 必须为所有 section 统一指定非空字符串，或全部省略；指定后查看器按首次出现顺序渲染为分页",
            "note": "scaffold_adapter 会自动生成基础 layout，可用 write_adapter_file 微调",
        },
    }


def read_guide(scope: ProjectScope, topic: str) -> dict[str, Any]:
    """读取白名单内的文档。

    Args:
        scope: 项目作用域。
        topic: 指南主题，见 ``_GUIDES``。

    Returns:
        ``{topic, title, path, content, truncated}``。

    Raises:
        DiscoveryError: topic 未知或文档不存在。
    """
    key = str(topic).strip().lower()
    if key not in _GUIDES:
        raise DiscoveryError(f"未知 topic: {topic!r}，可用: {', '.join(sorted(_GUIDES))}")

    title, rel = _GUIDES[key]
    try:
        path = scope.resolve(rel, must_exist=True)
    except ScopeError as exc:
        raise DiscoveryError(f"指南文件不存在: {rel}") from exc

    content, truncated = scope.read_text(path, max_bytes=_GUIDE_MAX_BYTES)
    return {
        "topic": key,
        "title": title,
        "path": rel,
        "content": content.lstrip("﻿"),
        "truncated": truncated,
    }


def _read_meta(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}
