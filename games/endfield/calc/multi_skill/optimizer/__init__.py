#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""多技能加权总伤优化。"""

from .search import evaluate_multi_skill_task, optimize_multi_skill_loadouts
from .types import (
    MultiSkillConfig,
    MultiSkillResult,
    MultiSkillScore,
    SkillScenario,
    resolve_scenario_damage_type,
)

__all__ = [
    "MultiSkillConfig",
    "MultiSkillResult",
    "MultiSkillScore",
    "SkillScenario",
    "evaluate_multi_skill_task",
    "optimize_multi_skill_loadouts",
    "resolve_scenario_damage_type",
]
