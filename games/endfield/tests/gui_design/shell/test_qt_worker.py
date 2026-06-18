# SPDX-License-Identifier: AGPL-3.0
"""CalcWorker 单元测试（直接调用 _run 避免 QThread）。"""

from __future__ import annotations

from unittest.mock import MagicMock

from games.endfield.gui.shell.qt_worker import CalcWorker
from PySide6.QtCore import QCoreApplication
from PySide6.QtWidgets import QApplication


def _app() -> QApplication | QCoreApplication:
    inst = QApplication.instance()

    if inst is None:
        inst = QApplication([])

    return inst


class TestCalcWorker:
    def test_run_cancelled_skips_emit(self) -> None:
        _app()

        worker = CalcWorker(fn=lambda: "ok")

        finished = MagicMock()

        worker.finished.connect(finished)

        worker._cancelled = True

        worker._run()

        finished.emit.assert_not_called()

    def test_cancel_before_start(self) -> None:
        _app()

        worker = CalcWorker(fn=lambda: "ok")

        worker.cancel()

        assert worker._cancelled is True

    def test_wait_for_finished_no_thread(self) -> None:
        _app()

        worker = CalcWorker(fn=lambda: "ok")

        assert worker.wait_for_finished() is True

    def test_start_already_running(self) -> None:
        _app()

        worker = CalcWorker(fn=lambda: "ok")

        mock_thread = MagicMock()

        mock_thread.isRunning.return_value = True

        worker._thread = mock_thread

        worker.start()

        mock_thread.started.connect.assert_not_called()

    def test_worker_attributes(self) -> None:
        worker = CalcWorker(fn=lambda x: x, args=(42,), kwargs={"y": 1})

        assert worker._args == (42,)

        assert worker._kwargs == {"y": 1}

    def test_run_finally_quits_thread(self) -> None:
        _app()

        worker = CalcWorker(fn=lambda: "ok")

        mock_thread = MagicMock()

        worker._thread = mock_thread

        worker._run()

        mock_thread.quit.assert_called_once()

    def test_cancel_with_running_thread(self) -> None:
        _app()

        worker = CalcWorker(fn=lambda: "ok")

        mock_thread = MagicMock()

        mock_thread.isRunning.return_value = True

        worker._thread = mock_thread

        worker.cancel()

        assert worker._cancelled is True

        mock_thread.quit.assert_called_once()

        mock_thread.wait.assert_called_once_with(3000)

    def test_wait_for_finished_with_thread(self) -> None:
        _app()

        worker = CalcWorker(fn=lambda: "ok")

        mock_thread = MagicMock()

        mock_thread.isRunning.return_value = True

        worker._thread = mock_thread

        result = worker.wait_for_finished(100)

        mock_thread.wait.assert_called_once_with(100)

        assert result == mock_thread.wait.return_value
