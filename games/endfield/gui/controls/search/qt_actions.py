#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# SPDX-License-Identifier: AGPL-3.0
"""PySide6 搜索线程与结果弹窗。

P2-07 拆分：结果弹窗与树构建迁至 ``qt_results_dialog.py``；本模块保留
``SearchWorker`` 并继续再导出弹窗符号，既有导入路径与 patch 目标不变。
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, Signal
from utils.search_diagnostics import get_search_logger, log_search_config

from games.endfield.calc.search.plan.controller import (
    optimizer_config_for_search_job,
)
from games.endfield.calc.search.plan.job import SingleSkillSearchJob
from games.endfield.calc.search.run.cancel import SearchCancelToken
from games.endfield.calc.search.run.single_skill import (
    run_exported_single_skill_search,
)
from games.endfield.gui.controls.search.qt_results_dialog import (
    QtSearchResultsDialog,
    _build_tree_items,
)
from games.endfield.gui.controls.search.search_settings import (
    format_search_progress_text,
    resolve_parallel_workers,
    resolve_top_n,
)
from games.endfield.gui.presentation.search_results_lines import (
    export_paths_to_strings,
)

__all__ = ["QtSearchResultsDialog", "SearchWorker", "_build_tree_items"]

# ═══════════════════════════════════════════════════════

#  搜索线程 Worker

# ═══════════════════════════════════════════════════════


class SearchWorker(QObject):
    """在 QThread 中执行全量遍历搜索。"""

    progress = Signal(str)

    finished = Signal(object, object, object, object)  # mode_label, job, outcome, export_paths

    error = Signal(str)

    def __init__(
        self,
        job: SingleSkillSearchJob,
        *,
        mode_label: str,
        export_root: Path,
        top_n_choice: str,
        workers_choice: str,
        status_prefix: str,
        cancel_token: SearchCancelToken,
    ) -> None:
        super().__init__()

        self._job = job

        self._mode_label = mode_label

        self._export_root = export_root

        self._top_n = resolve_top_n(top_n_choice)

        self._max_workers = resolve_parallel_workers(workers_choice)

        self._workers_choice = workers_choice

        self._status_prefix = status_prefix

        self._cancel_token = cancel_token

    def run(self) -> None:
        """在 QThread 中执行全量遍历搜索，发射 progress/finished/error 信号。"""
        slog = get_search_logger()
        config = optimizer_config_for_search_job(self._job, top_n=self._top_n)

        from games.endfield.gui.controls.search.search_settings import get_cpu_parallel_info

        cpu_info = get_cpu_parallel_info()
        log_search_config(
            phase="gui_worker",
            mode=self._mode_label,
            export_root=str(self._export_root),
            max_workers=self._max_workers,
            top_n=self._top_n,
            workers_choice=self._workers_choice,
            logical_processors=cpu_info.logical_processors,
            physical_cores=cpu_info.physical_cores,
            recommended_workers=cpu_info.recommended_workers,
            skill=getattr(self._job, "skill_label", ""),
            char=getattr(self._job, "char_data", {}).get("名称", ""),
        )

        def _progress(info: dict) -> None:
            processed = int(info.get("processed", 0))
            total = int(info.get("total", 0))
            speed = float(info.get("speed_per_sec", 0))
            if processed > 0 and (processed % 5000 == 0 or processed == total):
                slog.info(
                    "GUI 搜索进度 processed=%s/%s speed=%.1f/s eta=%.0fs",
                    processed,
                    total,
                    speed,
                    float(info.get("eta_seconds", 0.0)),
                )
            eta_seconds = float(info.get("eta_seconds", 0.0))
            estimated_total = (total / speed) if speed > 0 and total > 0 else 0
            text = format_search_progress_text(
                prefix=self._status_prefix,
                processed=processed,
                total=total,
                eta_seconds=eta_seconds,
                estimated_total_seconds=estimated_total,
            )
            self.progress.emit(text)

        try:
            outcome = run_exported_single_skill_search(
                self._job,
                export_root=self._export_root,
                config=config,
                max_workers=self._max_workers,
                cancel_token=self._cancel_token,
                progress_callback=_progress,
            )

        except Exception as exc:
            slog.exception("GUI 搜索线程异常")
            self.error.emit(str(exc))
            return

        slog.info(
            "GUI 搜索完成 processed=%s total=%s cancelled=%s",
            outcome.processed_combinations,
            outcome.total_combinations,
            outcome.cancelled,
        )

        export_paths = export_paths_to_strings(outcome.exports or {})

        export_paths["数据库"] = str(outcome.db_path)

        export_paths["导出目录"] = str(outcome.export_dir)

        self.finished.emit(self._mode_label, self._job, outcome, export_paths)
