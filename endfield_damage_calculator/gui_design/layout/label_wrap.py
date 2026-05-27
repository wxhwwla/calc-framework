#!/usr/bin/env python3
"""可换行标签宽度计算（纯函数，无 CustomTkinter）。"""

from __future__ import annotations


def compute_wraplength(
    container_width: int,
    *,
    viewport_width: int | None = None,
    padding: int = 24,
    min_wrap: int = 160,
) -> int:
    """
    计算标签 wraplength（像素）。

    CTkScrollableFrame 内层宽度常大于可见列宽；传入 viewport_width 时取二者较小值，
    使长文案在「计算与搜索」等窄列中仍能换行而非被横向裁切。
    """
    effective = container_width
    if viewport_width is not None and viewport_width > 0:
        if effective <= 0:
            effective = viewport_width
        else:
            effective = min(effective, viewport_width)
    if effective <= padding:
        return min_wrap
    return max(min_wrap, effective - padding)
