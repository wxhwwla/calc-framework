#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""单段伤害引擎（15 乘区链）。"""

from .calculate import calculate_single_hit_damage  # type: ignore[unused-import]
from .helpers import _clamp, _collect_effects, _match_scope, _resolve_crit_zone  # type: ignore[unused-import]
from .types import (
    KNOWN_EFFECT_TYPES,
    ZONE_ORDER,
    CritMode,
    DamageContext,
    DamageEffect,
    DamageResult,
)

__all__ = [
    "KNOWN_EFFECT_TYPES",
    "ZONE_ORDER",
    "CritMode",
    "DamageContext",
    "DamageEffect",
    "DamageResult",
]
