# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""MCP 适配器校验与冒烟求值。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from calc_framework.config.adapter import AdapterPackage
from calc_framework.config.entity_meta import (
    EntityMetaError,
    normalize_entity_detail,
    normalize_entity_input_rules,
)
from calc_framework.dag.serializer import dag_from_dict
from calc_framework.data.attr_schema import AttributeSchema
from calc_framework.data.entity_sources import DATA_STEM_SOURCE
from calc_framework.ui.layout import load_layout

from tools.generator.data_files import NAME_KEY
from tools.generator.selectors import SelectorError, normalize_entity_selectors
from tools.quality.validate_layout_sync import validate_layout

from .safety import ProjectScope, ScopeError


class VerifyError(ValueError):
    """适配器校验/冒烟求值错误。"""


def validate_adapter(scope: ProjectScope, adapter_id: str) -> dict[str, Any]:
    """结构化校验适配器包，不 fail-fast。

    Args:
        scope: 项目作用域。
        adapter_id: 适配器目录名。

    Returns:
        ``{ok, adapter_id, valid, errors, warnings, stats}``。
    """
    target = scope.adapter_dir(adapter_id, must_exist=True)
    errors: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []
    stats: dict[str, int] = {}

    meta = _load_json(target / "meta.json", "meta.json", errors)
    if meta is None:
        return _result(adapter_id, errors, warnings, stats)

    if meta.get("schema_version") != "dag-v1":
        errors.append(
            _issue(
                "META_INVALID",
                f"schema_version 必须为 'dag-v1'，实际为 {meta.get('schema_version')!r}",
                "meta.json",
            )
        )

    dag_raw = _load_referenced_json(target, meta, "entry_dag", errors, required=True)
    layout_raw = _load_referenced_json(target, meta, "ui_layout", errors, required=False)
    attr_raw = _load_referenced_json(target, meta, "attr_schema", errors, required=False)

    if dag_raw is not None:
        stats.update(
            {
                "variables": len(dag_raw.get("variables", {}) or {}),
                "nodes": len(dag_raw.get("nodes", {}) or {}),
                "outputs": len(dag_raw.get("outputs", {}) or {}),
            }
        )
        try:
            dag_from_dict(json.loads(json.dumps(dag_raw)))
        except Exception as exc:
            errors.append(_issue("DAG_INVALID", f"DAG 校验失败: {exc}", str(meta.get("entry_dag", "entry_dag"))))

    if layout_raw is not None:
        sections = layout_raw.get("sections", [])
        stats["sections"] = len(sections) if isinstance(sections, list) else 0
        try:
            load_layout(layout_raw)
        except Exception as exc:
            errors.append(_issue("LAYOUT_INVALID", f"layout 校验失败: {exc}", str(meta.get("ui_layout", "layout"))))
        else:
            if dag_raw is not None:
                layout_result = validate_layout(layout_raw, dag_raw, attr_raw)
                stats["layout_issues"] = len(layout_result.get("issues", []))
                for issue in layout_result.get("issues", []):
                    target_list = errors if issue.get("severity") == "error" else warnings
                    target_list.append(
                        _issue(
                            "LAYOUT_ISSUE",
                            str(issue.get("message", "")),
                            str(meta.get("ui_layout", "layout")),
                        )
                    )

    if attr_raw is not None:
        try:
            AttributeSchema.from_dict(attr_raw)
        except Exception as exc:
            errors.append(_issue("ATTR_SCHEMA_INVALID", f"attr_schema 校验失败: {exc}", "attr_schema.json"))

    _check_functions(target, meta, errors, warnings)
    data_records = _check_data_files(target, meta, errors, warnings)
    _check_entity_selectors(meta, data_records, errors)
    _check_entity_meta(meta, data_records, dag_raw, errors)
    if not errors:
        _check_adapter_package(target, errors)

    return _result(adapter_id, errors, warnings, stats)


def smoke_test_adapter(
    scope: ProjectScope,
    adapter_id: str,
    *,
    context: dict[str, Any] | None = None,
    include_node_values: bool = False,
) -> dict[str, Any]:
    """用默认值 + 用户覆盖构建 context 并求值。

    注意：该函数会执行适配包 ``meta.json`` 中声明的 ``functions.py``。

    Args:
        scope: 项目作用域。
        adapter_id: 适配器目录名。
        context: 可选的上下文覆盖，按 ``{source: {field: value}}`` 合并。
        include_node_values: 是否返回全部节点值。

    Returns:
        ``{ok, adapter_id, outputs, executed_nodes, warnings, node_values?}``。

    Raises:
        VerifyError: 适配器不存在、加载失败或求值失败。
    """
    try:
        target = scope.adapter_dir(adapter_id, must_exist=True)
    except ScopeError as exc:
        raise VerifyError(str(exc)) from exc

    try:
        package = AdapterPackage(target)
    except Exception as exc:
        raise VerifyError(f"适配包加载失败: {exc}") from exc

    graph = package.dag_service.dag
    merged = _build_default_context(graph)
    if context:
        _deep_merge(merged, context)

    try:
        result = package.dag_service.evaluate(merged)
    except Exception as exc:
        raise VerifyError(f"求值失败: {exc}") from exc

    warnings = []
    if package.meta.get("functions"):
        warnings.append("smoke_test 已执行适配包 functions.py 中声明的自定义函数")

    payload: dict[str, Any] = {
        "ok": True,
        "adapter_id": adapter_id,
        "outputs": dict(result.outputs),
        "executed_nodes": len(result.execution_order),
        "context_used": merged,
        "warnings": warnings,
    }
    if include_node_values:
        payload["node_values"] = dict(result.node_values)
    return payload


