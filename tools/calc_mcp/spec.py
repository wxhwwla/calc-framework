# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""MCP 适配器规格归一化与校验。

把 AI 提交的宽松 JSON 规格转换为 ``GeneratorEngine`` 可直接消费的
数据类，并在写盘前完成引用与冲突检查。
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from calc_framework.config.entity_meta import (
    EntityMetaError,
    normalize_entity_detail,
    normalize_entity_input_rules,
)
from calc_framework.dag.graph_types import VALID_VAR_SOURCES, VALID_VAR_TYPES
from calc_framework.dag.sandbox import MAX_EXPR_LENGTH

from tools.generator.data_files import (
    DataFileError,
    binding_warnings,
    bound_entity_sources,
    normalize_data_files,
)
from tools.generator.layout_sections import LayoutSectionsError, normalize_layout_sections
from tools.generator.selectors import SelectorError, normalize_entity_selectors
from tools.generator.variable_ui import VariableUiError, normalize_variable_ui

_SOURCE_ALIASES = {
    "input": "user_input",
    "userinput": "user_input",
    "user-input": "user_input",
}
_TYPE_ALIASES = {
    "percent": "float",
    "number": "float",
    "integer": "int",
    "boolean": "bool",
    "string": "str",
}
_OP_ALIASES = {
    "add": "+",
    "plus": "+",
    "sub": "-",
    "minus": "-",
    "mul": "*",
    "times": "*",
    "div": "/",
    "if": "condition",
    "expression": "expr",
}
_VALID_OPS = frozenset({"+", "-", "*", "/", "condition", "expr"})
_NAME_RE = re.compile(r"^[^\s./\\]{1,64}$")


class SpecError(ValueError):
    """适配器规格错误。"""


@dataclass
class VariableSpec:
    """变量声明。"""

    name: str
    type: str = "float"
    source: str = "user_input"
    default: float | bool | int | str = 0
    description: str = ""
    min_value: float | int | None = None
    max_value: float | int | None = None
    ui_control: dict[str, Any] = field(default_factory=dict)

    def to_generator_dict(self) -> dict[str, Any]:
        """转换为 ``GeneratorEngine`` 接受的字典。"""
        return {
            "name": self.name,
            "type": self.type,
            "source": self.source,
            "default": self.default,
            "description": self.description,
            "min": self.min_value,
            "max": self.max_value,
            "ui_control": dict(self.ui_control),
        }


@dataclass
class StepSpec:
    """公式步骤声明。"""

    id: str
    op: str = "+"
    lhs: str = ""
    rhs: str = ""
    cond: str = ""
    true_val: str = ""
    false_val: str = ""
    expr: str = ""
    input_map: dict[str, str] = field(default_factory=dict)
    label: str = ""

    def to_generator_dict(self) -> dict[str, Any]:
        """转换为 ``GeneratorEngine`` 接受的字典。"""
        return {
            "id": self.id,
            "op": self.op,
            "lhs": self.lhs,
            "rhs": self.rhs,
            "cond": self.cond,
            "true_val": self.true_val,
            "false_val": self.false_val,
            "expr": self.expr,
            "input_map": dict(self.input_map),
            "label": self.label,
        }


@dataclass
class OutputSpec:
    """输出声明。"""

    name: str
    node: str = ""
    label: str = ""
    format: str = ""
    is_primary: bool = True

    def to_generator_dict(self) -> dict[str, Any]:
        """转换为 ``GeneratorEngine`` 接受的字典。"""
        return {
            "name": self.name,
            "node": self.node,
            "label": self.label,
            "format": self.format,
            "is_primary": self.is_primary,
        }


