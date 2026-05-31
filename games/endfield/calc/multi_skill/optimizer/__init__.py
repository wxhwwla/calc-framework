#!/usr/bin/env python3
"""多技能加权总伤优化。"""

from .search import evaluate_multi_skill_task, optimize_multi_skill_loadouts
from .types import (
    MultiSkillConfig,
    MultiSkillResult,
    MultiSkillScore,
    SkillScenario,
    resolve_scenario_damage_type,
)
