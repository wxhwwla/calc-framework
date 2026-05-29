"""SearchWorker.run() 完整路径测试。"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from PySide6.QtCore import QCoreApplication, QObject
from PySide6.QtWidgets import QApplication

from calculation.search.run.cancel import SearchCancelToken
from gui_design.controls.search.qt_actions import SearchWorker


def _app() -> QApplication | QCoreApplication:
    inst = QApplication.instance()
    if inst is None:
        inst = QApplication([])
    return inst


class _CollectSignals(QObject):
    def __init__(self) -> None:
        super().__init__()
        self.progress_calls: list[str] = []
        self.finished_calls: list[tuple] = []
        self.error_calls: list[str] = []

    def on_progress(self, text: str) -> None:
        self.progress_calls.append(text)

    def on_finished(self, *args: object) -> None:
        self.finished_calls.append(args)

    def on_error(self, text: str) -> None:
        self.error_calls.append(text)


class TestSearchWorkerRun:
    def test_run_success(self) -> None:
        _app()
        job = MagicMock()
        cancel = SearchCancelToken()

        mock_outcome = MagicMock()
        mock_outcome.exports = {"json": "/tmp/out.json"}
        mock_outcome.db_path = Path("/tmp/db")
        mock_outcome.export_dir = Path("/tmp")

        progress_callback_called = False

        def mock_run_search(_job, *, export_root, config, max_workers, cancel_token, progress_callback):
            nonlocal progress_callback_called
            progress_callback({"processed": 50, "total": 100, "eta_seconds": 30.0})
            progress_callback_called = True
            return mock_outcome

        with patch(
            "gui_design.controls.search.qt_actions.run_exported_single_skill_search",
            side_effect=mock_run_search,
        ):
            worker = SearchWorker(
                job, mode_label="测试", export_root=Path("/tmp"),
                top_n_choice="10", workers_choice="自动",
                status_prefix="搜索", cancel_token=cancel,
            )
            signals = _CollectSignals()
            worker.finished.connect(signals.on_finished)
            worker.error.connect(signals.on_error)
            worker.progress.connect(signals.on_progress)

            worker.run()

            assert len(signals.progress_calls) >= 1
            assert progress_callback_called
            assert len(signals.finished_calls) == 1

    def test_run_exception(self) -> None:
        _app()
        job = MagicMock()
        cancel = SearchCancelToken()

        with patch(
            "gui_design.controls.search.qt_actions.run_exported_single_skill_search",
            side_effect=ValueError("search failed"),
        ):
            worker = SearchWorker(
                job, mode_label="测试", export_root=Path("/tmp"),
                top_n_choice="10", workers_choice="自动",
                status_prefix="搜索", cancel_token=cancel,
            )
            signals = _CollectSignals()
            worker.finished.connect(signals.on_finished)
            worker.error.connect(signals.on_error)

            worker.run()

            assert len(signals.finished_calls) == 0
            assert len(signals.error_calls) == 1
            assert "search failed" in signals.error_calls[0]
