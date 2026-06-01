# SPDX-License-Identifier: AGPL-3.0
"""明日方舟 Web API。"""

from __future__ import annotations

import json
import zipfile
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from calc_framework.config.manager import AdapterManager

from games.arknights.calc.dag_adapter import compute_snapshot_with_dag

router = APIRouter(prefix="/api/arknights", tags=["arknights"])

_REPO_ROOT = Path(__file__).resolve().parents[3]
_DATA_DIR = _REPO_ROOT / "tools" / "arknights_scout" / "output" / "parsed"
_AKNIGHTS_ZIP_CANDIDATES = (
    _REPO_ROOT / "tools" / "arknights_scout" / "arknights_parsed.zip",
    _REPO_ROOT / "dist_arknights_parsed.zip",
)
_ADAPTER_DIR = _REPO_ROOT / "framework" / "adapters"
_SKIP_STEMS = frozenset({"_sync_summary", "operators"})
# parsed/ 不完整时改读 zip（PA 上常见：只解压了少量英文名 JSON）
_MIN_PARSED_COUNT = 100

ADAPTER_MANAGER = AdapterManager(_ADAPTER_DIR)


def _arknights_zip_path() -> Path | None:
    for path in _AKNIGHTS_ZIP_CANDIDATES:
        if path.is_file():
            return path
    return None


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


def _names_from_parsed_dir() -> list[str]:
    if not _DATA_DIR.is_dir():
        return []
    return sorted(
        p.stem for p in _DATA_DIR.iterdir()
        if p.suffix == ".json" and p.stem not in _SKIP_STEMS
    )


def _names_from_zip() -> list[str]:
    zip_path = _arknights_zip_path()
    if zip_path is None:
        return []
    with zipfile.ZipFile(zip_path) as zf:
        return sorted(
            Path(name).stem
            for name in zf.namelist()
            if name.endswith(".json") and Path(name).stem not in _SKIP_STEMS
        )


def _resolve_operator_names() -> list[str]:
    dir_names = _names_from_parsed_dir()
    if len(dir_names) >= _MIN_PARSED_COUNT:
        return dir_names
    zip_names = _names_from_zip()
    if len(zip_names) > len(dir_names):
        return zip_names
    if dir_names:
        return dir_names
    if zip_names:
        return zip_names
    raise HTTPException(
        status_code=500,
        detail="干员数据不存在：请放置 parsed/*.json 或 arknights_parsed.zip",
    )


def _read_operator_json_bytes(raw: bytes, name: str) -> dict:
    try:
        return json.loads(raw.decode("utf-8"))
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail=f"干员数据损坏: {name}") from None


def _load_operator(name: str) -> dict:
    safe_name = name.strip()
    path = _DATA_DIR / f"{safe_name}.json"
    if path.is_file():
        return _read_operator_json_bytes(path.read_bytes(), safe_name)

    arc = f"{safe_name}.json"
    zip_path = _arknights_zip_path()
    if zip_path is not None:
        with zipfile.ZipFile(zip_path) as zf:
            if arc in zf.namelist():
                return _read_operator_json_bytes(zf.read(arc), safe_name)

    raise HTTPException(status_code=404, detail=f"干员不存在: {name}")


def list_operators_payload() -> dict:
    names = _resolve_operator_names()
    return {"operators": names, "count": len(names)}


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
    return list_operators_payload()


@router.get("/operators/{name}")
def get_operator(name: str):
    return operator_summary_payload(name)


@router.post("/compute", response_model=ComputeResponse)
def compute_damage(req: ComputeRequest):
    return compute_damage_payload(req)
