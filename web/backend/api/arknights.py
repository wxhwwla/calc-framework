# SPDX-License-Identifier: AGPL-3.0
"""明日方舟 Web API。"""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from calc_framework.config.manager import AdapterManager

from games.arknights.calc.dag_adapter import compute_snapshot_with_dag

router = APIRouter(prefix="/api/arknights", tags=["arknights"])

_REPO_ROOT = Path(__file__).resolve().parents[3]
_DATA_DIR = _REPO_ROOT / "tools" / "arknights_scout" / "output" / "parsed"
_ADAPTER_DIR = _REPO_ROOT / "framework" / "adapters"

ADAPTER_MANAGER = AdapterManager(_ADAPTER_DIR)


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


def _load_operator(name: str) -> dict:
    safe_name = name.strip()
    path = _DATA_DIR / f"{safe_name}.json"
    if not path.is_file():
        raise HTTPException(status_code=404, detail=f"干员不存在: {name}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail=f"干员数据损坏: {name}")


@router.get("/operators")
async def list_operators():
    if not _DATA_DIR.is_dir():
        raise HTTPException(status_code=500, detail="干员数据目录不存在")
    names = sorted(
        p.stem for p in _DATA_DIR.iterdir()
        if p.suffix == ".json" and p.stem not in ("_sync_summary", "operators")
    )
    return {"operators": names, "count": len(names)}


@router.get("/operators/{name}")
async def get_operator(name: str):
    data = _load_operator(name)
    summary = {
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
    return summary


@router.post("/compute", response_model=ComputeResponse)
async def compute_damage(req: ComputeRequest):
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
        raise HTTPException(status_code=400, detail=f"计算失败: {e}")

    return ComputeResponse(
        operator_name=req.operator_name,
        final_atk=result.outputs.get("最终攻击力", 0.0),
        physical_damage=result.outputs.get("物理伤害", 0.0),
        magical_damage=result.outputs.get("法术伤害", 0.0),
        true_damage=result.outputs.get("真伤伤害", 0.0),
        execution_count=len(result.execution_order),
    )
