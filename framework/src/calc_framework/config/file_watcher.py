"""单文件监视器 — 通过 mtime 轮询检测文件变化。

用法::

    from calc_framework.config.file_watcher import FileWatcher

    def on_change() -> None:
        print("文件已变化")

    watcher = FileWatcher(Path("dag.json"), on_change=on_change)
    watcher.start()
    # ...
    watcher.stop()
"""

from __future__ import annotations

import threading
from pathlib import Path
from typing import Callable

from calc_framework.logging import get_logger

logger = get_logger(__name__)


class FileWatcher:
    """单文件 mtime 轮询监视器。

    在 daemon 后台线程中检测文件的 mtime，发现变化时调用 ``on_change`` 回调。
    线程安全：``start`` / ``stop`` 可在任意线程调用。
    """

    def __init__(
        self,
        path: str | Path,
        on_change: Callable[[], None],
        poll_interval: float = 1.0,
    ) -> None:
        self._path = Path(path)
        self._on_change = on_change
        self._poll_interval = max(0.5, poll_interval)
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()
        self._last_mtime: float = 0.0

    def start(self) -> None:
        """启动后台监视线程。"""
        with self._lock:
            if self._thread and self._thread.is_alive():
                logger.warning("FileWatcher[%s] 已在运行", self._path.name)
                return
            self._last_mtime = self._read_mtime()
            self._stop_event.clear()
            self._thread = threading.Thread(
                target=self._run, daemon=True, name=f"file-watcher-{self._path.name}",
            )
            self._thread.start()
            logger.info("FileWatcher[%s] 已启动 (poll=%ss)", self._path.name, self._poll_interval)

    def stop(self) -> None:
        """停止后台监视线程。"""
        self._stop_event.set()
        with self._lock:
            if self._thread:
                self._thread.join(timeout=5.0)
                self._thread = None
        logger.info("FileWatcher[%s] 已停止", self._path.name)

    @property
    def is_running(self) -> bool:
        with self._lock:
            return self._thread is not None and self._thread.is_alive()

    @property
    def path(self) -> Path:
        return self._path

    def _read_mtime(self) -> float:
        try:
            return self._path.stat().st_mtime
        except OSError:
            return 0.0

    def _run(self) -> None:
        while not self._stop_event.is_set():
            try:
                current = self._read_mtime()
                if current > 0 and current != self._last_mtime:
                    self._last_mtime = current
                    logger.info("FileWatcher[%s] 检测到文件变化", self._path.name)
                    try:
                        self._on_change()
                    except Exception as exc:
                        logger.error("FileWatcher[%s] 回调异常: %s", self._path.name, exc)
            except Exception as exc:
                logger.warning("FileWatcher[%s] 检查异常: %s", self._path.name, exc)
            self._stop_event.wait(timeout=self._poll_interval)
