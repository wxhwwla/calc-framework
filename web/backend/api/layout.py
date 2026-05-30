import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/layout", tags=["layout"])

ADAPTER_ROOT = Path(__file__).resolve().parents[3] / "framework" / "adapters" / "endfield"

_VALID_SECTION_TYPES = frozenset({"inputs", "outputs", "widget"})


def _load_json(path: Path) -> dict:
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"文件不存在: {path.name}")
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return data
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"JSON 解析失败: {path.name}: {e}")


@router.get("", summary="获取当前适配器 layout.json")
async def get_layout():
    """返回终末地适配器的 layout.json（ComputeSheet 排版描述）。"""
    layout_path = ADAPTER_ROOT / "ui" / "layout.json"
    return _load_json(layout_path)


@router.get("/variables", summary="获取 DAG variables 定义")
async def get_variables():
    """返回 DAG 中所有 variables 的完整定义。"""
    dag_path = (
        Path(__file__).resolve().parents[3]
        / "framework" / "src" / "calc_framework" / "configs" / "endfield_full.dag.json"
    )
    dag = _load_json(dag_path)
    variables = dag.get("variables", {})
    return variables


@router.get("/schema", summary="获取 attr_schema.json")
async def get_attr_schema():
    """返回适配器的 attr_schema.json（属性字段声明）。"""
    schema_path = ADAPTER_ROOT / "attr_schema.json"
    return _load_json(schema_path)


@router.get("/dag", summary="获取完整 DAG JSON")
async def get_dag():
    """返回终末地 15 乘区完整 DAG JSON。"""
    dag_path = (
        Path(__file__).resolve().parents[3]
        / "framework" / "src" / "calc_framework" / "configs" / "endfield_full.dag.json"
    )
    return _load_json(dag_path)


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
            issues.append(ValidationIssue(severity="error", section_id=sid, field="type", message=f"无效 section type: {stype!r}，必须是 {_VALID_SECTION_TYPES}"))

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
                    issues.append(ValidationIssue(severity="error", section_id=sid, field="variables", message=f"变量 {v!r} 既不在 DAG variables 中，也不在 attr_schema 或 user_input 中"))

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
        issues.append(ValidationIssue(severity="info", message=f"layout 未覆盖 {len(uncovered)}/{total_vars} 个 DAG variables: {', '.join(sorted(uncovered)[:10])}"))

    if used_outputs < total_outputs:
        uncovered = set(dag_outputs.keys()) - referenced_outputs
        issues.append(ValidationIssue(severity="info", message=f"layout 未覆盖 {len(uncovered)}/{total_outputs} 个 DAG outputs: {', '.join(sorted(uncovered)[:10])}"))

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
async def validate_layout():
    """加载 layout.json 与 DAG，校验结构完整性。

    检查项：
    - 所有 section 是否包含 id/type/title
    - section type 是否合法
    - input section 引用的变量是否存在于 DAG variables
    - output section 引用的输出是否存在于 DAG outputs
    - 覆盖度统计
    """
    layout_path = ADAPTER_ROOT / "ui" / "layout.json"
    dag_path = (
        Path(__file__).resolve().parents[3]
        / "framework" / "src" / "calc_framework" / "configs" / "endfield_full.dag.json"
    )
    schema_path = ADAPTER_ROOT / "attr_schema.json"
    layout = _load_json(layout_path)
    dag = _load_json(dag_path)
    attr_schema = _load_json(schema_path) if schema_path.exists() else None
    return _validate_layout(layout, dag, attr_schema)
