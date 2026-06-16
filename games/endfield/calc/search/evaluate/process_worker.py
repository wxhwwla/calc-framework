#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""全量搜索多进程 worker — 模块级可 pickle 入口，供 ProcessPoolExecutor 使用。

支持单任务和批量化（batch）两种模式。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, TypeAlias, TypeGuard, cast

from games.endfield.calc.damage.engine import DamageContext
from games.endfield.calc.loadout.optimizer import LoadoutScore, OptimizerConfig, OptimizerTask, evaluate_task
from games.endfield.calc.search.evaluate.context import SearchEvalContext

KeyedOptimizerTask: TypeAlias = tuple[str, OptimizerTask]
BatchKeyedItem: TypeAlias = KeyedOptimizerTask | OptimizerTask


def _is_keyed_optimizer_task(item: BatchKeyedItem) -> TypeGuard[KeyedOptimizerTask]:
    """续跑项 ``(combo_key, task)`` 的首元素为 str；裸 ``OptimizerTask`` 首元素为 ``WeaponCandidate``。"""
    return isinstance(item, tuple) and len(item) == 2 and isinstance(item[0], str)


_evaluator: Any | None = None
_batch_evaluator: Any | None = None


@dataclass(frozen=True)
class ProcessWorkerPayload:
    """进程池 initializer 载荷（须可 pickle）。"""

    config: OptimizerConfig
    search_eval: SearchEvalContext | None
    search_job: Any | None = None
    base_context: DamageContext | None = None


def init_process_worker(payload: ProcessWorkerPayload) -> None:
    """在子进程内构建评估闭包（绕开主进程 GIL）。"""
    global _evaluator, _batch_evaluator
    if payload.search_job is not None:
        from games.endfield.calc.search.evaluate.task import make_loadout_task_evaluator

        _evaluator = make_loadout_task_evaluator(
            payload.search_job,
            crit_mode=payload.config.crit_mode,
            search_eval=payload.search_eval,
        )
        return
    if payload.base_context is None:
        raise RuntimeError("ProcessWorkerPayload 需要 search_job 或 base_context")
    base_context = payload.base_context
    search_eval = payload.search_eval
    crit_mode = payload.config.crit_mode

    def _simple_evaluator(task: OptimizerTask) -> LoadoutScore:
        return evaluate_task(
            base_context=base_context,
            crit_mode=crit_mode,
            task=task,
            search_eval=search_eval,
        )

    _evaluator = _simple_evaluator

    # 批量化评估器
    from games.endfield.calc.loadout.optimizer.evaluate import evaluate_task_batch

    _batch_evaluator = evaluate_task_batch(
        base_context=base_context,
        crit_mode=crit_mode,
        search_eval=search_eval,
    )


def evaluate_optimizer_task_in_process(task: OptimizerTask) -> LoadoutScore:
    """评估单条配装任务（子进程调用）。"""
    if _evaluator is None:
        raise RuntimeError("搜索进程 worker 未初始化")
    return _evaluator(task)


def evaluate_optimizer_batch_in_process(tasks: list[OptimizerTask]) -> list[LoadoutScore]:
    """批量评估配装任务（子进程调用，利用 Rust 批量化加速）。"""
    if _batch_evaluator is None:
        # fallback：逐条评估
        return [evaluate_optimizer_task_in_process(t) for t in tasks]
    return _batch_evaluator(tasks)


def _unwrap_batch_item(item: BatchKeyedItem) -> OptimizerTask:
    """从续跑项 ``(combo_key, task)`` 或裸 ``OptimizerTask`` 取出 task。"""
    if _is_keyed_optimizer_task(item):
        return item[1]
    return cast(OptimizerTask, item)


def evaluate_optimizer_batch_keyed_in_process(
    items: list[BatchKeyedItem],
) -> list[LoadoutScore]:
    """批量评估续跑项 ``(combo_key, task)`` 或裸 ``task``（子进程调用）。"""
    tasks = [_unwrap_batch_item(item) for item in items]
    return evaluate_optimizer_batch_in_process(tasks)


def evaluate_keyed_task_in_process(item: KeyedOptimizerTask) -> LoadoutScore:
    """评估 ``(combo_key, task)`` 续跑项（子进程调用）。"""
    _key, task = item
    return evaluate_optimizer_task_in_process(task)