@dataclass
class AdapterSpec:
    """归一化后的完整适配器规格。"""

    variables: list[VariableSpec]
    steps: list[StepSpec]
    outputs: list[OutputSpec]
    data_files: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    entity_selectors: list[dict[str, Any]] = field(default_factory=list)
    entity_detail: dict[str, Any] | None = None
    entity_input_rules: list[dict[str, Any]] = field(default_factory=list)
    layout_sections: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def normalize_spec(
    *,
    variables: list[dict[str, Any]] | None = None,
    formula_steps: list[dict[str, Any]] | None = None,
    outputs: list[dict[str, Any]] | None = None,
    data_files: dict[str, Any] | None = None,
    entity_selectors: list[dict[str, Any]] | None = None,
    entity_detail: dict[str, Any] | None = None,
    entity_input_rules: list[dict[str, Any]] | None = None,
    layout_sections: list[dict[str, Any]] | None = None,
) -> AdapterSpec:
    """归一化并校验变量/步骤/输出/数据文件/级联选择器/实体增强声明。

    Args:
        variables: 变量声明列表；可含 ``min``/``max``/``ui_control``。
        formula_steps: 公式步骤列表。
        outputs: 输出声明列表；为空时自动以最后一步生成「最终结果」。
        data_files: 实体数据文件声明，键仅允许 character/weapon/equipment/enemy。
        entity_selectors: 查看器级联选择器声明，依赖非空 data_files。
        entity_detail: 查看器实体详情面板声明，字段必须存在于已绑定数据文件。
        entity_input_rules: 条件禁用输入规则；disable 只能引用有效的
            ``user_input.*`` 变量。
        layout_sections: 自定义 layout 段落声明；为空时使用自动 layout。
            每段可指定 ``type``（inputs/outputs）、``title``、``tab``、
            ``columns``（1–3），以及 inputs 的 ``variables``/``source``
            或 outputs 的 ``outputs``。

    Returns:
        归一化后的 :class:`AdapterSpec`。

    Raises:
        SpecError: 字段缺失、类型非法、引用悬空、id 冲突或数据/选择器/实体增强非法。
    """
    warnings: list[str] = []
    try:
        var_specs = _normalize_variables(variables or [], warnings)
    except VariableUiError as exc:
        raise SpecError(str(exc)) from exc
    step_specs = _normalize_steps(formula_steps or [], warnings)

    if not var_specs:
        raise SpecError("至少需要一个变量")
    if not step_specs:
        raise SpecError("至少需要一个公式步骤")

    known_refs = _build_ref_set(var_specs, step_specs)
    _validate_id_collisions(var_specs, step_specs)
    _validate_step_refs(step_specs, known_refs)

    out_specs = _normalize_outputs(outputs or [], warnings)
    if not out_specs:
        last = step_specs[-1]
        out_specs = [OutputSpec(name="最终结果", node=last.id, label="最终结果")]
        warnings.append("未提供 outputs，已自动使用最后一步生成「最终结果」")

    for out in out_specs:
        if out.node not in known_refs:
            raise SpecError(f"输出 {out.name!r} 引用了不存在的节点: {out.node!r}")

    try:
        normalized_data_files, data_warnings = normalize_data_files(data_files)
    except DataFileError as exc:
        raise SpecError(f"data_files 无效: {exc}") from exc
    warnings.extend(data_warnings)
    warnings.extend(binding_warnings((var.source for var in var_specs), normalized_data_files))

    try:
        normalized_selectors = normalize_entity_selectors(entity_selectors, normalized_data_files)
    except SelectorError as exc:
        raise SpecError(f"entity_selectors 无效: {exc}") from exc

    try:
        normalized_detail = normalize_entity_detail(entity_detail, normalized_data_files)
    except EntityMetaError as exc:
        raise SpecError(f"entity_detail 无效: {exc}") from exc

    bound_sources = bound_entity_sources(normalized_data_files)
    user_input_paths = [
        f"user_input.{var.name}" for var in var_specs if _effective_source(var.source, bound_sources) == "user_input"
    ]
    try:
        normalized_rules = normalize_entity_input_rules(
            entity_input_rules,
            data_files=normalized_data_files,
            user_input_paths=user_input_paths,
        )
    except EntityMetaError as exc:
        raise SpecError(f"entity_input_rules 无效: {exc}") from exc

    try:
        normalized_layout_sections, layout_warnings = normalize_layout_sections(layout_sections)
        warnings.extend(layout_warnings)
    except LayoutSectionsError as exc:
        raise SpecError(f"layout_sections 无效: {exc}") from exc

    return AdapterSpec(
        variables=var_specs,
        steps=step_specs,
        outputs=out_specs,
        data_files=normalized_data_files,
        entity_selectors=normalized_selectors,
        entity_detail=normalized_detail,
        entity_input_rules=normalized_rules,
        layout_sections=normalized_layout_sections,
        warnings=warnings,
    )


