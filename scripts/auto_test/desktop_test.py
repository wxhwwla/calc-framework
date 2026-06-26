# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""
桌面应用自动化测试

测试 PySide6 桌面应用的功能完整性。
使用 pywinauto 的 UIA 后端识别和操作 Qt 控件。

用法：
    python scripts/auto_test/desktop_test.py
"""

from __future__ import annotations

import logging
import subprocess
import sys
import time
from pathlib import Path

# 添加项目路径
_SCRIPT_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _SCRIPT_DIR.parent.parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from config import (
    APP_STARTUP_TIMEOUT,
    APP_WINDOW_TITLE,
    DESKTOP_ENTRY,
    SCREENSHOT_DESKTOP_DIR,
    TEST_SCENARIOS,
    ensure_dirs,
)

from utils.qt_inspector import QtInspector
from utils.report import TestReport, TestScenario, TestStep

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


class DesktopTestRunner:
    """桌面应用测试运行器。

    负责启动应用、执行测试场景、生成报告。
    """

    def __init__(self) -> None:
        self.inspector = QtInspector()
        self.report = TestReport(title="桌面应用测试报告")
        self._process: subprocess.Popen | None = None

    def start_app(self) -> bool:
        """启动桌面应用。

        Returns:
            是否启动成功
        """
        logger.info("启动桌面应用: %s", DESKTOP_ENTRY)

        try:
            # 使用 Python 启动应用
            self._process = subprocess.Popen(
                [sys.executable, str(DESKTOP_ENTRY)],
                cwd=str(_REPO_ROOT),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            # 等待窗口出现
            logger.info("等待窗口出现 (超时: %ds)...", APP_STARTUP_TIMEOUT)
            if self.inspector.connect(APP_WINDOW_TITLE, timeout=APP_STARTUP_TIMEOUT):
                logger.info("应用启动成功")
                return True
            else:
                logger.error("应用启动超时")
                self.stop_app()
                return False

        except Exception as e:
            logger.error("启动应用失败: %s", e)
            return False

    def stop_app(self) -> None:
        """停止应用。"""
        if self._process:
            try:
                self._process.terminate()
                self._process.wait(timeout=5)
            except Exception:
                self._process.kill()
            self._process = None
            logger.info("应用已停止")

    def run_scenario(self, scenario_config: dict) -> TestScenario:
        """运行单个测试场景。

        Args:
            scenario_config: 场景配置

        Returns:
            测试场景结果
        """
        scenario = TestScenario(
            name=scenario_config["name"],
            description=scenario_config["description"],
        )
        scenario.start_time = time.time()

        logger.info("━━━ 场景: %s ━━━", scenario.name)

        # 根据场景名称执行不同的测试
        if scenario.name == "启动检查":
            self._test_startup(scenario)
        elif scenario.name == "计算页功能":
            self._test_compute_page(scenario)
        elif scenario.name == "高级页功能":
            self._test_advanced_page(scenario)
        elif scenario.name == "数据设计器":
            self._test_designer(scenario)
        else:
            logger.warning("未知场景: %s", scenario.name)

        scenario.end_time = time.time()
        scenario.status = "passed" if scenario.failed_count == 0 else "failed"

        return scenario

    def _test_startup(self, scenario: TestScenario) -> None:
        """测试启动。"""
        # 步骤 1: 检查窗口存在
        step = TestStep(name="检查窗口存在")
        step_start = time.time()

        if self.inspector.main_window and self.inspector.main_window.exists():
            step.status = "passed"
            step.message = "主窗口已找到"
        else:
            step.status = "failed"
            step.message = "主窗口未找到"

        step.duration = time.time() - step_start
        scenario.steps.append(step)

        # 步骤 2: 截图
        step = TestStep(name="截图")
        step_start = time.time()

        screenshot_path = SCREENSHOT_DESKTOP_DIR / "startup.png"
        try:
            self.inspector.screenshot(str(screenshot_path))
            step.status = "passed"
            step.screenshot = str(screenshot_path.relative_to(_SCRIPT_DIR))
        except Exception as e:
            step.status = "failed"
            step.message = f"截图失败: {e}"

        step.duration = time.time() - step_start
        scenario.steps.append(step)

    def _test_compute_page(self, scenario: TestScenario) -> None:
        """测试计算页功能。"""
        # 步骤 1: 切换到计算页
        step = TestStep(name="切换到计算页")
        step_start = time.time()

        # 查找计算页标签
        tab = self.inspector.find_control(name="计算页")
        if tab:
            self.inspector.click(tab)
            step.status = "passed"
            step.message = "已切换到计算页"
        else:
            step.status = "failed"
            step.message = "未找到计算页标签"

        step.duration = time.time() - step_start
        scenario.steps.append(step)

        # 步骤 2: 检查角色选择区域
        step = TestStep(name="检查角色选择区域")
        step_start = time.time()

        char_selector = self.inspector.find_control(name="角色选择")
        if char_selector:
            step.status = "passed"
            step.message = "角色选择区域已找到"
        else:
            step.status = "failed"
            step.message = "角色选择区域未找到"

        step.duration = time.time() - step_start
        scenario.steps.append(step)

        # 步骤 3: 截图
        step = TestStep(name="截图")
        step_start = time.time()

        screenshot_path = SCREENSHOT_DESKTOP_DIR / "compute_page.png"
        try:
            self.inspector.screenshot(str(screenshot_path))
            step.status = "passed"
            step.screenshot = str(screenshot_path.relative_to(_SCRIPT_DIR))
        except Exception as e:
            step.status = "failed"
            step.message = f"截图失败: {e}"

        step.duration = time.time() - step_start
        scenario.steps.append(step)

    def _test_advanced_page(self, scenario: TestScenario) -> None:
        """测试高级页功能。"""
        # 步骤 1: 切换到高级页
        step = TestStep(name="切换到高级页")
        step_start = time.time()

        tab = self.inspector.find_control(name="高级页")
        if tab:
            self.inspector.click(tab)
            step.status = "passed"
            step.message = "已切换到高级页"
        else:
            step.status = "failed"
            step.message = "未找到高级页标签"

        step.duration = time.time() - step_start
        scenario.steps.append(step)

        # 步骤 2: 检查搜索面板
        step = TestStep(name="检查搜索面板")
        step_start = time.time()

        search_panel = self.inspector.find_control(name="全量搜索")
        if search_panel:
            step.status = "passed"
            step.message = "搜索面板已找到"
        else:
            step.status = "failed"
            step.message = "搜索面板未找到"

        step.duration = time.time() - step_start
        scenario.steps.append(step)

        # 步骤 3: 截图
        step = TestStep(name="截图")
        step_start = time.time()

        screenshot_path = SCREENSHOT_DESKTOP_DIR / "advanced_page.png"
        try:
            self.inspector.screenshot(str(screenshot_path))
            step.status = "passed"
            step.screenshot = str(screenshot_path.relative_to(_SCRIPT_DIR))
        except Exception as e:
            step.status = "failed"
            step.message = f"截图失败: {e}"

        step.duration = time.time() - step_start
        scenario.steps.append(step)

    def _test_designer(self, scenario: TestScenario) -> None:
        """测试数据设计器。"""
        # 步骤 1: 查找设计器入口
        step = TestStep(name="查找设计器入口")
        step_start = time.time()

        # 设计器可能是菜单项或按钮
        designer_entry = self.inspector.find_control(name="设计器")
        if not designer_entry:
            designer_entry = self.inspector.find_control(name="数据设计器")

        if designer_entry:
            step.status = "passed"
            step.message = "设计器入口已找到"
        else:
            step.status = "skipped"
            step.message = "设计器入口未找到（可能需要从菜单打开）"

        step.duration = time.time() - step_start
        scenario.steps.append(step)

        # 步骤 2: 截图
        step = TestStep(name="截图")
        step_start = time.time()

        screenshot_path = SCREENSHOT_DESKTOP_DIR / "designer.png"
        try:
            self.inspector.screenshot(str(screenshot_path))
            step.status = "passed"
            step.screenshot = str(screenshot_path.relative_to(_SCRIPT_DIR))
        except Exception as e:
            step.status = "failed"
            step.message = f"截图失败: {e}"

        step.duration = time.time() - step_start
        scenario.steps.append(step)

    def run_all(self) -> TestReport:
        """运行所有测试场景。

        Returns:
            测试报告
        """
        ensure_dirs()
        self.report.start_time = time.time()

        # 启动应用
        if not self.start_app():
            self.report.end_time = time.time()
            return self.report

        # 运行测试场景
        scenarios_config = TEST_SCENARIOS.get("desktop", [])
        for config in scenarios_config:
            scenario = self.run_scenario(config)
            self.report.scenarios.append(scenario)

        # 停止应用
        self.stop_app()
        self.report.end_time = time.time()

        return self.report


def main() -> None:
    """主入口。"""
    runner = DesktopTestRunner()
    report = runner.run_all()

    # 保存报告
    report_path = SCREENSHOT_DESKTOP_DIR / "report.md"
    report.save(report_path)

    # 输出摘要
    print("\n" + "=" * 60)
    print(f"测试完成: {report.passed_scenarios}/{report.total_scenarios} 场景通过")
    print(f"报告已保存: {report_path}")
    print("=" * 60)

    # 返回退出码
    if report.failed_scenarios > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
