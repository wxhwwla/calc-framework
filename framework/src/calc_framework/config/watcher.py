"""适配包热加载监视器 — 文件变化时自动重载。"""

from __future__ import annotations

import os
import threading
import time
from pathlib import Path
from typing import Any, Callable

from calc_framework.config.adapter import AdapterPackage
from calc_framework.config.manager import AdapterManager
from calc_framework.logging import get_logger

logger = get_logger(__name__)

_RELOADABLE_EXTENSIONS = frozenset({".json", ".py"})


class AdapterWatcher:
    """适配包文件监视器。

    在后台线程中轮询适配包目录的文件变化，发现变更时触发回调。

    用法::

        mgr = AdapterManager()
        watcher = AdapterWatcher(mgr, on_reload=my_callback)
        watcher.start()

        # ... 运行中 ...

        watcher.stop()
    """

    def __init__(
        self,
        manager: AdapterManager,
        *,
        on_reload: Callable[[str, AdapterPackage], None] | None = None,
        poll_interval: float = 2.0,
    ) -> None:
        self._manager = manager
        self._on_reload = on_reload
        self._poll_interval = max(0.5, poll_interval)
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._snapshots: dict[str, dict[str, float]] = {}
        self._lock = threading.Lock()

    def start(self) -> None:
        """启动后台监视线程。"""
        if self._thread and self._thread.is_alive():
            logger.warning("AdapterWatcher 已在运行")
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True, name="adapter-watcher")
        self._thread.start()
        logger.info("适配包监视器已启动 (poll=%ss)", self._poll_interval)

    def stop(self) -> None:
        """停止后台监视线程。"""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5.0)
            self._thread = None
        logger.info("适配包监视器已停止")

    def _take_snapshot(self, name: str, base_path: Path) -> dict[str, float]:
        """记录目录下所有可加载文件的 mtime。"""
        snap: dict[str, float] = {}
        for entry in base_path.rglob("*"):
            if entry.suffix not in _RELOADABLE_EXTENSIONS:
                continue
            try:
                snap[str(entry.relative_to(base_path))] = entry.stat().st_mtime
            except OSError:
                pass
        return snap

    def _has_changed(self, name: str, base_path: Path) -> bool:
        """检查目录是否有文件变化。"""
        current = self._take_snapshot(name, base_path)
        previous = self._snapshots.get(name, {})
        if set(current.keys()) != set(previous.keys()):
            return True
        for fpath, mtime in current.items():
            if previous.get(fpath, 0) != mtime:
                return True
        return False

    def _run(self) -> None:
        while not self._stop_event.is_set():
            try:
                self._check_adapters()
            except Exception as exc:
                logger.warning("适配包检查异常: %s", exc)
            self._stop_event.wait(timeout=self._poll_interval)

    def _check_adapters(self) -> None:
        available = self._manager.available_adapters
        changed_names: list[str] = []

        for name, path in available.items():
            if name not in self._snapshots:
                self._snapshots[name] = self._take_snapshot(name, path)
                continue

            if self._has_changed(name, path):
                logger.info("检测到适配包变化: %s", name)
                changed_names.append(name)

        for name in changed_names:
            self._snapshots[name] = self._take_snapshot(name, available[name])
            try:
                pkg = self._manager.reload(name)
                if self._on_reload:
                    self._on_reload(name, pkg)
            except Exception as exc:
                logger.error("重载适配包 %s 失败: %s", name, exc)

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()