def _result(
    adapter_id: str,
    errors: list[dict[str, str]],
    warnings: list[dict[str, str]],
    stats: dict[str, int],
) -> dict[str, Any]:
    return {
        "ok": not errors,
        "adapter_id": adapter_id,
        "valid": not errors,
        "errors": errors,
        "warnings": warnings,
        "stats": stats,
    }


def _issue(code: str, message: str, file: str) -> dict[str, str]:
    return {"code": code, "message": message, "file": file}


def _load_json(path: Path, label: str, errors: list[dict[str, str]]) -> dict[str, Any] | None:
    if not path.is_file():
        errors.append(_issue("META_MISSING", f"缺少 {label}", label))
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(_issue("META_INVALID", f"{label} 解析失败: {exc}", label))
        return None
    if not isinstance(data, dict):
        errors.append(_issue("META_INVALID", f"{label} 必须是对象", label))
        return None
    return data


def _load_referenced_json(
    target: Path,
    meta: dict[str, Any],
    key: str,
    errors: list[dict[str, str]],
    *,
    required: bool,
) -> dict[str, Any] | None:
    ref = meta.get(key)
    if not ref:
        if required:
            errors.append(_issue("META_INVALID", f"meta.json 缺少必需的 {key}", "meta.json"))
        return None

    try:
        path = _safe_join(target, str(ref))
    except VerifyError as exc:
        errors.append(_issue("FILE_MISSING", str(exc), str(ref)))
        return None

    if not path.is_file():
        errors.append(_issue("FILE_MISSING", f"{key} 文件不存在: {ref}", str(ref)))
        return None

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(_issue("FILE_INVALID", f"{ref} 解析失败: {exc}", str(ref)))
        return None
    return data if isinstance(data, dict) else None


def _check_functions(
    target: Path,
    meta: dict[str, Any],
    errors: list[dict[str, str]],
    warnings: list[dict[str, str]],
) -> None:
    functions = meta.get("functions") or {}
    if not isinstance(functions, dict):
        errors.append(_issue("META_INVALID", "meta.json 的 functions 必须是对象", "meta.json"))
        return

    for name, ref in functions.items():
        if not isinstance(ref, str):
            errors.append(_issue("META_INVALID", f"函数 {name!r} 的路径必须是字符串", "meta.json"))
            continue
        if not ref.endswith(".py"):
            warnings.append(
                _issue("FUNCTIONS_DOTTED", f"函数 {name!r} 使用点分隔导入，跳过文件检查: {ref}", "meta.json")
            )
            continue
        try:
            path = _safe_join(target, ref)
        except VerifyError as exc:
            errors.append(_issue("FILE_MISSING", str(exc), ref))
            continue
        if not path.is_file():
            errors.append(_issue("FILE_MISSING", f"函数文件不存在: {ref}", ref))


def _check_data_files(
    target: Path,
    meta: dict[str, Any],
    errors: list[dict[str, str]],
    warnings: list[dict[str, str]],
) -> dict[str, list[Any]]:
    """校验 ``data/*.json`` 与 ``meta.entry_data`` 引用。

    查看器只识别 ``DATA_STEM_SOURCE`` 中的约定文件名，并按 ``名称`` 建立实体下拉。
    对约定文件，缺失/重复名称会导致实体无法选择或选择错位，因此按错误上报；
    空文件仅告警。非约定文件（如适配包自用的 ``*_standard.json``）只做格式提示，
    不影响校验结果。

    Returns:
        ``{实体来源: 记录列表}``，供 ``entity_selectors`` 字段校验复用。
    """
    records_by_source: dict[str, list[Any]] = {}
    data_dir = target / "data"
    if data_dir.is_dir():
        for path in sorted(data_dir.glob("*.json")):
            label = path.relative_to(target).as_posix()
            recognized = path.stem in DATA_STEM_SOURCE
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                issue = _issue("DATA_INVALID", f"数据文件解析失败: {exc}", label)
                target_list = errors if recognized else warnings
                target_list.append(issue)
                continue
            if not isinstance(payload, list):
                issue = _issue("DATA_INVALID", "数据文件必须是记录数组", label)
                target_list = errors if recognized else warnings
                target_list.append(issue)
                continue
            if not recognized:
                warnings.append(_issue("DATA_UNKNOWN", f"数据文件 {label} 没有对应的实体来源，查看器会忽略", label))
                continue
            records_by_source[DATA_STEM_SOURCE[path.stem]] = payload
            if not payload:
                warnings.append(_issue("DATA_EMPTY", "数据文件为空列表，查看器不会显示该来源的实体选择", label))
            else:
                _check_data_records(payload, label, errors)

    _check_entry_data(target, meta, errors)
    return records_by_source