def safe_node_id(name: str) -> str:
    """与 ``GeneratorEngine._safe_id`` 保持一致的节点 id 规则。"""
    return name.strip().replace(" ", "_").replace(".", "_").lower() or "unnamed"


def _effective_source(source: str, bound_sources: frozenset[str]) -> str:
    """与 ``GeneratorEngine._effective_sources`` 一致的生成后来源。"""
    if source in ("user_input", "computed") or source in bound_sources:
        return source
    return "user_input"


def _normalize_variables(raw_items: list[dict[str, Any]], warnings: list[str]) -> list[VariableSpec]:
    specs: list[VariableSpec] = []
    seen_paths: set[str] = set()

    for index, raw in enumerate(raw_items):
        if not isinstance(raw, dict):
            raise SpecError(f"variables[{index}] 必须是对象")
        data = _filter_known(
            raw,
            {"name", "type", "source", "default", "description", "min", "max", "ui_control"},
            f"variables[{index}]",
            warnings,
        )

        name = str(data.get("name", "")).strip()
        if not _NAME_RE.match(name):
            raise SpecError(f"variables[{index}] 的 name 无效: {name!r}")

        raw_source = str(data.get("source", "user_input")).strip()
        source = _SOURCE_ALIASES.get(raw_source, raw_source)
        if source not in VALID_VAR_SOURCES:
            raise SpecError(f"变量 {name!r} 的 source 无效: {raw_source!r}")

        raw_type = str(data.get("type", "float")).strip()
        var_type = _TYPE_ALIASES.get(raw_type, raw_type)
        if var_type not in VALID_VAR_TYPES:
            raise SpecError(f"变量 {name!r} 的 type 无效: {raw_type!r}")

        path = f"{source}.{name}"
        if path in seen_paths:
            raise SpecError(f"变量路径重复: {path!r}")
        seen_paths.add(path)

        min_value, max_value, ui_control = normalize_variable_ui(
            name=name,
            var_type=var_type,
            source=source,
            min_value=data.get("min"),
            max_value=data.get("max"),
            ui_control=data.get("ui_control"),
            warnings=warnings,
        )

        default = data.get("default", 0)
        specs.append(
            VariableSpec(
                name=name,
                type=var_type,
                source=source,
                default=0 if default is None else default,
                description=str(data.get("description", "")),
                min_value=min_value,
                max_value=max_value,
                ui_control=ui_control,
            )
        )

    return specs


def _normalize_steps(raw_items: list[dict[str, Any]], warnings: list[str]) -> list[StepSpec]:
    specs: list[StepSpec] = []
    seen_ids: set[str] = set()

    for index, raw in enumerate(raw_items):
        if not isinstance(raw, dict):
            raise SpecError(f"formula_steps[{index}] 必须是对象")
        data = _filter_known(
            raw,
            {"id", "op", "lhs", "rhs", "cond", "true_val", "false_val", "expr", "input_map", "label"},
            f"formula_steps[{index}]",
            warnings,
        )

        step_id = str(data.get("id", "")).strip()
        if not _NAME_RE.match(step_id):
            raise SpecError(f"formula_steps[{index}] 的 id 无效: {step_id!r}")

        raw_op = str(data.get("op", "+")).strip().lower()
        op = _OP_ALIASES.get(raw_op, raw_op)
        if op not in _VALID_OPS:
            raise SpecError(f"步骤 {step_id!r} 的 op 无效: {raw_op!r}")

        if safe_node_id(step_id) in seen_ids:
            raise SpecError(f"步骤 id 重复: {step_id!r}")
        seen_ids.add(safe_node_id(step_id))

        input_map = data.get("input_map") or {}
        if not isinstance(input_map, dict):
            raise SpecError(f"步骤 {step_id!r} 的 input_map 必须是对象")

        spec = StepSpec(
            id=step_id,
            op=op,
            lhs=str(data.get("lhs", "")),
            rhs=str(data.get("rhs", "")),
            cond=str(data.get("cond", "")),
            true_val=str(data.get("true_val", "")),
            false_val=str(data.get("false_val", "")),
            expr=str(data.get("expr", "")),
            input_map={str(k): str(v) for k, v in input_map.items()},
            label=str(data.get("label", "")),
        )
        _validate_step_shape(spec)
        specs.append(spec)

    return specs


