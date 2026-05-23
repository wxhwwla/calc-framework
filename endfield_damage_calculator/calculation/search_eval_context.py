#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""全量搜索评估上下文（角色/武器/等级，供配装逐条重算面板）。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class SearchEvalContext:
    """搜索时按配装重算最终攻击力所需数据。"""

    char_data: dict[str, Any]
    char_level: int
    weapon_level: int
    trust_level: int
    weapon_data_by_name: dict[str, dict[str, Any]]