def _check_entity_selectors(
    meta: dict[str, Any],
    records_by_source: dict[str, list[Any]],
    errors: list[dict[str, str]],
) -> None:
    """校验 ``meta.entity_selectors`` 的结构、数据绑定与末级 ``名称`` 字段。"""
    raw = meta.get("entity_selectors")
    if raw is None:
        return
    try:
        normalize_entity_selectors(raw, records_by_source)
    except SelectorError as exc:
        errors.append(_issue("SELECTOR_INVALID", f"entity_selectors 校验失败: {exc}", "meta.json"))


def _check_entity_meta(
    meta: dict[str, Any],
    records_by_source: dict[str, list[Any]],
    dag_raw: dict[str, Any] | None,
    errors: list[dict[str, str]],
) -> None:
    """校验 ``meta.entity_detail`` 与 ``meta.entity_input_rules``。"""
    try:
        normalize_entity_detail(meta.get("entity_detail"), records_by_source)
    except EntityMetaError as exc:
        errors.append(_issue("ENTITY_DETAIL_INVALID", f"entity_detail 校验失败: {exc}", "meta.json"))

    variables = (dag_raw or {}).get("variables", {}) or {}
    user_input_paths = [
        path for path, spec in variables.items() if isinstance(spec, dict) and spec.get("source") == "user_input"
    ]
    try:
        normalize_entity_input_rules(
            meta.get("entity_input_rules"),
            data_files=records_by_source,
            user_input_paths=user_input_paths,
        )
    except EntityMetaError as exc:
        errors.append(_issue("INPUT_RULE_INVALID", f"entity_input_rules 校验失败: {exc}", "meta.json"))


def _check_data_records(records: list[Any], label: str, errors: list[dict[str, str]]) -> None:
    seen: set[str] = set()
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            errors.append(_issue("DATA_INVALID", f"第 {index + 1} 条记录必须是对象", label))
            continue
        name = record.get(NAME_KEY)
        if not isinstance(name, str) or not name.strip():
            errors.append(_issue("DATA_INVALID", f"第 {index + 1} 条记录缺少非空字符串 {NAME_KEY!r}", label))
            continue
        if name in seen:
            errors.append(_issue("DATA_INVALID", f"{NAME_KEY} 重复: {name!r}", label))
        seen.add(name)


def _check_entry_data(target: Path, meta: dict[str, Any], errors: list[dict[str, str]]) -> None:
    refs = meta.get("entry_data")
    if refs is None:
        return
    if not isinstance(refs, list) or not all(isinstance(ref, str) for ref in refs):
        errors.append(_issue("META_INVALID", "meta.json 的 entry_data 必须是字符串数组", "meta.json"))
        return
    for ref in refs:
        try:
            path = _safe_join(target, ref)
        except VerifyError as exc:
            errors.append(_issue("FILE_MISSING", str(exc), ref))
            continue
        if not path.is_file():
            errors.append(_issue("FILE_MISSING", f"entry_data 引用的文件不存在: {ref}", ref))


def _check_adapter_package(target: Path, errors: list[dict[str, str]]) -> None:
    try:
        AdapterPackage(target)
    except Exception as exc:
        errors.append(_issue("ADAPTER_LOAD_FAILED", f"适配包加载失败: {exc}", "meta.json"))


def _safe_join(base: Path, rel: str) -> Path:
    candidate = Path(rel)
    if candidate.is_absolute() or candidate.drive:
        raise VerifyError(f"不允许绝对路径: {rel!r}")
    resolved = (base / candidate).resolve()
    if not resolved.is_relative_to(base.resolve()):
        raise VerifyError(f"路径越界: {rel!r}")
    return resolved


def _build_default_context(graph: Any) -> dict[str, dict[str, Any]]:
    context: dict[str, dict[str, Any]] = {}
    for path, var in graph.variables.items():
        parts = path.split(".")
        if len(parts) != 2:
            continue
        section, field = parts
        default = var.default if var.default is not None else _zero_value(var.type)
        context.setdefault(section, {})[field] = default
    return context


def _zero_value(var_type: str) -> Any:
    if var_type == "int":
        return 0
    if var_type == "bool":
        return False
    if var_type == "str":
        return ""
    return 0.0


def _deep_merge(target: dict[str, Any], source: dict[str, Any]) -> None:
    for key, value in source.items():
        if isinstance(value, dict) and isinstance(target.get(key), dict):
            _deep_merge(target[key], value)
        else:
            target[key] = value
