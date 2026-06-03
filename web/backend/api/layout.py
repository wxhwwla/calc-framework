# SPDX-License-Identifier: AGPL-3.0
"""布局/属性/DAG JSON 读取与校验 API — 供前端渲染计算面板。"""

from pathlib import Path
from typing import Any

from api.adapter_assets import get_adapter_dag, get_adapter_layout
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from ._json_utils import ADAPTER_ROOT, load_json

router = APIRouter(prefix="/api/layout", tags=["layout"])

DEFAULT_ADAPTER = "endfield"
_LOCAL_ADAPTER_ROOT = ADAPTER_ROOT / DEFAULT_ADAPTER

_VALID_SECTION_TYPES = frozenset({"inputs", "outputs", "widget"})


def get_layout_payload(adapter_id: str = DEFAULT_ADAPTER) -> dict:
    """返回适配器 layout.json（WSGI / FastAPI 共用）。"""
    if adapter_id == DEFAULT_ADAPTER:
        try:
            return get_adapter_layout(adapter_id)
        except HTTPException:
            pass
    return get_adapter_layout(adapter_id)


def get_variables_payload(adapter_id: str = DEFAULT_ADAPTER) -> dict:
    """返回 DAG variables 定义（WSGI / FastAPI 共用）。"""
    dag = get_adapter_dag(adapter_id)
    return dag.get("variables", {})


def get_dag_payload(adapter_id: str = DEFAULT_ADAPTER) -> dict:
    return get_adapter_dag(adapter_id)


@router.get("", summary="获取适配器 layout.json")
def get_layout(adapter: str = Query(DEFAULT_ADAPTER, description="适配器目录名")):
    return get_layout_payload(adapter)


@router.get("/variables", summary="获取 DAG variables 定义")
def get_variables(adapter: str = Query(DEFAULT_ADAPTER)):
    return get_variables_payload(adapter)


@router.get("/schema", summary="获取 attr_schema.json")
async def get_attr_schema(adapter: str = Query(DEFAULT_ADAPTER)):
    schema_path = _LOCAL_ADAPTER_ROOT / "attr_schema.json"
    if adapter != DEFAULT_ADAPTER:
        schema_path = Path(__file__).resolve().parents[3] / "framework" / "adapters" / adapter / "attr_schema.json"
    return load_json(schema_path)


@router.get("/dag", summary="获取完整 DAG JSON")
async def get_dag(adapter: str = Query(DEFAULT_ADAPTER)):
    return get_dag_payload(adapter)


class ValidationIssue(BaseModel):
    severity: str
    section_id: str | None = None
    field: str | None = None
    message: str


class LayoutValidationResult(BaseModel):
    valid: bool
    issues: list[ValidationIssue]
    stats: dict[str, int]


