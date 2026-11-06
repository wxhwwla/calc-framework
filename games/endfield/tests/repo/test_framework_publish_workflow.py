# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""Framework PyPI 发布工作流必须从已提交版本构建，并在发布前跑测试。

审查项 R-05：旧流程只在 runner 临时改写 ``framework/pyproject.toml``，
随后用原提交创建标签，导致 wheel、标签与源码版本不一致。
"""

from __future__ import annotations

import unittest
from typing import Any

import yaml
from games.endfield.tests.conftest import REPO_ROOT

WORKFLOW = REPO_ROOT / ".github" / "workflows" / "framework-publish.yml"


def _steps() -> list[dict[str, Any]]:
    data: dict[str, Any] = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    steps: list[dict[str, Any]] = []
    for job in (data.get("jobs") or {}).values():
        steps.extend(job.get("steps") or [])
    return steps


def _step_index(steps: list[dict[str, Any]], name: str) -> int:
    for i, step in enumerate(steps):
        if step.get("name") == name:
            return i
    raise AssertionError(f"未找到步骤: {name}")


def _runs(steps: list[dict[str, Any]]) -> list[str]:
    return [str(step.get("run", "")) for step in steps if step.get("run")]


class TestFrameworkPublishWorkflow(unittest.TestCase):
    def test_never_rewrites_pyproject_on_runner(self) -> None:
        for script in _runs(_steps()):
            self.assertNotIn("pyproject.toml', 'w'", script)
            self.assertNotIn("pyproject.toml\", 'w'", script)

    def test_verifies_committed_version_matches_input(self) -> None:
        scripts = _runs(_steps())
        self.assertTrue(
            any("tomllib" in s and "project']['version']" in s for s in scripts),
            "缺少 pyproject.toml 已提交版本与输入版本一致性校验",
        )

    def test_tests_run_before_build_and_upload(self) -> None:
        steps = _steps()
        tests = _step_index(steps, "Run tests before publishing")
        build = _step_index(steps, "Build distribution")
        upload = _step_index(steps, "Upload to PyPI")
        self.assertLess(tests, build)
        self.assertLess(build, upload)

    def test_wheel_metadata_verified_before_upload(self) -> None:
        steps = _steps()
        verify = _step_index(steps, "Verify wheel metadata and contents")
        upload = _step_index(steps, "Upload to PyPI")
        self.assertLess(verify, upload)

    def test_release_tag_matches_input_version(self) -> None:
        release = next(s for s in _steps() if s.get("name") == "Create GitHub Release")
        self.assertEqual(release["with"]["tag_name"], "framework-v${{ github.event.inputs.version }}")


if __name__ == "__main__":
    unittest.main()
