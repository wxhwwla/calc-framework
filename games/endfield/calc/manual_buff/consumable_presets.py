# SPDX-License-Identifier: AGPL-3.0
"""消耗品临时加成预设（NGA PART 05 节选，映射为手动 buff 条目）。"""

from __future__ import annotations

from games.endfield.calc.manual_buff.model import build_active_keys_from_counts, get_buffs_for_key, set_buffs_for_key

# (显示名, buff 条目)；数值来自 NGA 文内描述，待游戏内复核时可改此表
CONSUMABLE_PRESETS: tuple[tuple[str, tuple[dict[str, str | float], ...]], ...] = (
    (
        "铁瓶兴奋剂",
        ({"effect_type": "其他伤害加成", "value": 0.24},),
    ),
    (
        "雅各布的遗产",
        (
            {"effect_type": "其他伤害加成", "value": 0.15},
            {"effect_type": "暴击率", "value": 0.08},
        ),
    ),
)


def list_consumable_preset_names() -> tuple[str, ...]:
    return tuple(name for name, _ in CONSUMABLE_PRESETS)


def consumable_preset_buffs(name: str) -> list[dict[str, str | float]]:
    """按预设名返回 buff 条目副本。"""
    key = str(name or "").strip()
    for preset_name, entries in CONSUMABLE_PRESETS:
        if preset_name == key:
            return [dict(entry) for entry in entries]
    return []


def apply_consumable_preset_to_store(
    store: dict[str, list[dict[str, str | float]]],
    preset_name: str,
    *,
    skill_counts: dict[str, int],
    physical_abnormal_counts: dict[str, int],
    spell_abnormal_counts: dict[str, int],
    merge: bool = True,
) -> int:
    """将消耗品预设写入全部活跃段/异常键；返回写入键数。"""
    buffs = consumable_preset_buffs(preset_name)
    if not buffs:
        return 0
    keys = build_active_keys_from_counts(
        skill_counts=skill_counts,
        physical_abnormal_counts=physical_abnormal_counts,
        spell_abnormal_counts=spell_abnormal_counts,
    )
    for key in keys:
        if merge:
            merged = [dict(entry) for entry in get_buffs_for_key(store, key)]
            merged.extend(dict(entry) for entry in buffs)
            set_buffs_for_key(store, key, merged)
        else:
            set_buffs_for_key(store, key, [dict(entry) for entry in buffs])
    return len(keys)
