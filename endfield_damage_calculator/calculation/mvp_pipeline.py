#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MVP 端到端搜索流水线。"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from calculation.damage_engine import DamageContext
from calculation.loadout_optimizer import OptimizerConfig, WeaponCandidate
from calculation.result_export import export_search_outputs
from calculation.search_persistence import execute_search_with_resume


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
) -> dict[str, Any]:
    """运行 MVP 主链路：续跑搜索 + 导出。"""
    resume_result = execute_search_with_resume(
        db_path=db_path,
        run_signature=run_signature,
        base_context=base_context,
        weapons=weapons,
        equipment_catalog=equipment_catalog,
        config=config,
        max_workers=max_workers,
    )
    exports = export_search_outputs(
        scores=resume_result.top_results,
        output_dir=export_dir,
        top_n=config.top_n,
        export_all=True,
    )
    return {
        "processed_combinations": resume_result.processed_combinations,
        "total_combinations": resume_result.total_combinations,
        "cancelled": resume_result.cancelled,
        "exports": exports,
    }
