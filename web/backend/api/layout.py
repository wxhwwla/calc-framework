import json
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/layout", tags=["layout"])

ADAPTER_ROOT = Path(__file__).resolve().parents[3] / "framework" / "adapters" / "endfield"


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
