#!/usr/bin/env python3
"""
PySide6 后台 Worker 基础设施。

``CalcWorker`` 封装了 ``QObject`` + ``QThread`` 模式，
将耗时计算卸载到后台线程，通过 ``Signal`` 安全更新 GUI。

用法::

    worker = CalcWorker(fn=my_heavy_computation)
    worker.finished.connect(on_result)
    worker.error.connect(on_error)
    worker.start()
    # ...
    worker.cancel()
"""

from __future__ import annotations

import traceback
from collections.abc import Callable
from typing import Any

from PySide6.QtCore import QObject, QThread, Signal, Slot


class CalcWorker(QObject):
    """在子线程中执行 ``fn(*args, **kwargs)``，完成后通过信号返回结果。

    用法:
        worker = CalcWorker(fn=expensive_function, args=(42,))
        worker.finished.connect(on_result)
        worker.error.connect(on_error)
        worker.start()

    信号（跨线程安全，自动 QueuedConnection）：
        progress(current, total): 进度通知
        finished(result): 计算完成
        error(message): 计算异常
    """

    progress = Signal(int, int)
    finished = Signal(str)
    error = Signal(str)

    def __init__(
        self,
        fn: Callable[..., Any],
        args: tuple = (),
        kwargs: dict | None = None,
    ) -> None:
        super().__init__()
        self._fn = fn
        self._args = args
        self._kwargs = kwargs or {}
        self._cancelled: bool = False
        self._thread: QThread | None = None

    def start(self) -> None:
        """创建 QThread 并启动后台计算。"""
        if self._thread is not None and self._thread.isRunning():
            return
        self._thread = QThread()
        self._thread.setObjectName("CalcWorkerThread")
        self.moveToThread(self._thread)
        self._thread.started.connect(self._run)
        self._thread.start()

    @Slot()
    def _run(self) -> None:
        """在子线程中执行（由 ``QThread.started`` 触发）。"""
        try:
            result = self._fn(*self._args, **self._kwargs)
            if not self._cancelled:
                self.finished.emit(str(result))
        except Exception as exc:
            if not self._cancelled:
                tb = traceback.format_exc()
                self.error.emit(f"{exc}\n{tb}")
        finally:
            if self._thread is not None:
                self._thread.quit()

    def cancel(self) -> None:
        """取消计算并终止线程。"""
        self._cancelled = True
        if self._thread is not None and self._thread.isRunning():
            self._thread.quit()
            self._thread.wait(3000)

    def wait_for_finished(self, timeout: int = 30000) -> bool:
        """等待线程退出。"""
        if self._thread is not None and self._thread.isRunning():
            return self._thread.wait(timeout)
        return True
