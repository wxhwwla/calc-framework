#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MVP 端到端搜索流水线。"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Optional

from calculation.damage_engine import DamageContext
from calculation.loadout_optimizer import OptimizerConfig, WeaponCandidate
from calculation.result_export import export_search_outputs
from calculation.search_cancel import SearchCancelToken
from calculation.search_session import run_search_session


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
    """运行 MVP 主链路：续跑搜索 + 导出。"""
    session = run_search_session(
        db_path=db_path,
        run_signature=run_signature,
        base_context=base_context,
        weapons=weapons,
        equipment_catalog=equipment_catalog,
        config=config,
        max_workers=max_workers,
        cancel_token=cancel_token,
        progress_callback=progress_callback,
    )
    exports = export_search_outputs(
        scores=session.top_results,
        output_dir=export_dir,
        top_n=config.top_n,
        export_all=True,
    )
    return {
        "processed_combinations": session.processed_combinations,
        "total_combinations": session.total_combinations,
        "cancelled": session.cancelled,
        "top_results": [
            {
                "weapon_name": score.weapon_name,
                "final_damage": score.final_damage,
                "loadout_names": dict(score.loadout_names),
            }
            for score in session.top_results
        ],
        "exports": exports,
    }
