# SPDX-License-Identifier: AGPL-3.0
"""生存能力预估 API。"""

from typing import Any

from api.internal.errors import raise_http_from_exc
from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/survival", tags=["survival"])


class SurvivalEstimateRequest(BaseModel):
    """生存能力预估请求体。"""

    char_data: dict[str, Any] = Field(description="角色数据")
    weapon_data: dict[str, Any] = Field(description="武器数据")
    char_level: int = Field(default=90, description="角色等级")
    weapon_level: int = Field(default=90, description="武器等级")
    trust_level: int = Field(default=0, description="信赖等级")
    enemy_tier: str = Field(default="普通", description="敌方等级")
    imbalance_efficiency_bonus: float = Field(default=0.0, description="失衡效率加成")
    enemy_max_hp: float | None = Field(default=None, description="敌人最大 HP")
    enemy_id: str = Field(default="", description="敌人 ID")
    base_heal_flat: float = Field(default=201.6, description="基础治疗量")
    stat_per_point: float = Field(default=0.47, description="每点属性治疗成长")
    heal_efficiency: float = Field(default=0.20, description="治疗效率")
    independent_heal_bonus: float = Field(default=0.30, description="独立治疗加成")
    imbalance_gain_base: float = Field(default=10.0, description="失衡收益基数")
    hot_resistance_percent: float = Field(default=0.0, description="HOT 抗性百分比")
    sp_start: float = Field(default=0.0, description="初始 SP")
    sp_seconds: float = Field(default=5.0, ge=0.0, description="SP 回复秒数")
    ult_start: float = Field(default=0.0, description="初始大招能量")
    life_steal_rate: float = Field(default=0.10, ge=0.0, le=1.0, description="生命窃取率")


@router.post("/estimate")
def survival_estimate(req: SurvivalEstimateRequest) -> dict[str, Any]:
    """执行生存能力预估计算。"""
    from games.endfield.calc.survival.estimate import build_survival_estimate
    from web.backend.data_materialize import prepare_character_for_compute, prepare_weapon_for_compute

    try:
        return build_survival_estimate(
            char_data=prepare_character_for_compute(req.char_data),
            weapon_data=prepare_weapon_for_compute(req.weapon_data),
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
        raise_http_from_exc(exc, status_code=400)


__all__: list[str] = []
