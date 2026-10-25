# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""
打包后 exe 自动化测试

测试 PyInstaller 打包后的 exe 功能完整性。
流程：打包 → 启动 exe → 自动化测试 → 截图 → 生成报告

用法：
    python scripts/auto_test/packaged_test.py
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
    BUILD_SCRIPT,
    BUILD_TIMEOUT,
    DIST_DIR,
    PACKAGED_EXE_NAME,
    SCREENSHOT_PACKAGED_DIR,
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


class PackagedTestRunner:
    """打包后测试运行器。

    负责打包应用、启动 exe、执行测试场景、生成报告。
    """

    def __init__(self, *, skip_build: bool = False) -> None:
        self.inspector = QtInspector()
        self.report = TestReport(title="打包后测试报告")
        self._process: subprocess.Popen | None = None
        self._skip_build = skip_build
        self._exe_path: Path | None = None

    def build_exe(self) -> bool:
        """打包应用。

        Returns:
            是否打包成功
        """
        if self._skip_build:
            logger.info("跳过打包步骤")
            # 查找已有的 exe
            self._find_existing_exe()
            return self._exe_path is not None

        logger.info("开始打包应用...")
        logger.info("打包脚本: %s", BUILD_SCRIPT)

        try:
            # 运行打包脚本
            result = subprocess.run(
                [
                    sys.executable,
                    str(BUILD_SCRIPT),
                    "--target",
                    "calculator",
                ],
                cwd=str(_REPO_ROOT),
                capture_output=True,
                text=True,
                timeout=BUILD_TIMEOUT,
            )

            if result.returncode != 0:
                logger.error("打包失败:\n%s", result.stderr)
                return False

            logger.info("打包成功")

            # 查找生成的 exe
            self._find_existing_exe()
            return self._exe_path is not None

        except subprocess.TimeoutExpired:
            logger.error("打包超时 (%ds)", BUILD_TIMEOUT)
            return False
        except Exception as e:
            logger.error("打包异常: %s", e)
            return False

    def _find_existing_exe(self) -> None:
        """查找已存在的 exe 文件。"""
        # 常见的输出路径
        possible_paths = [
            DIST_DIR / PACKAGED_EXE_NAME,
            DIST_DIR / "终末地伤害计算器" / PACKAGED_EXE_NAME,
            DIST_DIR / "calculator" / PACKAGED_EXE_NAME,
        ]

        for path in possible_paths:
            if path.exists():
                self._exe_path = path
                logger.info("找到 exe: %s", path)
                return

        # 递归查找
        for exe in DIST_DIR.rglob("*.exe"):
            if "calculator" in exe.name.lower() or "终末地" in exe.name:
                self._exe_path = exe
                logger.info("找到 exe: %s", exe)
                return

        logger.error("未找到 exe 文件")

    def start_exe(self) -> bool:
        """启动 exe。

        Returns:
            是否启动成功
        """
        if not self._exe_path:
            logger.error("exe 路径未设置")
            return False

        logger.info("启动 exe: %s", self._exe_path)

        try:
            self._process = subprocess.Popen(
                [str(self._exe_path)],
                cwd=str(self._exe_path.parent),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            # 等待窗口出现
            logger.info("等待窗口出现 (超时: %ds)...", APP_STARTUP_TIMEOUT)
            if self.inspector.connect("终末地伤害计算器", timeout=APP_STARTUP_TIMEOUT):
                logger.info("exe 启动成功")
                return True
            else:
                logger.error("exe 启动超时")
                self.stop_exe()
                return False

        except Exception as e:
            logger.error("启动 exe 失败: %s", e)
            return False

    def stop_exe(self) -> None:
        """停止 exe。"""
        if self._process:
            try:
                self._process.terminate()
                self._process.wait(timeout=5)
            except Exception:
                self._process.kill()
            self._process = None
            logger.info("exe 已停止")

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
        if scenario.name == "exe 启动检查":
            self._test_exe_startup(scenario)
        elif scenario.name == "exe 功能完整性":
            self._test_exe_functionality(scenario)
        else:
            logger.warning("未知场景: %s", scenario.name)

        scenario.end_time = time.time()
        scenario.status = "passed" if scenario.failed_count == 0 else "failed"

        return scenario

    def _test_exe_startup(self, scenario: TestScenario) -> None:
        """测试 exe 启动。"""
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

        screenshot_path = SCREENSHOT_PACKAGED_DIR / "exe_startup.png"
        try:
            self.inspector.screenshot(str(screenshot_path))
            step.status = "passed"
            step.screenshot = str(screenshot_path.relative_to(_SCRIPT_DIR))
        except Exception as e:
            step.status = "failed"
            step.message = f"截图失败: {e}"

        step.duration = time.time() - step_start
        scenario.steps.append(step)

    def _test_exe_functionality(self, scenario: TestScenario) -> None:
        """测试 exe 功能完整性。"""
        # 步骤 1: 切换计算页
        step = TestStep(name="切换计算页")
        step_start = time.time()

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

        # 步骤 2: 切换高级页
        step = TestStep(name="切换高级页")
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

        # 步骤 3: 检查基本功能
        step = TestStep(name="检查基本功能")
        step_start = time.time()

        # 检查是否有基本的 UI 元素
        missing = []

        # 检查搜索面板
        search = self.inspector.find_control(name="全量搜索")
        if not search:
            missing.append("搜索面板")

        if missing:
            step.status = "failed"
            step.message = f"缺失元素: {', '.join(missing)}"
        else:
            step.status = "passed"
            step.message = "基本功能正常"

        step.duration = time.time() - step_start
        scenario.steps.append(step)

        # 步骤 4: 截图
        step = TestStep(name="截图")
        step_start = time.time()

        screenshot_path = SCREENSHOT_PACKAGED_DIR / "exe_functionality.png"
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

        # 打包
        if not self.build_exe():
            self.report.end_time = time.time()
            return self.report

        # 启动 exe
        if not self.start_exe():
            self.report.end_time = time.time()
            return self.report

        # 运行测试场景
        scenarios_config = TEST_SCENARIOS.get("packaged", [])
        for config in scenarios_config:
            scenario = self.run_scenario(config)
            self.report.scenarios.append(scenario)

        # 停止 exe
        self.stop_exe()
        self.report.end_time = time.time()

        return self.report


def main() -> None:
    """主入口。"""
    import argparse

    parser = argparse.ArgumentParser(description="打包后 exe 测试")
    parser.add_argument(
        "--skip-build",
        action="store_true",
        help="跳过打包步骤，使用已有的 exe",
    )
    args = parser.parse_args()

    runner = PackagedTestRunner(skip_build=args.skip_build)
    report = runner.run_all()

    # 保存报告
    report_path = SCREENSHOT_PACKAGED_DIR / "report.md"
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
