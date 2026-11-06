# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""桌面自动测试报告与退出码回归测试。

覆盖审查项 P1-04：启动失败、0 场景、必要步骤未执行时不得返回成功。
"""

from __future__ import annotations

from scripts.auto_test.utils.report import TestReport as Report
from scripts.auto_test.utils.report import TestScenario as Scenario
from scripts.auto_test.utils.report import TestStep as Step
from scripts.auto_test.utils.report import any_report_failed, check_required_steps


def _passed_scenario(name: str = "启动检查") -> Scenario:
    scenario = Scenario(name=name, description="desc")
    scenario.steps.append(Step(name="检查窗口存在", status="passed"))
    scenario.status = "passed"
    return scenario


def test_empty_report_is_not_success() -> None:
    report = Report(title="空报告")
    assert report.total_scenarios == 0
    assert report.success is False
    assert report.exit_code == 1


def test_report_with_passed_scenario_is_success() -> None:
    report = Report(title="通过")
    report.scenarios.append(_passed_scenario())
    assert report.success is True
    assert report.exit_code == 0


def test_infra_failure_forces_non_zero_exit() -> None:
    report = Report(title="启动失败")
    report.mark_infra_failed("应用启动失败")
    assert report.infra_failed is True
    assert report.infra_error == "应用启动失败"
    assert report.success is False
    assert report.exit_code == 1


def test_failed_scenario_forces_non_zero_exit() -> None:
    report = Report(title="失败")
    scenario = _passed_scenario()
    scenario.steps.append(Step(name="截图", status="failed", message="截图失败"))
    scenario.status = "failed"
    report.scenarios.append(scenario)
    assert report.success is False
    assert report.exit_code == 1


def test_scenario_without_executed_steps_forces_non_zero_exit() -> None:
    report = Report(title="空场景")
    report.scenarios.append(Scenario(name="未知场景", description="desc", status="passed"))
    assert report.success is False
    assert report.exit_code == 1


def test_check_required_steps_reports_missing_names() -> None:
    scenario = _passed_scenario()
    assert check_required_steps(scenario, ["检查窗口存在"]) == []
    assert check_required_steps(scenario, ["检查窗口存在", "点击确认"]) == ["点击确认"]


def test_any_report_failed_ignores_explicit_skips() -> None:
    passed = Report(title="通过")
    passed.scenarios.append(_passed_scenario())

    assert any_report_failed({"Web 前端": None, "桌面应用": passed}) is False
    assert any_report_failed({"桌面应用": Report(title="未执行")}) is True

    infra = Report(title="启动失败")
    infra.mark_infra_failed("应用启动失败")
    assert any_report_failed({"桌面应用": infra}) is True
