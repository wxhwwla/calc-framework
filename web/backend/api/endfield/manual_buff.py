# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""手动 Buff / 异常状态矩阵 / 消耗品预设 API。"""

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/manual-buff", tags=["manual-buff"])


@router.get("/zone-options")
def list_zone_options() -> list[dict[str, str]]:
    from games.endfield.calc.manual_buff.model import MANUAL_BUFF_ZONE_OPTIONS

    return [{"label": label, "id": zone_id} for label, zone_id in MANUAL_BUFF_ZONE_OPTIONS]


@router.get("/abnormal-matrix-specs")
def abnormal_matrix_specs() -> dict[str, Any]:
    from games.endfield.calc.manual_buff.abnormal_matrix import (
        ABNORMAL_MATRIX_HINT,
        matrix_column_labels,
        physical_abnormal_matrix_specs,
        spell_abnormal_matrix_specs,
    )

    def _rows(specs):
        return [
            {
                "label": spec.label,
                "abnormal_key": spec.abnormal_key,
                "ui_levels": list(spec.ui_levels),
            }
            for spec in specs
        ]

    return {
        "hint": ABNORMAL_MATRIX_HINT,
        "column_labels": list(matrix_column_labels()),
        "physical": _rows(physical_abnormal_matrix_specs()),
        "spell": _rows(spell_abnormal_matrix_specs()),
    }


@router.get("/consumable-presets")
def list_consumable_presets() -> list[dict[str, object]]:
    """获取消耗品预设列表（名称 + 效果条目）。"""
    from games.endfield.calc.manual_buff.consumable_presets import (
        CONSUMABLE_PRESETS,
        list_consumable_preset_names,
    )

    names = list_consumable_preset_names()
    return [
        {
            "name": name,
            "entries": [
                {"effect_type": entry["effect_type"], "value": float(entry["value"])}
                for entry in next(entries for n, entries in CONSUMABLE_PRESETS if n == name)
            ],
        }
        for name in names
    ]


class ActiveKeysRequest(BaseModel):
    """活跃 Buff key 计算请求体。"""

    manual_counts: dict[str, int] = Field(default_factory=dict, description="手动技能计数")
    physical_abnormal_counts: dict[str, int] = Field(default_factory=dict, description="物理异常层数")
    spell_abnormal_counts: dict[str, int] = Field(default_factory=dict, description="法术异常层数")


@router.post("/active-keys")
def active_keys(req: ActiveKeysRequest) -> dict[str, list[str]]:
    """基于计数返回活跃的 Buff key 列表。"""
    from games.endfield.calc.manual_buff.model import build_active_keys_from_counts

    keys = build_active_keys_from_counts(
        skill_counts=req.manual_counts,
        physical_abnormal_counts=req.physical_abnormal_counts,
        spell_abnormal_counts=req.spell_abnormal_counts,
    )
    return {"keys": keys}


class ApplyConsumableRequest(ActiveKeysRequest):
    preset_name: str
    merge: bool = True
    store: dict[str, list[dict[str, str | float]]] = Field(default_factory=dict)


@router.post("/apply-consumable")
def apply_consumable(req: ApplyConsumableRequest) -> dict[str, Any]:
    from games.endfield.calc.manual_buff.consumable_presets import apply_consumable_preset_to_store

    store = {k: [dict(e) for e in v] for k, v in req.store.items()}
    count = apply_consumable_preset_to_store(
        store,
        req.preset_name,
        skill_counts=req.manual_counts,
        physical_abnormal_counts=req.physical_abnormal_counts,
        spell_abnormal_counts=req.spell_abnormal_counts,
        merge=req.merge,
    )
    return {"store": store, "keys_written": count}


__all__: list[str] = []
