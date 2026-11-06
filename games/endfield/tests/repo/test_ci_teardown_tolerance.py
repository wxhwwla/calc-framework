# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""CI 必须容忍 PySide6 在 pytest 退出阶段的 native crash（139 segfault / 134 abort）。

pytest 已跑完全部用例并写出 coverage.xml 后，解释器退出阶段偶发 Qt teardown 崩溃：
- SIGSEGV → exit 139（`Segmentation fault`）
- SIGABRT → exit 134（`QObject: shared QObject was deleted directly` +
  `malloc(): unaligned tcache chunk` + `Aborted (core dumped)`）

两条工作流的守卫都必须同时覆盖这两种信号，否则测试全绿仍会判定 Job 失败。
"""

from __future__ import annotations

import unittest
from collections.abc import Iterator
from typing import Any

import yaml
from games.endfield.tests.conftest import REPO_ROOT

WORKFLOWS = REPO_ROOT / ".github" / "workflows"


def _run_steps(workflow: str) -> Iterator[tuple[str, str]]:
    """遍历工作流中所有带 ``run`` 的步骤，返回 (步骤名, 脚本)。"""
    data: dict[str, Any] = yaml.safe_load((WORKFLOWS / workflow).read_text(encoding="utf-8"))
    for job in (data.get("jobs") or {}).values():
        for step in job.get("steps") or []:
            run = step.get("run")
            if run:
                yield str(step.get("name", "")), str(run)


def _teardown_guards(workflow: str) -> list[tuple[str, str]]:
    return [(name, run) for name, run in _run_steps(workflow) if "Ignoring Qt teardown" in run]


class TestCiTeardownTolerance(unittest.TestCase):
    def _assert_tolerates_both_signals(self, workflow: str, expected: int) -> None:
        guards = _teardown_guards(workflow)
        self.assertEqual(len(guards), expected, f"{workflow} 中 teardown 容错步骤数应为 {expected}，实际 {len(guards)}")
        for name, run in guards:
            with self.subTest(workflow=workflow, step=name):
                self.assertIn("-eq 134", run, f"{name} 未容忍 SIGABRT（exit 134）")
                self.assertIn("-eq 139", run, f"{name} 未容忍 SIGSEGV（exit 139）")
                self.assertIn("-f coverage.xml", run, f"{name} 未要求 coverage.xml 作为测试已完成的判据")
                self.assertIn(
                    "rm -f coverage.xml",
                    run,
                    f"{name} 未在 pytest 前删除旧 coverage.xml，崩溃时可能误判为本次测试已完成",
                )
                self.assertLess(
                    run.index("rm -f coverage.xml"),
                    run.index("pytest"),
                    f"{name} 必须在 pytest 前删除旧 coverage.xml",
                )

    def test_game_ci_tolerates_both_signals(self) -> None:
        self._assert_tolerates_both_signals("ci.yml", expected=2)

    def test_framework_ci_tolerates_both_signals(self) -> None:
        self._assert_tolerates_both_signals("framework-ci.yml", expected=1)


if __name__ == "__main__":
    unittest.main()
