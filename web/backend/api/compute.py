# SPDX-License-Identifier: AGPL-3.0
from pathlib import Path

from fastapi import APIRouter, HTTPException

from pydantic import BaseModel

from calc_framework.config.manager import AdapterManager



router = APIRouter(prefix="/api/compute", tags=["compute"])



ADAPTER_ROOT = Path(__file__).resolve().parents[3] / "framework" / "adapters"

_manager = AdapterManager(ADAPTER_ROOT)

_DATA = Path(__file__).resolve().parents[3] / "games" / "endfield" / "data"





class EvaluateRequest(BaseModel):

    adapter: str

    context: dict





class EvaluateResponse(BaseModel):

    outputs: dict[str, float]

    node_values: dict[str, float | str | None]

    execution_order: list[str]





@router.post("/evaluate", response_model=EvaluateResponse)

async def evaluate(req: EvaluateRequest):

    try:

        pkg = _manager.load(req.adapter)

    except KeyError as e:

        raise HTTPException(status_code=404, detail=str(e))

    except Exception as e:

        raise HTTPException(status_code=500, detail=str(e))



    try:

        result = pkg.dag_service.evaluate(req.context)

    except Exception as e:

        raise HTTPException(status_code=400, detail=str(e))



    return EvaluateResponse(

        outputs=result.outputs,

        node_values={k: v for k, v in result.node_values.items()},

        execution_order=result.execution_order,

    )





class SnapshotRequest(BaseModel):

    char_name: str

    weapon_name: str

    char_level: int = 90

    weapon_level: int = 90

    trust_level: int = 0

    skill_1_level: int = 8

    skill_2_level: int = 8

    skill_3_level: int = 8

    normal_skill_1_level: int = 1

    normal_skill_2_level: int = 1

    normal_skill_3_level: int = 0

    special_skill_1_level: int = 1

    special_skill_1_stack: int = 0

    special_skill_2_level: int = 1

    special_skill_2_stack: int = 0

    enemy_defense: float = 100.0

    enemy_resistance: float = 0.0

    ignore_resistance: float = 0.0

    imbalance_vulnerability_coeff: float = 1.3

    is_unbalanced: bool = False

    damage_component_mode: str = "skill_and_abnormal"

    extra_crit_rate: float = 0.0

    extra_crit_damage: float = 0.0





def _load_json(path: Path):

    import json

    try:

        with open(path, encoding="utf-8") as f:

            return json.load(f)

    except FileNotFoundError:

        return []



_CHARACTERS_PATH = _DATA / "characters.json"

_WEAPONS_PATH = _DATA / "weapons.json"



@router.post("/snapshot")

def snapshot(req: SnapshotRequest):

    from games.endfield.gui_design.presentation.damage_snapshot import build_damage_snapshot

    chars = _load_json(_CHARACTERS_PATH)

    char_data = next((c for c in chars if c.get("名称") == req.char_name), None)

    if not char_data:

        raise HTTPException(status_code=404, detail=f"角色不存在: {req.char_name}")

    weapons = _load_json(_WEAPONS_PATH)

    weapon_data = next((w for w in weapons if w.get("名称") == req.weapon_name), None)

    if not weapon_data:

        raise HTTPException(status_code=404, detail=f"武器不存在: {req.weapon_name}")



    skill_counts: dict[str, int] = {}

    raw_skills = char_data.get("战技倍率", [])

    conn_skills = char_data.get("连携技倍率", [])

    ult_skills = char_data.get("终结技倍率", [])

    for seg_idx in range(max(len(raw_skills), len(conn_skills), len(ult_skills))):

        for st, arr in [("战技", raw_skills), ("连携技", conn_skills), ("终结技", ult_skills)]:

            if seg_idx < len(arr) and len(arr[seg_idx]) > 0:

                key = f"{st}:{seg_idx + 1}"

                skill_counts[key] = 1



    try:

        result = build_damage_snapshot(

            char_data=char_data,

            weapon_data=weapon_data,

            char_level=req.char_level,

            weapon_level=req.weapon_level,

            trust_level=req.trust_level,

            skill_levels=(req.skill_1_level, req.skill_2_level, req.skill_3_level),

            skill_counts=skill_counts,

            use_manual_counts=False,

            normal_skill_1_level=req.normal_skill_1_level,

            normal_skill_2_level=req.normal_skill_2_level,

            normal_skill_3_level=req.normal_skill_3_level,

            special_skill_1_level=req.special_skill_1_level,

            special_skill_1_stack=req.special_skill_1_stack,

            special_skill_2_level=req.special_skill_2_level,

            special_skill_2_stack=req.special_skill_2_stack,

            enemy_defense=req.enemy_defense,

            enemy_resistance=req.enemy_resistance,

            ignore_resistance=req.ignore_resistance,

            imbalance_vulnerability_coeff=req.imbalance_vulnerability_coeff,

            is_unbalanced=req.is_unbalanced,

        )

        return dict(

            segment_damage=result.segment_damage,

            segment_counts=result.segment_counts,

            segment_totals=result.segment_totals,

            skill_type_totals=result.skill_type_totals,

            weighted_total_damage=result.weighted_total_damage,

            rotation_share_percent=result.rotation_share_percent,

            zone_share_percent=result.zone_share_percent,

            selected_skill_label=result.selected_skill_label,

        )

    except Exception as e:

        raise HTTPException(status_code=400, detail=str(e))

