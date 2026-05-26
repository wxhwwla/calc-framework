#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""武器有条件特殊能力字段：特殊能力1 / 特殊能力2（兼容旧 特殊能力）。"""

from __future__ import annotations

from typing import Any

import re

SPECIAL_FIELD_KEYS: tuple[str, ...] = ("特殊能力1", "特殊能力2")
LEGACY_SPECIAL_KEY = "特殊能力"

_MAX_STACK_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"最多(?:可)?叠加(\d+)层"),
    re.compile(r"最多(?:可)?叠加(\d+)次"),
    re.compile(r"同名效果最多叠加(\d+)层"),
    re.compile(r"可叠加(?:至)?(\d+)层"),
    re.compile(r"叠加(?:至)?(\d+)层"),
    re.compile(r"共(\d+)层"),
)


def is_accidental_rank_multiple_curve(curve: list[float]) -> bool:
    """
    误把满档「每层%」当 base 且 growth=base，导致九档呈 base×(1..9)（如 [21,42,…,189]）。

    正确语义：九档为各精炼下「每层叠加%」，再乘叠加层数。
    """
    if len(curve) != 9:
        return False
    base = float(curve[0])
    if base <= 0:
        return False
    return all(abs(float(curve[i]) - base * (i + 1)) <= 0.01 for i in range(9))


def infer_max_stack_from_special(name: str = "", text: str = "") -> int:
    """从特殊能力名称与 Wiki/seed 条件文案推断最大叠加层数（默认 1）。"""
    combined = f"{name}\n{text}".strip()
    if not combined:
        return 1
    for pattern in _MAX_STACK_PATTERNS:
        match = pattern.search(combined)
        if match:
            return max(1, int(match.group(1)))
    return 1


def parse_special_field(field: Any) -> tuple[bool, str, list[float], int]:
    """解析单条特殊能力字段 → (启用, 名称, 九档曲线, 最大叠加层数)。"""
    if field is False or field == [False]:
        return False, "", [], 1
    if not isinstance(field, list) or len(field) < 3 or field[0] is not True:
        return False, "", [], 1
    name = field[1] if isinstance(field[1], str) else ""
    curve = field[2] if isinstance(field[2], list) else []
    if len(field) >= 4 and isinstance(field[3], int):
        max_stack = max(1, int(field[3]))
    else:
        max_stack = infer_max_stack_from_special(name)
    return True, name, [float(v) for v in curve], max_stack


def build_special_field(
    *,
    enabled: bool,
    name: str = "",
    curve: list[float] | None = None,
    max_stack: int = 1,
) -> list:
    """构造 JSON 特殊能力字段。"""
    if not enabled:
        return [False]
    out: list[Any] = [True, name, list(curve or [])]
    if max_stack > 1:
        out.append(int(max_stack))
    return out


