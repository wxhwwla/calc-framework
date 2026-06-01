# SPDX-License-Identifier: AGPL-3.0
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/survival", tags=["survival"])


class SurvivalEstimateRequest(BaseModel):
    char_data: dict[str, Any]
    weapon_data: dict[str, Any]
    char_level: int = 90
    weapon_level: int = 90
    trust_level: int = 0
    enemy_tier: str = "普通"
    imbalance_efficiency_bonus: float = 0.0
    enemy_max_hp: float | None = None
    enemy_id: str = ""
    base_heal_flat: float = 201.6
    stat_per_point: float = 0.47
    heal_efficiency: float = 0.20
    independent_heal_bonus: float = 0.30
    imbalance_gain_base: float = 10.0
    hot_resistance_percent: float = 0.0
    sp_start: float = 0.0
    sp_seconds: float = Field(5.0, ge=0.0)
    ult_start: float = 0.0
    life_steal_rate: float = Field(0.10, ge=0.0, le=1.0)


@router.post("/estimate")
def survival_estimate(req: SurvivalEstimateRequest) -> dict[str, Any]:
    from games.endfield.calc.survival.estimate import build_survival_estimate

    try:
        return build_survival_estimate(
            char_data=req.char_data,
            weapon_data=req.weapon_data,
            char_level=req.char_level,
            weapon_level=req.weapon_level,
            trust_level=req.trust_level,
            enemy_tier=req.enemy_tier,
            imbalance_efficiency_bonus=req.imbalance_efficiency_bonus,
            enemy_max_hp=req.enemy_max_hp,
            enemy_id=req.enemy_id,
            base_heal_flat=req.base_heal_flat,
            stat_per_point=req.stat_per_point,
            heal_efficiency=req.heal_efficiency,
            independent_heal_bonus=req.independent_heal_bonus,
            imbalance_gain_base=req.imbalance_gain_base,
            hot_resistance_percent=req.hot_resistance_percent,
            sp_start=req.sp_start,
            sp_seconds=req.sp_seconds,
            ult_start=req.ult_start,
            life_steal_rate=req.life_steal_rate,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
