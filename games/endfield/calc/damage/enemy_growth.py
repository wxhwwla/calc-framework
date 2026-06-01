# SPDX-License-Identifier: AGPL-3.0
"""敌人生命/攻击成长（NGA PART 04）。

机制文建议勿对通用敌人硬算成长曲线；插件敌人可选填 ``enemy_max_hp`` 供燃烧 DoT 等承伤估算。
"""

from __future__ import annotations

from typing import Any

from games.endfield.data_loading.plugin_registry import get_plugin_registry


def resolve_enemy_max_hp(enemy_id: str, *, default: float | None = None) -> float | None:
    """按插件 id 读取敌方最大生命；未配置时返回 default。"""
    if not (enemy_id or "").strip():
        return default
    row = get_plugin_registry().get_enemy(enemy_id.strip()) or {}
    raw = row.get("enemy_max_hp", row.get("最大生命"))
    if raw is None:
        return default
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return default
    return value if value > 0.0 else default


def enemy_growth_note() -> str:
    """说明文案（G52：不内置全量成长表）。"""
    return "敌人生命/攻击成长线型未硬编码；请在插件 enemies 中填写 enemy_max_hp / enemy_defense 等实测值。"


def plugin_enemy_survival_fields(enemy_id: str) -> dict[str, Any]:
    """承伤/燃烧估算用的插件敌参摘要。"""
    if not (enemy_id or "").strip():
        return {}
    row = get_plugin_registry().get_enemy(enemy_id.strip()) or {}
    out: dict[str, Any] = {}
    hp = resolve_enemy_max_hp(enemy_id)
    if hp is not None:
        out["enemy_max_hp"] = hp
    if "enemy_defense" in row:
        out["enemy_defense"] = float(row["enemy_defense"])
    if "enemy_resistance" in row:
        out["enemy_resistance"] = float(row["enemy_resistance"])
    tier = row.get("enemy_tier") or row.get("等阶")
    if tier:
        out["enemy_tier"] = str(tier)
    return out
