#!/usr/bin/env python3
"""插件敌人参数解析（敌方防御/抗性等）。"""

from __future__ import annotations

from typing import Any

from data.plugin_registry import get_plugin_registry

DEFAULT_ENEMY_DEFENSE = 100.0
DEFAULT_ENEMY_RESISTANCE = 0.0
DEFAULT_IGNORE_RESISTANCE = 0.0
DEFAULT_IMBALANCE_VULNERABILITY = 1.3
DEFAULT_IS_UNBALANCED = False


def list_plugin_enemy_choices() -> tuple[tuple[str, str], ...]:
    """
    返回 (显示名, enemy_id) 列表；首项为内置默认。

    enemy_id 为空字符串表示使用默认防御。
    """
    choices: list[tuple[str, str]] = [("默认敌人", "")]
    reg = get_plugin_registry()
    for enemy_id in reg.list_enemy_ids():
        row = reg.get_enemy(enemy_id) or {}
        label = str(row.get("名称") or enemy_id)
        defense = row.get("enemy_defense", DEFAULT_ENEMY_DEFENSE)
        choices.append((f"{label} (防{defense})", enemy_id))
    return tuple(choices)


def resolve_enemy_defense(enemy_id: str, *, default: float = DEFAULT_ENEMY_DEFENSE) -> float:
    """按插件 id 读取敌方防御；id 为空时用 default。"""
    if not (enemy_id or "").strip():
        return float(default)
    row = get_plugin_registry().get_enemy(enemy_id.strip())
    if not row:
        return float(default)
    return float(row.get("enemy_defense", default))


def resolve_enemy_resistance(enemy_id: str, *, default: float = DEFAULT_ENEMY_RESISTANCE) -> float:
    """按插件 id 读取敌方抗性百分比；id 为空时用 default。"""
    if not (enemy_id or "").strip():
        return float(default)
    row = get_plugin_registry().get_enemy(enemy_id.strip())
    if not row:
        return float(default)
    return float(row.get("enemy_resistance", default))


def resolve_ignore_resistance(enemy_id: str, *, default: float = DEFAULT_IGNORE_RESISTANCE) -> float:
    """按插件 id 读取无视抗性百分比；id 为空时用 default。"""
    if not (enemy_id or "").strip():
        return float(default)
    row = get_plugin_registry().get_enemy(enemy_id.strip())
    if not row:
        return float(default)
    return float(row.get("ignore_resistance", default))


def resolve_imbalance_vulnerability(enemy_id: str, *, default: float = DEFAULT_IMBALANCE_VULNERABILITY) -> float:
    """按插件 id 读取失衡易伤系数；id 为空时用 default。"""
    if not (enemy_id or "").strip():
        return float(default)
    row = get_plugin_registry().get_enemy(enemy_id.strip())
    if not row:
        return float(default)
    return float(row.get("imbalance_vulnerability_coeff", default))


def resolve_is_unbalanced(enemy_id: str, *, default: bool = DEFAULT_IS_UNBALANCED) -> bool:
    """按插件 id 读取是否处于失衡状态；id 为空时用 default。"""
    if not (enemy_id or "").strip():
        return default
    row = get_plugin_registry().get_enemy(enemy_id.strip())
    if not row:
        return default
    return bool(row.get("is_unbalanced", default))


def enemy_damage_context_overrides(enemy_id: str) -> dict[str, Any]:
    """返回可并入 DamageContext 的敌方参数字段。"""
    if not (enemy_id or "").strip():
        return {
            "enemy_defense": DEFAULT_ENEMY_DEFENSE,
            "enemy_resistance": DEFAULT_ENEMY_RESISTANCE,
            "ignore_resistance": DEFAULT_IGNORE_RESISTANCE,
            "imbalance_vulnerability_coeff": DEFAULT_IMBALANCE_VULNERABILITY,
            "is_unbalanced": DEFAULT_IS_UNBALANCED,
        }
    row = get_plugin_registry().get_enemy(enemy_id.strip()) or {}
    return {
        "enemy_defense": float(row.get("enemy_defense", DEFAULT_ENEMY_DEFENSE)),
        "enemy_resistance": float(row.get("enemy_resistance", DEFAULT_ENEMY_RESISTANCE)),
        "ignore_resistance": float(row.get("ignore_resistance", DEFAULT_IGNORE_RESISTANCE)),
        "imbalance_vulnerability_coeff": float(
            row.get("imbalance_vulnerability_coeff", DEFAULT_IMBALANCE_VULNERABILITY)
        ),
        "is_unbalanced": bool(row.get("is_unbalanced", DEFAULT_IS_UNBALANCED)),
    }
