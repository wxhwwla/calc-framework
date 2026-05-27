#!/usr/bin/env python3
"""PySide6 搜索线程与结果弹窗。"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from calculation.search.plan.controller import (
    optimizer_config_for_search_job,
)
from calculation.search.plan.job import SingleSkillSearchJob
from calculation.search.run.cancel import SearchCancelToken
from calculation.search.run.single_skill import (
    run_exported_single_skill_search,
)
from gui_design.presentation.search_results_lines import (
    export_paths_to_strings,
)
from gui_design.search_ui.search_settings import (
    format_search_progress_text,
    resolve_parallel_workers,
    resolve_top_n,
)

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
        self._status_prefix = status_prefix
        self._cancel_token = cancel_token

    def run(self) -> None:
        """在 QThread 中执行全量遍历搜索，发射 progress/finished/error 信号。"""
        config = optimizer_config_for_search_job(self._job, top_n=self._top_n)

        def _progress(info: dict) -> None:
            text = format_search_progress_text(
                prefix=self._status_prefix,
                processed=int(info.get("processed", 0)),
                total=int(info.get("total", 0)),
                eta_seconds=float(info.get("eta_seconds", 0.0)),
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
            self.error.emit(str(exc))
            return

        export_paths = export_paths_to_strings(outcome.exports or {})
        export_paths["数据库"] = str(outcome.db_path)
        export_paths["导出目录"] = str(outcome.export_dir)

        self.finished.emit(self._mode_label, self._job, outcome, export_paths)


# ═══════════════════════════════════════════════════════
#  搜索弹窗
# ═══════════════════════════════════════════════════════


class QtSearchResultsDialog(QDialog):
    """全量 / MVP 搜索结果展示弹窗。"""

    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        title: str,
        lines: list[str],
        big_font: QFont,
        small_font: QFont,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(920, 720)
        self.setMinimumSize(640, 480)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)

        text = QPlainTextEdit()
        text.setFont(small_font)
        text.setReadOnly(True)
        text.setPlainText("\n".join(lines))
        text.setStyleSheet("""
            QPlainTextEdit {
                background-color: #1E1E1E; color: #D1D1D1;
                border: 1px solid #464646; border-radius: 6px;
                padding: 8px;
            }
        """)
        layout.addWidget(text, stretch=1)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        close_btn = QPushButton("关闭")
        close_btn.setFont(small_font)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent; color: #D1D1D1;
                border: 1px solid #464646; border-radius: 6px;
                padding: 6px 24px;
            }
            QPushButton:hover { border-color: #2B6CB6; color: white; }
        """)
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(close_btn)
        layout.addLayout(btn_row)
