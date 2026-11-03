# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""有界并行搜索拆分结构测试（P2-07）。"""

from __future__ import annotations

from pathlib import Path

_MODULE_NAMES = (
    "games.endfield.calc.search.run.parallel",
    "games.endfield.calc.search.run.parallel_loops",
)


def _line_count(module_name: str) -> int:
    module = __import__(module_name, fromlist=["__file__"])
    return len(Path(module.__file__).read_text(encoding="utf-8").splitlines())


def test_parallel_modules_stay_within_target() -> None:
    for module_name in _MODULE_NAMES:
        assert _line_count(module_name) <= 400, module_name


def test_parallel_reexports_loop_helpers() -> None:
    from games.endfield.calc.search.run import parallel, parallel_loops

    assert parallel._run_inline_loop is parallel_loops._run_inline_loop
    assert parallel._run_parallel_loop is parallel_loops._run_parallel_loop
