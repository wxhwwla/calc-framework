#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""单技能最优配装搜索。"""

from .catalog import count_loadout_combinations
from .evaluate import build_runtime_eval_snapshot, evaluate_task
from .plan import build_optimizer_search_plan
from .search import search_best_single_skill_loadouts
from .tasks import (
    OptimizerTask,
    enumerate_optimizer_tasks,
    iter_optimizer_tasks,
    optimizer_config_for_character,
)
from .types import (
    LoadoutScore,
    OptimizerConfig,
    OptimizerResult,
    OptimizerSearchPlan,
    RuntimeEvalSnapshot,
    WeaponCandidate,
)

__all__ = [
    "LoadoutScore",
    "OptimizerConfig",
    "OptimizerResult",
    "OptimizerSearchPlan",
    "RuntimeEvalSnapshot",
    "WeaponCandidate",
    "build_optimizer_search_plan",
    "build_runtime_eval_snapshot",
    "count_loadout_combinations",
    "enumerate_optimizer_tasks",
    "evaluate_task",
    "iter_optimizer_tasks",
    "optimizer_config_for_character",
    "search_best_single_skill_loadouts",
]
