# SPDX-License-Identifier: AGPL-3.0
"""明日方舟 Web API。"""

from __future__ import annotations

from api.internal.json_utils import ADAPTER_ROOT
from calc_framework.config.manager import AdapterManager
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from games.arknights.calc.dag_adapter import compute_snapshot_with_dag
from games.arknights.operator_catalog import (
    build_operator_index,
    load_operators_map,
)

router = APIRouter(prefix="/api/arknights", tags=["arknights"])

ADAPTER_MANAGER = AdapterManager(ADAPTER_ROOT)

_OPERATORS_MAP: dict | None = None
_OPERATOR_INDEX_CACHE: list[dict] | None = None


def _operators_map() -> dict:
    global _OPERATORS_MAP
    if _OPERATORS_MAP is None:
        _OPERATORS_MAP = load_operators_map()
        if not _OPERATORS_MAP:
            raise HTTPException(
                status_code=500,
                detail="干员数据不存在：请放置 parsed/*.json 或 arknights_parsed.zip",
            )
    return _OPERATORS_MAP


def _load_operator(name: str) -> dict:
    safe = name.strip()
    m = _operators_map()
    if safe in m:
        return m[safe]
    for data in m.values():
        if str(data.get("名称")) == safe:
            return data
    raise HTTPException(status_code=404, detail=f"干员不存在: {name}")


def _build_operator_index() -> list[dict]:
    global _OPERATOR_INDEX_CACHE
    if _OPERATOR_INDEX_CACHE is not None:
        return _OPERATOR_INDEX_CACHE
    _OPERATOR_INDEX_CACHE = build_operator_index(_operators_map())
    return _OPERATOR_INDEX_CACHE


class ComputeRequest(BaseModel):
    operator_name: str
    skill_multiplier: float | None = None
    skill_level: int = 7
    enemy_def: float = 200.0
    enemy_res: float = 50.0
    atk_percent_bonus: float = 0.0
    dmg_bonus: float = 0.0
    def_penetration: float = 0.0
    res_penetration: float = 0.0


class ComputeResponse(BaseModel):
    operator_name: str
    final_atk: float
    physical_damage: float
    magical_damage: float
    true_damage: float
    execution_count: int


def list_operators_payload() -> dict:
    index = _build_operator_index()
    names = [row["名称"] for row in index]
    return {"operators": names, "index": index, "count": len(names)}


def operator_summary_payload(name: str) -> dict:
    data = _load_operator(name)
    return {
        "名称": data.get("名称"),
        "星级": data.get("星级"),
        "职业": data.get("职业"),
        "分支": data.get("分支"),
        "特性": data.get("特性"),
        "基础属性": data.get("基础属性"),
        "信赖加成": data.get("信赖加成"),
        "天赋": data.get("天赋"),
        "技能": data.get("技能"),
        "潜能": data.get("潜能"),
    }


def compute_damage_payload(req: ComputeRequest) -> ComputeResponse:
    """执行 DAG 快照计算并返回各项伤害。"""
    operator = _load_operator(req.operator_name)
    try:
        result = compute_snapshot_with_dag(
            operator,
            skill_level=req.skill_level,
            skill_multiplier=req.skill_multiplier,
            enemy_def=req.enemy_def,
            enemy_res=req.enemy_res,
            atk_percent_bonus=req.atk_percent_bonus,
            dmg_bonus=req.dmg_bonus,
            def_penetration=req.def_penetration,
            res_penetration=req.res_penetration,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"计算失败: {e}") from e

    return ComputeResponse(
        operator_name=req.operator_name,
        final_atk=result.outputs.get("最终攻击力", 0.0),
        physical_damage=result.outputs.get("物理伤害", 0.0),
        magical_damage=result.outputs.get("法术伤害", 0.0),
        true_damage=result.outputs.get("真伤伤害", 0.0),
        execution_count=len(result.execution_order),
    )


@router.get("/operators")
def list_operators():
    """获取所有明日方舟干员列表。"""
    return list_operators_payload()


@router.get("/operators/{name}")
def get_operator(name: str):
    """获取指定干员的详细属性。"""
    return operator_summary_payload(name)


@router.post("/compute", response_model=ComputeResponse)
def compute_damage(req: ComputeRequest):
    """计算指定干员的技能伤害。"""
    return compute_damage_payload(req)


__all__: list[str] = []
