# SPDX-License-Identifier: AGPL-3.0
"""PyInstaller 冻结 exe 运行时能力与分阶段恢复（须在 rust_bridge 导入前调用）。

环境变量::

    CALC_FROZEN_SEARCH_PHASE  — 0=全保守 … 4=尽量恢复（见下方阶段表）
    RUST_SEARCH_FALLBACK=1      — 强制纯 Python（任意阶段均生效）

阶段（逐步加回，默认 **3**）::

    0  纯 Python + 单线程内联 + 主线程搜索（崩溃修复基线）
    1  + Rust 单条 evaluate（仍单线程内联 + 主线程）
    2  + ThreadPool 多 worker（主线程阻塞；**仅 phase 2**）
    3  + QThread 异步 + 内联单线程评估（界面不卡，**当前默认**；不与 ThreadPool 同开）
    4  + Rust 批量 evaluate_task_batch（仅裸 evaluate 路径）
"""

from __future__ import annotations

import os
import sys

_PHASE_MAX = 4


def is_frozen_exe() -> bool:
    """是否 PyInstaller 冻结 exe。"""
    return bool(getattr(sys, "frozen", False))


def frozen_search_phase() -> int:
    """当前 frozen 搜索恢复阶段（0–4）。"""
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


def frozen_allow_multi_workers(requested: int) -> int:
    """frozen 下有效 worker 数（phase 2 才允许多 worker；phase 3 内联单线程）。"""
    workers = max(1, int(requested))
    if not is_frozen_exe():
        return workers
    phase = frozen_search_phase()
    if phase < 2 or phase >= 3:
        return 1
    return workers


def frozen_use_qthread_search() -> bool:
    """frozen 下是否在 QThread 跑搜索（phase≥3）；否则主线程阻塞 + processEvents。"""
    if not is_frozen_exe():
        return True
    return frozen_search_phase() >= 3


def frozen_use_rust_batch() -> bool:
    """frozen 下是否允许 evaluate_task_batch Rust 批量（phase≥4）。"""
    if _rust_fallback_forced():
        return False
    if not is_frozen_exe():
        return True
    return frozen_search_phase() >= 4


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
    return " ".join(parts)
