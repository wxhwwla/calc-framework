#!/usr/bin/env python3
"""手动场外 buff 数据模型。"""

from __future__ import annotations

from dataclasses import dataclass

MANUAL_BUFF_ZONE_OPTIONS: tuple[tuple[str, str], ...] = (
    ("暴击率", "crit_rate"),
    ("暴击伤害", "crit_damage"),
    ("伤害类型加成", "damage_bonus_type"),
    ("技能类型加成", "damage_bonus_skill"),
    ("失衡伤害加成", "damage_bonus_imbalance"),
    ("其他伤害加成", "damage_bonus_other"),
    ("增幅", "amplification"),
    ("脆弱", "fragile"),
    ("易伤", "vulnerability"),
    ("伤害减免", "damage_reduction"),
    ("连击增伤", "combo_bonus"),
    ("特殊乘区", "special_zone"),
)


@dataclass
class ManualBuffEntry:
    effect_type: str
    value: float


def empty_buff_dict() -> dict[str, list[dict[str, float]]]:
    return {}


def get_buffs_for_key(
    store: dict[str, list[dict[str, float]]],
    key: str,
) -> list[dict[str, float]]:
    return list(store.get(key, []))


def set_buffs_for_key(
    store: dict[str, list[dict[str, float]]],
    key: str,
    entries: list[dict[str, float]],
) -> None:
    if entries:
        store[key] = [dict(e) for e in entries]
    else:
        store.pop(key, None)


def build_active_keys_from_counts(
    *,
    skill_counts: dict[str, int],
    physical_abnormal_counts: dict[str, int],
    spell_abnormal_counts: dict[str, int],
) -> list[str]:
    """从次数统计生成全部 "键:次数" keys，按展示顺序排列。"""
    result: list[str] = []

    segment_order = {"战技": 0, "连携技": 1, "终结技": 2}

    def _segment_rank(key: str) -> int:
        if ":" not in key:
            return 99
        kind, _rest = key.split(":", 1)
        return segment_order.get(kind, 99)

    sorted_skills = sorted(skill_counts.items(), key=lambda kv: _segment_rank(kv[0]))
    for segment_key, count in sorted_skills:
        if count <= 0:
            continue
        for i in range(1, count + 1):
            result.append(f"{segment_key}:{i}")

    for abnormal_key, count in physical_abnormal_counts.items():
        if count <= 0:
            continue
        for i in range(1, count + 1):
            result.append(f"{abnormal_key}:{i}")

    for abnormal_key, count in spell_abnormal_counts.items():
        if count <= 0:
            continue
        for i in range(1, count + 1):
            result.append(f"{abnormal_key}:{i}")

    return result
