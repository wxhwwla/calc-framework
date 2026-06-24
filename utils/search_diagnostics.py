# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""全量搜索与打包 exe 崩溃诊断日志。

写入目录（与 exe 同级）::

    logs/app.log       — 应用通用日志（由 setup_logging 配置）
    logs/search.log    — 全量搜索专用追踪（组合数、并行后端、进度、异常）
    logs/crash.log     — faulthandler / 未捕获异常 / 线程异常

环境变量::

    CALC_SEARCH_LOG_LEVEL   — search.log 级别，默认 frozen=DEBUG 否则 INFO
    CALC_DISABLE_CRASH_LOG  — 设为 1 关闭 crash.log 写入
"""

from __future__ import annotations

import faulthandler
import logging
import os
import sys
import threading
import traceback
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any

from utils.path_utils import get_application_dir

_LOG_FORMAT = "[%(asctime)s.%(msecs)03d] [%(levelname)-7s] [%(name)s] %(message)s"
_LOG_DATE = "%Y-%m-%d %H:%M:%S"
_LOGGER_NAME = "endfield.search.trace"

_initialized = False
_crash_file: Any | None = None
_search_logger: logging.Logger | None = None


def get_logs_dir() -> Path:
    """诊断日志根目录（exe 旁 ``logs/``）。"""
    return get_application_dir() / "logs"


def get_search_logger() -> logging.Logger:
    """全量搜索追踪 logger（懒初始化）。"""
    global _search_logger
    if _search_logger is not None:
        return _search_logger
    init_search_diagnostics()
    assert _search_logger is not None
    return _search_logger


def init_search_diagnostics(*, force: bool = False) -> Path:
    """初始化 crash 捕获与 search.log（幂等）。"""
    global _initialized, _search_logger, _crash_file
    if _initialized and not force:
        return get_logs_dir()

    if force:
        if _crash_file is not None:
            try:
                faulthandler.disable()
                _crash_file.close()
            except OSError:
                pass
            _crash_file = None
        if _search_logger is not None:
            for handler in list(_search_logger.handlers):
                try:
                    handler.close()
                except OSError:
                    pass
                _search_logger.removeHandler(handler)
        _initialized = False
        if hasattr(_install_exception_hooks, "_done"):
            _install_exception_hooks._done = False  # type: ignore[attr-defined]

    log_dir = get_logs_dir()
    log_dir.mkdir(parents=True, exist_ok=True)

    if os.environ.get("CALC_DISABLE_CRASH_LOG", "").strip() not in ("1", "true", "yes"):
        crash_path = log_dir / "crash.log"
        _crash_file = open(crash_path, "a", encoding="utf-8")  # noqa: SIM115
        _crash_file.write(
            f"\n--- session start {datetime.now(timezone.utc).isoformat()} "
            f"frozen={getattr(sys, 'frozen', False)} pid={os.getpid()} ---\n"
        )
        _crash_file.flush()
        faulthandler.enable(file=_crash_file, all_threads=True)

    _install_exception_hooks(log_dir / "crash.log")

    level_name = os.environ.get("CALC_SEARCH_LOG_LEVEL", "").strip().upper()
    if not level_name:
        level_name = "DEBUG" if getattr(sys, "frozen", False) else "INFO"
    level = getattr(logging, level_name, logging.DEBUG)

    logger = logging.getLogger(_LOGGER_NAME)
    logger.setLevel(level)
    logger.propagate = False
    logger.handlers.clear()

    handler = RotatingFileHandler(
        log_dir / "search.log",
        maxBytes=8 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    handler.setLevel(level)
    handler.setFormatter(logging.Formatter(_LOG_FORMAT, datefmt=_LOG_DATE))
    logger.addHandler(handler)

    if not getattr(sys, "frozen", False):
        console = logging.StreamHandler(sys.stderr)
        console.setLevel(level)
        console.setFormatter(logging.Formatter(_LOG_FORMAT, datefmt=_LOG_DATE))
        logger.addHandler(console)

    _search_logger = logger
    _initialized = True

    logger.info(
        "搜索诊断日志就绪 dir=%s frozen=%s executable=%s",
        log_dir,
        getattr(sys, "frozen", False),
        sys.executable,
    )
    _log_runtime_flags(logger)
    return log_dir


def log_search_event(message: str, *args: Any, level: int = logging.INFO, **kwargs: Any) -> None:
    """写一条搜索追踪日志。"""
    get_search_logger().log(level, message, *args, **kwargs)


def log_search_config(**fields: Any) -> None:
    """记录一次搜索启动参数快照。"""
    parts = ", ".join(f"{k}={fields[k]!r}" for k in sorted(fields))
    log_search_event("搜索启动 | %s", parts)


def summarize_work_item(item: Any, *, max_len: int = 200) -> str:
    """压缩日志中的任务项描述，避免整段装备 dict。"""
    text = repr(item)
    if len(text) > max_len:
        return text[: max_len - 3] + "..."
    return text


def _log_runtime_flags(logger: logging.Logger) -> None:
    """记录 Rust / 并行相关运行时标志。"""
    from utils.frozen_runtime import describe_frozen_search_capabilities

    logger.info("frozen_caps | %s", describe_frozen_search_capabilities())
    if os.environ.get("RUST_SEARCH_FALLBACK"):
        logger.info(
            "运行时 | rust_search=False rust_detail=RUST_SEARCH_FALLBACK=1 mp_start=%s",
            getattr(sys, "frozen", False),
        )
        return
    rust_ok = False
    rust_err = ""
    try:
        import rust_search  # noqa: F401

        rust_ok = True
    except Exception as exc:
        rust_err = f"{type(exc).__name__}: {exc}"
    logger.info(
        "运行时 | rust_search=%s rust_detail=%s mp_start=%s",
        rust_ok,
        rust_err or "ok",
        getattr(sys, "frozen", False),
    )


def _install_exception_hooks(crash_path: Path) -> None:
    """未捕获异常与 QThread 线程异常写入 crash.log。"""
    if getattr(_install_exception_hooks, "_done", False):
        return
    _install_exception_hooks._done = True  # type: ignore[attr-defined]

    def _append_crash(header: str, exc: BaseException | None, tb: Any) -> None:
        try:
            with open(crash_path, "a", encoding="utf-8") as fh:
                fh.write(f"\n=== {header} {datetime.now(timezone.utc).isoformat()} ===\n")
                if exc is not None:
                    fh.write("".join(traceback.format_exception(type(exc), exc, tb)))
                fh.flush()
        except OSError:
            pass
        try:
            get_search_logger().error("%s\n%s", header, "".join(traceback.format_exception(type(exc), exc, tb)))
        except Exception:
            pass

    _orig_excepthook = sys.excepthook

    def _excepthook(exc_type, exc, tb) -> None:
        if exc is not None:
            _append_crash("uncaught", exc, tb)
        _orig_excepthook(exc_type, exc, tb)

    sys.excepthook = _excepthook

    if hasattr(threading, "excepthook"):
        _orig_thread_hook = threading.excepthook

        def _thread_excepthook(args: threading.ExceptHookArgs) -> None:
            _append_crash(f"thread:{args.thread.name}", args.exc_value, args.exc_traceback)
            _orig_thread_hook(args)

        threading.excepthook = _thread_excepthook
