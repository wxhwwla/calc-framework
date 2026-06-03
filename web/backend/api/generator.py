# SPDX-License-Identifier: AGPL-3.0
"""AI 计算器生成器 API。"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/generator", tags=["generator"])

# 导入生成器引擎
try:
    from tools.generator import GeneratorEngine, list_templates as list_gen_templates

    engine = GeneratorEngine()
    _HAS_ENGINE = True
except ImportError:
    engine = None
    _HAS_ENGINE = False


class FormulaStep(BaseModel):
    id: str
    op: str  # + - * / condition expr
    lhs: str = ""
    rhs: str = ""
    cond: str = ""
    true_val: str = ""
    false_val: str = ""
    expr: str = ""
    input_map: dict[str, str] = {}
    label: str = ""


class VariableDef(BaseModel):
    name: str
    type: str = "float"
    source: str = "user_input"
    default: float | bool = 0
    description: str = ""


class OutputDef(BaseModel):
    name: str
    node: str = ""
    label: str = ""
    format: str = ""
    is_primary: bool = True


class GenerateRequest(BaseModel):
    template_id: str
    game_name: str
    variables: list[VariableDef] = []
    formula_steps: list[FormulaStep] = []
    outputs: list[OutputDef] = []


@router.get("/templates")
def get_templates():
    """获取所有可用模板。"""
    if not _HAS_ENGINE:
        # fallback: 读取目录
        adapters_dir = Path(__file__).resolve().parents[2] / "framework" / "adapters"
        templates = {}
        for d in adapters_dir.iterdir():
            if d.is_dir() and not d.name.startswith("_"):
                meta_fp = d / "meta.json"
                if meta_fp.exists():
                    meta = json.loads(meta_fp.read_text(encoding="utf-8"))
                    templates[d.name] = {
                        "name": meta.get("name", d.name),
                        "description": meta.get("description", ""),
                    }
        return templates
    return list_gen_templates()


@router.get("/templates/{template_id}")
def get_template_detail(template_id: str):
    """获取模板详情，包括文件结构预览。"""
    adapters_dir = Path(__file__).resolve().parents[2] / "framework" / "adapters"
    d = adapters_dir / template_id
    if not d.is_dir():
        raise HTTPException(status_code=404, detail=f"模板不存在: {template_id}")

    meta_fp = d / "meta.json"
    if not meta_fp.exists():
        raise HTTPException(status_code=404, detail="模板缺少 meta.json")

    meta = json.loads(meta_fp.read_text(encoding="utf-8"))
    info: dict[str, Any] = {
        "id": template_id,
        "meta": meta,
        "files": [f.name for f in d.iterdir() if f.is_file()],
    }

    # 读取 ui/ 子目录文件
    ui_dir = d / "ui"
    if ui_dir.is_dir():
        info["files"].extend([f"ui/{f.name}" for f in ui_dir.iterdir()])

    # 读取 dag 预览
    entry_dag = meta.get("entry_dag", "")
    if entry_dag:
        dag_paths = [d / entry_dag, d / "dag" / entry_dag]
        for dp in dag_paths:
            if dp.exists():
                dag = json.loads(dp.read_text(encoding="utf-8"))
                info["dag_preview"] = {
                    "variables": len(dag.get("variables", {})),
                    "nodes": len(dag.get("nodes", {})),
                    "outputs": len(dag.get("outputs", {})),
                }
                break

    return info


@router.post("/generate")
def generate_adapter(req: GenerateRequest):
    """生成适配器包。"""
    if not _HAS_ENGINE:
        raise HTTPException(status_code=500, detail="生成器引擎不可用")

    try:
        variables = [v.model_dump() for v in req.variables]
        steps = [s.model_dump() for s in req.formula_steps]
        outputs = [o.model_dump() for o in req.outputs]

        with tempfile.TemporaryDirectory() as tmpdir:
            files = engine.generate(
                req.template_id,
                req.game_name,
                variables=variables if variables else None,
                formula_steps=steps if steps else None,
                outputs=outputs if outputs else None,
                output_dir=tmpdir,
            )

            # 读取生成的文件内容
            result = {}
            for filepath, content in files.items():
                result[filepath] = content

            return {
                "success": True,
                "files": result,
                "file_count": len(result),
            }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
