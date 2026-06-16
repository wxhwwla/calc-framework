#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""Web 配装 context  enrichment：装备词条 + manual_buff + 额外暴击/技能倍率。"""

from __future__ import annotations

from typing import Any

from games.endfield.calc.damage.engine import DamageEffect
from games.endfield.calc.equipment.affix import aggregate_loadout_modifiers
from games.endfield.calc.equipment.system import build_four_slot_loadout, build_runtime_equipment_from_local_record
from games.endfield.data_loading.web_loadout_bridge import resolve_fixed_loadout_selection

_EMPTY_SLOT: dict[str, Any] = {
    "名称": "",
    "效果": [],
    "flat_stats": {},
    "套装": "",
    "三件套效果": [],
}


def _empty_slot(kind: str) -> dict[str, Any]:
    return {
        **_EMPTY_SLOT,
        "装备种类": kind,
        "部位": kind,
    }


def _runtime_equipment_row(row: dict[str, Any] | None) -> dict[str, Any]:
    if not row:
        return dict(_EMPTY_SLOT)
    if isinstance(row.get("flat_stats"), dict) or any(isinstance(e, DamageEffect) for e in (row.get("效果") or [])):
        return row
    return build_runtime_equipment_from_local_record(row)


def resolve_equipment_modifiers(
    *,
    fixed_equipment_names: dict[str, Any] | None,
    equipment_catalog: dict[str, list[dict[str, Any]]] | None,
    fixed_loadout_raw: dict[str, Any] | None = None,
) -> tuple[list[DamageEffect], dict[str, float], float]:
    """固定配装 → (效果列表, 平铺属性, 攻击力% 小数)。"""
    catalog = equipment_catalog or {}
    if not catalog and not fixed_equipment_names and not fixed_loadout_raw:
        return [], {}, 0.0
    fixed = resolve_fixed_loadout_selection(
        fixed_equipment_names=fixed_equipment_names,
        equipment_catalog=catalog,
        fixed_loadout_raw=fixed_loadout_raw,
    )
    if not any((fixed.chest, fixed.gloves, fixed.accessory_a, fixed.accessory_b)):
        return [], {}, 0.0
    loadout = build_four_slot_loadout(
        chest=_runtime_equipment_row(fixed.chest) if fixed.chest else _empty_slot("护甲"),
        gloves=_runtime_equipment_row(fixed.gloves) if fixed.gloves else _empty_slot("护手"),
        accessory_a=_runtime_equipment_row(fixed.accessory_a) if fixed.accessory_a else _empty_slot("配件"),
        accessory_b=_runtime_equipment_row(fixed.accessory_b) if fixed.accessory_b else _empty_slot("配件"),
        allow_duplicate_accessory=True,
    )
    return aggregate_loadout_modifiers(loadout)


def iter_manual_buff_entries(
    manual_buffs: dict[str, list[dict[str, str | float]]] | None,
) -> list[dict[str, str | float]]:
    """展平全部 manual_buff 条目（zone_snapshot 聚合）。"""
    out: list[dict[str, str | float]] = []
    for entries in (manual_buffs or {}).values():
        if not isinstance(entries, list):
            continue
        for entry in entries:
            if isinstance(entry, dict) and entry.get("effect_type"):
                out.append(entry)
    return out


def _apply_zone_effect(computed: dict[str, Any], char: dict[str, Any], effect_type: str, value: float) -> None:
    """将单条效果写入 context（与 search_evaluate 乘区语义对齐）。"""
    v = float(value)
    et = str(effect_type).strip()
    if et == "暴击率":
        char["暴击率"] = float(char.get("暴击率", 0.05)) + v
    elif et == "暴击伤害":
        char["暴击伤害"] = float(char.get("暴击伤害", 0.5)) + v
    elif et in ("伤害类型加成", "技能类型伤害加成", "技能类型加成", "失衡伤害加成", "其他伤害加成", "伤害加成"):
        computed["伤害加成"] = float(computed.get("伤害加成", 1.0)) + v
    elif et == "伤害减免":
        computed["伤害减免"] = float(computed.get("伤害减免", 1.0)) * (1.0 - v)
    elif et == "增幅":
        computed["增幅"] = float(computed.get("增幅", 1.0)) + v
    elif et == "虚弱":
        computed["虚弱"] = float(computed.get("虚弱", 1.0)) * (1.0 - v)
    elif et == "庇护":
        computed["庇护"] = min(float(computed.get("庇护", 1.0)), 1.0 - v)
    elif et == "脆弱":
        computed["脆弱"] = float(computed.get("脆弱", 1.0)) + v
    elif et == "易伤":
        computed["易伤"] = float(computed.get("易伤", 1.0)) + v
    elif et == "连击增伤":
        computed["连击增伤"] = float(computed.get("连击增伤", 1.0)) + v
    elif et == "非主控减伤":
        computed["非主控减伤"] = float(computed.get("非主控减伤", 1.0)) * (1.0 - v)
    elif et == "特殊乘区":
        computed["特殊乘区"] = float(computed.get("特殊乘区", 1.0)) * v
    elif et == "无视抗性":
        computed.setdefault("无视抗性", 0.0)
        computed["无视抗性"] = float(computed.get("无视抗性", 0.0)) + v
    elif et == "抗性":
        computed["抗性"] = float(computed.get("抗性", 1.0)) + v
    elif et == "防御":
        computed["防御"] = float(computed.get("防御", 0.5)) + v
    elif et == "失衡易伤系数":
        computed["失衡易伤"] = v


def enrich_adapter_context(
    ctx: dict[str, Any],
    loadout: Any,
    *,
    equip_effects: list[DamageEffect] | None = None,
    flat_stats: dict[str, float] | None = None,
) -> dict[str, Any]:
    """在 base context 上叠加技能倍率、额外暴击、manual_buff 与装备效果。"""
    computed = ctx.setdefault("computed", {})
    char = ctx.setdefault("character", {})
    equipment = ctx.setdefault("equipment", {})
    user_input = ctx.setdefault("user_input", {})

    computed["技能倍率"] = float(getattr(loadout, "skill_multiplier", 1.0) or 1.0)

    extra_crit_rate = float(getattr(loadout, "extra_crit_rate", 0.0) or 0.0)
    extra_crit_damage = float(getattr(loadout, "extra_crit_damage", 0.0) or 0.0)
    if extra_crit_rate:
        char["暴击率"] = float(char.get("暴击率", 0.05)) + extra_crit_rate
        user_input["额外暴击率"] = extra_crit_rate
    if extra_crit_damage:
        char["暴击伤害"] = float(char.get("暴击伤害", 0.5)) + extra_crit_damage
        user_input["额外暴击伤害"] = extra_crit_damage

    stats = dict(flat_stats or {})
    equipment["攻击力平值"] = float(stats.pop("攻击力", 0.0))

    for entry in iter_manual_buff_entries(getattr(loadout, "manual_buffs", None)):
        _apply_zone_effect(
            computed,
            char,
            str(entry.get("effect_type", "")),
            float(entry.get("value", 0.0)),
        )

    for effect in equip_effects or []:
        _apply_zone_effect(computed, char, str(effect.effect_type), float(effect.value))

    return ctx
