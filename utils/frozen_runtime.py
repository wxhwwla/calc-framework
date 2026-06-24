# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""PyInstaller 冻结 exe 运行时能力与分阶段恢复（须在 rust_bridge 导入前调用）。

环境变量::

    CALC_FROZEN_SEARCH_PHASE  — 0=全保守 … 5（见下方阶段表）
    RUST_SEARCH_FALLBACK=1      — 强制纯 Python（任意阶段均生效）
    CALC_SEARCH_BATCH_POOL=1    — 实验：batch ThreadPool 多 worker（默认关；实测常比单 worker 慢）
    CALC_RUST_PARALLEL_BATCH=0  — 关闭 Rust 批量 FFI 无锁并发

阶段（逐步加回，默认 **3**）::

    0  纯 Python + 单线程内联 + 主线程搜索（崩溃修复基线）
    1  + Rust 单条 evaluate（仍单线程内联 + 主线程）
    2  + ThreadPool 多 worker（主线程阻塞；**仅 phase 2**）
    3  + QThread + job Rust 批量 + **单 worker 内联 batch**（**当前默认**，97w~1min）
    4  + 裸 evaluate Rust 批量
    5  兼容编号；多 batch worker 同 ``CALC_SEARCH_BATCH_POOL=1``
"""

from __future__ import annotations

import os
import sys

_PHASE_MAX = 5


def is_frozen_exe() -> bool:
    """是否 PyInstaller 冻结 exe。"""
    return bool(getattr(sys, "frozen", False))


def frozen_search_phase() -> int:
    """当前 frozen 搜索恢复阶段（0–5）。"""
    if not is_frozen_exe():
        return _PHASE_MAX
    raw = os.environ.get("CALC_FROZEN_SEARCH_PHASE", "3").strip()
    try:
        phase = int(raw)
    except ValueError:
        phase = 3
    return max(0, min(phase, _PHASE_MAX))


def _rust_fallback_forced() -> bool:
    return os.environ.get("RUST_SEARCH_FALLBACK", "").strip().lower() in ("1", "true", "yes")


def apply_frozen_runtime_defaults() -> bool:
    """设置打包 exe 下的默认环境变量。返回是否处于 frozen 模式。"""
    if not is_frozen_exe():
        return False
    # 仅 phase 0 默认关闭 Rust；phase≥1 由用户逐步验收
    if frozen_search_phase() == 0:
        os.environ.setdefault("RUST_SEARCH_FALLBACK", "1")
    os.environ.setdefault("CALC_SEARCH_LOG_LEVEL", "DEBUG")
    return True


def use_rust_search_accel() -> bool:
    """是否允许加载/调用 Rust 搜索加速。"""
    if _rust_fallback_forced():
        return False
    if is_frozen_exe():
        return frozen_search_phase() >= 1
    return True


def frozen_use_thread_pool() -> bool:
    """frozen 下是否用 ThreadPool（仅 phase 2）。

    Phase 3+ 禁用：QThread + ThreadPool + Rust 在 PyInstaller exe 下会 native 崩溃。
    """
    if not is_frozen_exe():
        return True
    phase = frozen_search_phase()
    if phase >= 3:
        return False
    return phase >= 2


def _batch_pool_experimental_enabled() -> bool:
    """是否启用 batch ThreadPool 多 worker（默认关；job 批量路径下实测多 worker 更慢）。"""
    return os.environ.get("CALC_SEARCH_BATCH_POOL", "").strip().lower() in ("1", "true", "yes")


def search_job_batch_active() -> bool:
    """当前是否走 GUI/MVP search_job Rust 批量路径。"""
    return frozen_use_search_job_batch()


def search_recommended_workers(logical_processors: int) -> int:
    """GUI「自动」推荐 worker 数（job 批量默认 1；否则逻辑线程 −1）。"""
    logical = max(1, int(logical_processors))
    if search_job_batch_active() and not _batch_pool_experimental_enabled():
        return 1
    return max(1, logical - 1)


def frozen_allow_multi_workers(requested: int) -> int:
    """frozen/dev 有效 worker 数；job 批量默认强制 1（除非 CALC_SEARCH_BATCH_POOL=1）。"""
    workers = max(1, int(requested))
    if search_job_batch_active() and not _batch_pool_experimental_enabled():
        return 1
    if not is_frozen_exe():
        return workers
    phase = frozen_search_phase()
    if phase == 2:
        return workers
    if phase >= 3 and _batch_pool_experimental_enabled():
        return workers
    if phase >= 3:
        return 1
    return 1


def frozen_use_qthread_search() -> bool:
    """frozen 下是否在 QThread 跑搜索（phase≥3）；否则主线程阻塞 + processEvents。"""
    if not is_frozen_exe():
        return True
    return frozen_search_phase() >= 3


def frozen_use_rust_batch() -> bool:
    """frozen 下是否允许 evaluate_task_batch Rust 批量（phase≥4，裸 evaluate）。"""
    if _rust_fallback_forced():
        return False
    if not is_frozen_exe():
        return True
    return frozen_search_phase() >= 4


def frozen_use_search_job_batch() -> bool:
    """frozen 下是否允许 GUI search_job 单技能 Rust 批量（phase≥3，内联安全）。"""
    if _rust_fallback_forced():
        return False
    if not is_frozen_exe():
        return True
    return frozen_search_phase() >= 3 and use_rust_search_accel()


def frozen_use_batch_thread_pool() -> bool:
    """是否 batch 路径 ThreadPool 多 worker（默认关；``CALC_SEARCH_BATCH_POOL=1`` 开启）。"""
    if not _batch_pool_experimental_enabled():
        return False
    if not is_frozen_exe():
        return True
    return frozen_search_phase() >= 3


def rust_parallel_batch_enabled() -> bool:
    """Rust batch 是否无全局锁并发（仅 ``CALC_SEARCH_BATCH_POOL=1`` 时默认开）。"""
    raw = os.environ.get("CALC_RUST_PARALLEL_BATCH", "").strip().lower()
    if raw in ("0", "false", "no"):
        return False
    if raw in ("1", "true", "yes"):
        return True
    return frozen_use_batch_thread_pool()


def describe_frozen_search_capabilities() -> str:
    """供 search.log 记录的阶段摘要。"""
    if not is_frozen_exe():
        return "dev"
    p = frozen_search_phase()
    parts = [f"phase={p}"]
    parts.append(f"rust={'on' if use_rust_search_accel() else 'off'}")
    parts.append(f"pool={'on' if frozen_use_thread_pool() else 'inline'}")
    parts.append(f"qthread={'on' if frozen_use_qthread_search() else 'main'}")
    parts.append(f"rust_batch={'on' if frozen_use_rust_batch() else 'off'}")
    parts.append(f"job_batch={'on' if frozen_use_search_job_batch() else 'off'}")
    parts.append(f"batch_pool={'on' if frozen_use_batch_thread_pool() else 'off'}")
    return " ".join(parts)
