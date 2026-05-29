"""终末地搜索引擎适配器 — 实现 framework SearchEngine 接口。

将终末地配装搜索包装为通用搜索引擎，其他游戏可参考此模式实现自己的适配器。
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from calc_framework.search import SearchEngine

from calculation.damage.engine import DamageContext
from calculation.loadout.optimizer import (
    LoadoutScore,
    OptimizerConfig,
    OptimizerTask,
    WeaponCandidate,
    build_optimizer_search_plan,
    enumerate_optimizer_tasks,
    evaluate_task,
)

from .evaluate.context import SearchEvalContext
from .plan.job import SingleSkillSearchJob


class EndfieldSearchEngine(SearchEngine[OptimizerTask, LoadoutScore]):
    """终末地配装搜索适配器。

    将终末地特有的 ``SingleSkillSearchJob`` + 搜索流程包装为框架泛型接口。

    用法::

        engine = EndfieldSearchEngine.from_job(job, search_eval=eval_ctx)
        result = engine.run(SearchConfig(top_n=20, max_workers=4))
    """

    def __init__(
        self,
        base_context: DamageContext,
        weapons: list[WeaponCandidate],
        equipment_catalog: dict[str, list[dict[str, Any]]],
        config: OptimizerConfig,
        *,
        search_eval: SearchEvalContext | None = None,
        task_evaluator: Callable[[OptimizerTask], LoadoutScore] | None = None,
    ) -> None:
        self._base_context = base_context
        self._weapons = weapons
        self._equipment_catalog = equipment_catalog
        self._config = config
        self._search_eval = search_eval
        self._task_evaluator = task_evaluator

    @classmethod
    def from_job(
        cls,
        job: SingleSkillSearchJob,
        *,
        search_eval: SearchEvalContext | None = None,
        config: OptimizerConfig | None = None,
    ) -> EndfieldSearchEngine:
        from .plan.controller import optimizer_config_for_search_job

        cfg = config or optimizer_config_for_search_job(job, top_n=10)
        weapons = list(job.weapon_candidates)
        return cls(
            base_context=job.base_context,
            weapons=weapons,
            equipment_catalog=dict(job.equipment_catalog),
            config=cfg,
            search_eval=search_eval or None,
        )

    def generate_candidates(self) -> list[OptimizerTask]:
        plan = build_optimizer_search_plan(
            weapons=self._weapons,
            equipment_catalog=self._equipment_catalog,
            config=self._config,
        )
        tasks, _total, _pruned, _warnings = enumerate_optimizer_tasks(
            base_context=self._base_context,
            weapons=plan.weapons,
            equipment_catalog=plan.equipment_catalog,
            config=self._config,
        )
        return list(tasks)

    def evaluate(self, candidate: OptimizerTask) -> LoadoutScore:
        if self._task_evaluator is not None:
            return self._task_evaluator(candidate)
        return evaluate_task(
            base_context=self._base_context,
            crit_mode=self._config.crit_mode,
            task=candidate,
            search_eval=self._search_eval,
        )

    def score_key(self, result: LoadoutScore) -> float:
        return result.final_damage

    def estimate_workload(self) -> int:
        plan = build_optimizer_search_plan(
            weapons=self._weapons,
            equipment_catalog=self._equipment_catalog,
            config=self._config,
        )
        _, total, _pruned, _warnings = enumerate_optimizer_tasks(
            base_context=self._base_context,
            weapons=plan.weapons,
            equipment_catalog=plan.equipment_catalog,
            config=self._config,
        )
        return total
