# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""配装评估模块拆分结构测试（P2-07）。

锁定 ``evaluate`` 与 ``evaluate_runtime`` ≤400 行，并保证缓存/运行时函数
仍可从原路径导入（``task_batch`` 与 ``store`` 依赖这些路径）。
"""

from __future__ import annotations

from pathlib import Path

_MODULE_NAMES = (
    "games.endfield.calc.loadout.optimizer.evaluate",
    "games.endfield.calc.loadout.optimizer.evaluate_runtime",
)


def _line_count(module_name: str) -> int:
    module = __import__(module_name, fromlist=["__file__"])
    return len(Path(module.__file__).read_text(encoding="utf-8").splitlines())


def test_evaluate_modules_stay_within_target() -> None:
    for module_name in _MODULE_NAMES:
        assert _line_count(module_name) <= 400, module_name


def test_evaluate_reexports_runtime_symbols() -> None:
    from games.endfield.calc.loadout.optimizer import evaluate, evaluate_runtime

    assert evaluate.build_runtime_eval_snapshot is evaluate_runtime.build_runtime_eval_snapshot
    assert evaluate.set_single_thread_mode is evaluate_runtime.set_single_thread_mode
    assert evaluate.warmup_final_attack_cache is evaluate_runtime.warmup_final_attack_cache
    assert evaluate._loadout_cache is evaluate_runtime._loadout_cache
    assert evaluate._final_attack_cache is evaluate_runtime._final_attack_cache
