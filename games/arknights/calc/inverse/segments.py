# SPDX-License-Identifier: AGPL-3.0
"""明日方舟精英阶段等级上限与段内长度。"""

from __future__ import annotations

from typing import Any

from calc_framework.inverse.curve import expand_segment_linear

ELITE_CUMULATIVE_CAPS: dict[int, dict[str, int | None]] = {
    6: {"e0": 50, "e1": 80, "e2": 90},
    5: {"e0": 50, "e1": 70, "e2": 80},
    4: {"e0": 45, "e1": 60, "e2": 70},
    3: {"e0": 40, "e1": 55, "e2": None},
    2: {"e0": 30, "e1": None, "e2": None},
    1: {"e0": 30, "e1": None, "e2": None},
}

STAT_KEYS: tuple[str, ...] = ("hp", "atk", "def", "res")

STAT_LABELS: dict[str, str] = {
    "hp": "生命",
    "atk": "攻击",
    "def": "防御",
    "res": "法抗",
}

ELITE_SEGMENT_KEYS: dict[int, str] = {0: "e0", 1: "e1", 2: "e2"}


def elite_caps(rarity: int) -> dict[str, int | None]:
    """返回指定星级的精英累计等级上限。"""
    return ELITE_CUMULATIVE_CAPS.get(int(rarity), ELITE_CUMULATIVE_CAPS[6])


def segment_length(rarity: int, elite: int) -> int:
    """段内等级数（精0/1/2 各段单独计数，从 1 起）。"""
    caps = elite_caps(rarity)
    if elite == 0:
        return int(caps["e0"] or 0)
    if elite == 1:
        e0, e1 = caps["e0"], caps["e1"]
        if e0 is None or e1 is None:
            return 0
        return int(e1 - e0)
    if elite == 2:
        e1, e2 = caps["e1"], caps["e2"]
        if e1 is None or e2 is None:
            return 0
        return int(e2 - e1)
    raise ValueError(f"elite 应为 0/1/2，实际 {elite}")


def elite_segment_key(elite: int) -> str:
    """精英段在 ``CurveBlueprint`` 中的 key（``e0`` / ``e1`` / ``e2``）。"""
    try:
        return ELITE_SEGMENT_KEYS[elite]
    except KeyError as exc:
        raise ValueError(f"elite 应为 0/1/2，实际 {elite}") from exc


def segment_endpoints(milestones: dict[str, Any], stat_key: str, elite: int) -> tuple[int, int] | None:
    """从属性里程碑 dict 取段内起止值（段内 1 级 → 段内满级）。"""
    ms = milestones.get(stat_key)
    if not isinstance(ms, dict):
        return None
    if elite == 0:
        start = ms.get("e0_lv1")
        end = ms.get("e0_max")
    elif elite == 1:
        start = ms.get("e0_max")
        end = ms.get("e1_max")
    elif elite == 2:
        start = ms.get("e1_max")
        end = ms.get("e2_max")
    else:
        raise ValueError(f"elite 应为 0/1/2，实际 {elite}")
    if start is None or end is None:
        return None
    return int(start), int(end)


__all__ = [
    "ELITE_CUMULATIVE_CAPS",
    "STAT_KEYS",
    "STAT_LABELS",
    "elite_caps",
    "elite_segment_key",
    "expand_segment_linear",
    "segment_endpoints",
    "segment_length",
]
