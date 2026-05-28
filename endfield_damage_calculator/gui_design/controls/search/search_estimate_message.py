#!/usr/bin/env python3
"""搜索预估消息文案。"""

from __future__ import annotations


def compose_search_estimate_message(
    *,
    total_combinations: int,
    weapon_count: int,
    equipment_message: str = "",
) -> str:
    parts = [f"预计组合数：{total_combinations:,}"]
    parts.append(f"（{weapon_count} 武器 × 装备组合）")
    if equipment_message:
        parts.append(equipment_message)
    return " ".join(parts)
