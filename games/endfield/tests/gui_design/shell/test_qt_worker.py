#!/usr/bin/env python3
"""CalcWorker 后台 Worker 测试。"""

from __future__ import annotations

import unittest

from PySide6.QtCore import QCoreApplication, QEventLoop, QTimer

from gui_design.shell.qt_worker import CalcWorker


class TestCalcWorker(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not QCoreApplication.instance():
            cls._app = QCoreApplication([])

    def _run_with_loop(self, worker: CalcWorker, timeout_ms: int = 5000) -> None:
        loop = QEventLoop()
        worker.finished.connect(loop.quit)
        worker.error.connect(loop.quit)
        QTimer.singleShot(timeout_ms, loop.quit)
        worker.start()
        loop.exec()
        worker.wait_for_finished(timeout=3000)

    def test_worker_lifecycle(self) -> None:
        results: list[str] = []
        worker = CalcWorker(fn=lambda: "hello")
        worker.finished.connect(lambda r: results.append(r))
        self._run_with_loop(worker)
        self.assertEqual(results, ["hello"])

        worker2 = CalcWorker(fn=lambda a, b: str(a + b), args=(1, 2))
        results2: list[str] = []
        worker2.finished.connect(lambda r: results2.append(r))
        self._run_with_loop(worker2)
        self.assertEqual(results2, ["3"])

        errors: list[str] = []

        def crash() -> None:
            raise ValueError("boom")

        worker3 = CalcWorker(fn=crash)
        worker3.error.connect(lambda m: errors.append(m))
        self._run_with_loop(worker3)
        self.assertEqual(len(errors), 1)
        self.assertIn("boom", errors[0])

        worker4 = CalcWorker(fn=lambda: "x")
        worker4.cancel()
        self._run_with_loop(worker4)

    def test_wait_for_finished_no_thread(self) -> None:
        worker = CalcWorker(fn=lambda: "x")
        self.assertTrue(worker.wait_for_finished(timeout=100))


if __name__ == "__main__":
    unittest.main()
