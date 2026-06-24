#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# SPDX-License-Identifier: AGPL-3.0
"""搜索预估相关中性文案格式化（无 GUI 依赖）。"""

from __future__ import annotations


def format_duration_human(seconds: float) -> str:
    """将秒数格式化为中文可读时长。"""

    total = max(0, int(seconds))

    if total < 1:
        return "少于 1 秒"

    if total < 60:
        return f"约 {total} 秒"

    minutes, sec = divmod(total, 60)

    if minutes < 60:
        if sec > 0:
            return f"约 {minutes} 分 {sec} 秒"

        return f"约 {minutes} 分钟"

    hours, minutes = divmod(minutes, 60)

    if minutes > 0:
        return f"约 {hours} 小时 {minutes} 分"

    return f"约 {hours} 小时"


def format_workload_estimate_line(*, workload, duration) -> str:
    """生成「预计组合数/耗时」文案（workload / duration 为 search_estimate 数据类）。"""

    total = workload.total_combinations

    if total <= 0:
        return "预计组合数：0（请检查候选范围与装备数据）"

    human = format_duration_human(duration.estimated_seconds)

    return (
        f"预计组合数：{total:,}\n"
        f"（{workload.weapon_count} 武器 × {workload.loadout_combinations:,} 配装）\n"
        f"预计耗时：{human}\n"
        f"（{duration.max_workers} 线程，仅供参考）"
    )
