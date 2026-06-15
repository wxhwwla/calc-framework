# SPDX-License-Identifier: AGPL-3.0
"""明日方舟逆推 — 精英分段 + 技能 SP。"""

from games.arknights.calc.inverse.adapter import (
    SKILL_SP_BLUEPRINT,
    ArknightsInverseAdapter,
    blueprint_for_rarity,
)
from games.arknights.calc.inverse.materialize import materialize_operator_entity
from games.arknights.calc.inverse.milestones import attach_growth_params, fit_operator_growth_params
from games.arknights.calc.inverse.segments import (
    elite_segment_key,
    segment_length,
)
from games.arknights.calc.inverse.stats import resolve_stats_from_segments

__all__ = [
    "SKILL_SP_BLUEPRINT",
    "ArknightsInverseAdapter",
    "attach_growth_params",
    "blueprint_for_rarity",
    "elite_segment_key",
    "fit_operator_growth_params",
    "materialize_operator_entity",
    "resolve_stats_from_segments",
    "segment_length",
]