def _validate_layout(layout: dict[str, Any], dag: dict[str, Any], attr_schema: dict[str, Any] | None = None) -> LayoutValidationResult:
    issues: list[ValidationIssue] = []
    sections = layout.get("sections", [])
    dag_variables = dag.get("variables", {})
    dag_outputs = dag.get("outputs", {})

    attr_names: set[str] = set()
    if attr_schema:
        for attr in attr_schema.get("attributes", []):
            if isinstance(attr, dict):
                attr_names.add(attr.get("name", ""))

    if not isinstance(sections, list):
        issues.append(ValidationIssue(severity="error", message="sections 必须是数组"))
        return LayoutValidationResult(valid=False, issues=issues, stats={})

    section_types: dict[str, int] = {}
    seen_ids: set[str] = set()
    referenced_vars: set[str] = set()
    referenced_outputs: set[str] = set()

    for i, section in enumerate(sections):
        if not isinstance(section, dict):
            issues.append(ValidationIssue(severity="error", message=f"sections[{i}] 不是对象"))
            continue

        sid = section.get("id", f"<sections[{i}]>")
        stype = section.get("type", "")
        title = section.get("title", "")

        if not sid or not isinstance(sid, str):
            issues.append(ValidationIssue(severity="error", section_id=sid, message=f"sections[{i}] 缺少 id"))

        if sid in seen_ids:
            issues.append(ValidationIssue(severity="error", section_id=sid, message=f"重复的 section id: {sid}"))
        seen_ids.add(sid)

        if stype not in _VALID_SECTION_TYPES:
            issues.append(ValidationIssue(
                severity="error", section_id=sid, field="type",
                message=f"无效 section type: {stype!r}，必须是 {_VALID_SECTION_TYPES}",
            ))

        if not title:
            issues.append(ValidationIssue(severity="warning", section_id=sid, field="title", message="缺少 title"))
        section_types[stype] = section_types.get(stype, 0) + 1

        if stype == "inputs":
            variables = section.get("variables", [])
            if not variables:
                issues.append(ValidationIssue(severity="warning", section_id=sid, field="variables", message="input section 没有 variables"))
            for v in variables:
                referenced_vars.add(v)
                if v.startswith("user_input."):
                    continue
                if v in dag_variables:
                    var_def = dag_variables[v]
                    if not isinstance(var_def, dict) or "source" not in var_def:
                        issues.append(ValidationIssue(severity="warning", section_id=sid, field="variables", message=f"变量 {v!r} 定义不完整"))
                else:
                    short_name = v.split(".", 1)[1] if "." in v else v
                    if short_name in attr_names:
                        continue
                    issues.append(ValidationIssue(
                        severity="error", section_id=sid, field="variables",
                        message=f"变量 {v!r} 既不在 DAG variables 中，也不在 attr_schema 或 user_input 中",
                    ))

        if stype == "outputs":
            outputs = section.get("outputs", [])
            if not outputs:
                issues.append(ValidationIssue(severity="warning", section_id=sid, field="outputs", message="output section 没有 outputs"))
            for o in outputs:
                referenced_outputs.add(o)
                if o not in dag_outputs:
                    issues.append(ValidationIssue(severity="error", section_id=sid, field="outputs", message=f"输出 {o!r} 不在 DAG outputs 中"))

        if stype == "widget":
            widget_type = section.get("widget_type", "")
            if not widget_type:
                issues.append(ValidationIssue(severity="warning", section_id=sid, field="widget_type", message="widget section 缺少 widget_type"))

    total_vars = len(dag_variables)
    total_outputs = len(dag_outputs)
    used_vars = len(referenced_vars)
    used_outputs = len(referenced_outputs)

    if used_vars < total_vars:
        uncovered = set(dag_variables.keys()) - referenced_vars
        issues.append(ValidationIssue(
            severity="info",
            message=f"layout 未覆盖 {len(uncovered)}/{total_vars} 个 DAG variables: {', '.join(sorted(uncovered)[:10])}",
        ))

    if used_outputs < total_outputs:
        uncovered = set(dag_outputs.keys()) - referenced_outputs
        issues.append(ValidationIssue(
            severity="info",
            message=f"layout 未覆盖 {len(uncovered)}/{total_outputs} 个 DAG outputs: {', '.join(sorted(uncovered)[:10])}",
        ))

    has_error = any(i.severity == "error" for i in issues)

    return LayoutValidationResult(
        valid=not has_error,
        issues=issues,
        stats={
            "sections": len(sections),
            "inputs_sections": section_types.get("inputs", 0),
            "outputs_sections": section_types.get("outputs", 0),
            "widget_sections": section_types.get("widget", 0),
            "dag_variables": total_vars,
            "layout_variables": used_vars,
            "dag_outputs": total_outputs,
            "layout_outputs": used_outputs,
        },
    )


@router.post("/validate", summary="校验 layout.json 结构一致性")
async def validate_layout(adapter: str = Query(DEFAULT_ADAPTER)):
    layout = get_layout_payload(adapter)
    dag = get_dag_payload(adapter)
    schema_path = Path(__file__).resolve().parents[3] / "framework" / "adapters" / adapter / "attr_schema.json"
    attr_schema = load_json(schema_path) if schema_path.exists() else None
    return _validate_layout(layout, dag, attr_schema)

__all__: list[str] = []