def _validate_step_shape(step: StepSpec) -> None:
    if step.op in {"+", "-", "*", "/"}:
        missing = [name for name in ("lhs", "rhs") if not getattr(step, name)]
    elif step.op == "condition":
        missing = [name for name in ("cond", "true_val", "false_val") if not getattr(step, name)]
    else:
        missing = [] if step.expr else ["expr"]
        if len(step.expr) > MAX_EXPR_LENGTH:
            raise SpecError(f"步骤 {step.id!r} 的表达式超长（最大 {MAX_EXPR_LENGTH} 字符）")

    if missing:
        raise SpecError(f"步骤 {step.id!r} 缺少字段: {', '.join(missing)}")


def _normalize_outputs(raw_items: list[dict[str, Any]], warnings: list[str]) -> list[OutputSpec]:
    specs: list[OutputSpec] = []
    seen_names: set[str] = set()

    for index, raw in enumerate(raw_items):
        if not isinstance(raw, dict):
            raise SpecError(f"outputs[{index}] 必须是对象")
        data = _filter_known(raw, {"name", "node", "label", "format", "is_primary"}, f"outputs[{index}]", warnings)

        name = str(data.get("name", "")).strip()
        if not name:
            raise SpecError(f"outputs[{index}] 缺少 name")
        if name in seen_names:
            raise SpecError(f"输出名称重复: {name!r}")
        seen_names.add(name)

        specs.append(
            OutputSpec(
                name=name,
                node=str(data.get("node") or name),
                label=str(data.get("label", "")),
                format=str(data.get("format", "")),
                is_primary=bool(data.get("is_primary", True)),
            )
        )

    return specs


def _build_ref_set(variables: list[VariableSpec], steps: list[StepSpec]) -> set[str]:
    refs: set[str] = set()
    for var in variables:
        refs.add(var.name)
        refs.add(safe_node_id(var.name))
    for step in steps:
        refs.add(step.id)
        refs.add(safe_node_id(step.id))
    return refs


def _validate_step_refs(steps: list[StepSpec], known: set[str]) -> None:
    for step in steps:
        refs: list[str] = []
        if step.op in {"+", "-", "*", "/"}:
            refs = [step.lhs, step.rhs]
        elif step.op == "condition":
            refs = [step.cond, step.true_val, step.false_val]
        elif step.op == "expr":
            refs = list(step.input_map.values())

        for ref in refs:
            if ref in known or _is_number(ref):
                continue
            raise SpecError(f"步骤 {step.id!r} 引用了不存在的节点: {ref!r}")


def _validate_id_collisions(variables: list[VariableSpec], steps: list[StepSpec]) -> None:
    var_ids: dict[str, str] = {}
    for var in variables:
        node_id = safe_node_id(var.name)
        if node_id in var_ids:
            raise SpecError(f"变量 {var.name!r} 与 {var_ids[node_id]!r} 派生出的节点 id 相同: {node_id!r}")
        var_ids[node_id] = var.name

    for step in steps:
        node_id = safe_node_id(step.id)
        if node_id in var_ids:
            raise SpecError(f"步骤 id {step.id!r} 与变量 {var_ids[node_id]!r} 派生出的节点 id 冲突")


def _filter_known(raw: dict[str, Any], allowed: set[str], location: str, warnings: list[str]) -> dict[str, Any]:
    unknown = sorted(set(raw) - allowed)
    if unknown:
        warnings.append(f"{location} 忽略未知字段: {', '.join(unknown)}")
    return {key: value for key, value in raw.items() if key in allowed}


def _is_number(value: str) -> bool:
    try:
        float(value)
    except (TypeError, ValueError):
        return False
    return True
