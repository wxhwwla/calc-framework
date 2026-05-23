#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MVP 端到端搜索流水线。

串联：``run_search_session``（并行 + 可选 SQLite 续跑）→ TopN → ``export_search_outputs`` 写文件。
GUI「全量遍历」「MVP 导出/续跑」最终都进入 ``run_mvp_search_from_job``。
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Optional

from calculation.damage_engine import DamageContext
from calculation.loadout_optimizer import LoadoutScore, OptimizerConfig, WeaponCandidate
from calculation.result_export import export_search_outputs
from calculation.search_cancel import SearchCancelToken
from calculation.search_eval_context import SearchEvalContext
from calculation.search_session import run_search_session
from calculation.single_skill_search_job import SingleSkillSearchJob


@dataclass(frozen=True)
class MvpSearchOutcome:
    """MVP 搜索 + 导出结果。"""

    processed_combinations: int
    total_combinations: int
    cancelled: bool
    top_results: tuple[LoadoutScore, ...]
    exports: dict[str, Any]
    db_path: Path
    export_dir: Path


def run_mvp_search_from_job(
    job: SingleSkillSearchJob,
    *,
    db_path: Path,
    export_dir: Path,
    config: OptimizerConfig,
    max_workers: int = 1,
    cancel_token: Optional[SearchCancelToken] = None,
    progress_callback: Optional[Callable[[dict], None]] = None,
) -> MvpSearchOutcome:
    """运行 MVP 主链路：续跑搜索 + 导出。"""
    search_eval = SearchEvalContext(
        char_data=job.char_data,
        char_level=job.char_level,
        weapon_level=job.weapon_level,
        trust_level=job.trust_level,
        weapon_data_by_name=job.weapon_data_by_name,
    )
    session = run_search_session(
        db_path=db_path,
        run_signature=job.run_signature,
        base_context=job.base_context,
        weapons=list(job.weapon_candidates),
        equipment_catalog=job.equipment_catalog,
        config=config,
        max_workers=max_workers,
        cancel_token=cancel_token,
        progress_callback=progress_callback,
        search_eval=search_eval,
    )
    exports = export_search_outputs(
        scores=session.top_results,
        output_dir=export_dir,
        top_n=config.top_n,
        export_all=True,
    )
    return MvpSearchOutcome(
        processed_combinations=session.processed_combinations,
        total_combinations=session.total_combinations,
        cancelled=session.cancelled,
        top_results=session.top_results,
        exports=exports,
        db_path=Path(db_path),
        export_dir=Path(export_dir),
    )


def run_mvp_search_pipeline(
    *,
    db_path: Path,
    export_dir: Path,
    run_signature: str,
    base_context: DamageContext,
    weapons: list[WeaponCandidate],
    equipment_catalog: dict[str, list[dict[str, Any]]],
    config: OptimizerConfig,
    max_workers: int = 1,
    cancel_token: Optional[SearchCancelToken] = None,
    progress_callback: Optional[Callable[[dict], None]] = None,
) -> dict[str, Any]:
    """兼容：松散参数调用，返回 dict（新代码请用 run_mvp_search_from_job）。"""
    outcome = run_mvp_search_from_job(
        SingleSkillSearchJob(
            char_data={},
            char_level=1,
            weapon_level=1,
            trust_level=0,
            skill_label="",
            weapon_scope="",
            equipment_scope="",
            varying_equipment_slot_count=4,
            base_context=base_context,
            weapon_candidates=tuple(weapons),
            equipment_catalog=equipment_catalog,
            weapon_data_by_name={w.name: {} for w in weapons},
            run_signature=run_signature,
        ),
        db_path=db_path,
        export_dir=export_dir,
        config=config,
        max_workers=max_workers,
        cancel_token=cancel_token,
        progress_callback=progress_callback,
    )
    return mvp_outcome_to_legacy_dict(outcome)


def mvp_outcome_to_legacy_dict(outcome: MvpSearchOutcome) -> dict[str, Any]:
    """转换为历史 dict 结构（测试/旧调用方）。"""
    return {
        "processed_combinations": outcome.processed_combinations,
        "total_combinations": outcome.total_combinations,
        "cancelled": outcome.cancelled,
        "top_results": [
            {
                "weapon_name": score.weapon_name,
                "final_damage": score.final_damage,
                "loadout_names": dict(score.loadout_names),
            }
            for score in outcome.top_results
        ],
        "exports": outcome.exports,
    }
