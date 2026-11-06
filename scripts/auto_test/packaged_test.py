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
    APP_WINDOW_TITLE,
    BUILD_SCRIPT,
    BUILD_TIMEOUT,
    DIST_DIR,
    PACKAGED_APP_DIR_NAME,
    PACKAGED_BUILD_TARGET,
    PACKAGED_EXE_ARGS,
    PACKAGED_EXE_NAME,
    PACKAGED_LAUNCHER_TITLE,
    PACKAGED_STARTUP_TIMEOUT,
    SCREENSHOT_PACKAGED_DIR,
    STEP_TIMEOUT,
    TEST_SCENARIOS,
    ensure_dirs,
)

from utils.launch import start_exe_process
from utils.qt_inspector import QtInspector, find_visible_window
from utils.report import TestReport, TestScenario, TestStep, check_required_steps

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
        self._launcher_inspector: QtInspector | None = None
        self._launcher_startup_seconds: float | None = None
        self._endfield_startup_seconds: float | None = None

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
                    PACKAGED_BUILD_TARGET,
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
            DIST_DIR / PACKAGED_APP_DIR_NAME / PACKAGED_EXE_NAME,
            DIST_DIR / PACKAGED_EXE_NAME,
        ]

        for path in possible_paths:
            if path.exists():
                self._exe_path = path
                logger.info("找到 exe: %s", path)
                return

        # 递归查找
        for exe in DIST_DIR.rglob("*.exe"):
            if exe.name == PACKAGED_EXE_NAME:
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

        # 避免连接到上一次运行遗留的窗口：有旧实例时直接判失败
        existing = find_visible_window(PACKAGED_LAUNCHER_TITLE) or find_visible_window(APP_WINDOW_TITLE)
        if existing is not None:
            logger.error("检测到已在运行的实例：%s，请先关闭后再运行", existing[1])
            return False

        try:
            started_at = time.monotonic()
            self._process = start_exe_process(self._exe_path, PACKAGED_EXE_ARGS)

            # 先等待启动器窗口，验证真实链路而不是直接进入游戏
            logger.info("等待启动器窗口出现 (超时: %ds)...", PACKAGED_STARTUP_TIMEOUT)
            self._launcher_inspector = QtInspector()
            if not self._launcher_inspector.connect(PACKAGED_LAUNCHER_TITLE, timeout=PACKAGED_STARTUP_TIMEOUT):
                logger.error("启动器窗口未出现")
                self.stop_exe()
                return False
            self._launcher_startup_seconds = time.monotonic() - started_at

            # 启动器会在窗口就绪后自动拉起终末地
            remaining = max(PACKAGED_STARTUP_TIMEOUT - self._launcher_startup_seconds, 10)
            logger.info("等待终末地窗口出现 (超时: %.0fs)...", remaining)
            if not self.inspector.connect(APP_WINDOW_TITLE, timeout=remaining):
                logger.error("终末地窗口未出现")
                self.stop_exe()
                return False
            self._endfield_startup_seconds = time.monotonic() - started_at

            logger.info(
                "exe 启动成功（启动器 %.1fs，终末地累计 %.1fs）",
                self._launcher_startup_seconds,
                self._endfield_startup_seconds,
            )
            return True

        except Exception as e:
            logger.error("启动 exe 失败: %s", e)
            return False

    def stop_exe(self) -> None:
        """停止 exe 及其 onefile 子进程。"""
        if self._process:
            try:
                # PyInstaller onefile 会派生实际应用子进程，必须按进程树结束
                subprocess.run(
                    ["taskkill", "/PID", str(self._process.pid), "/T", "/F"],
                    capture_output=True,
                    timeout=10,
                    check=False,
                )
            except Exception:
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
            scenario.steps.append(TestStep(name="执行场景", status="failed", message=f"未知场景: {scenario.name}"))

        missing = check_required_steps(scenario, scenario_config.get("steps", []))
        if missing:
            scenario.steps.append(
                TestStep(
                    name="必要步骤未执行",
                    status="failed",
                    message="、".join(missing),
                )
            )

        scenario.end_time = time.time()
        scenario.status = "passed" if scenario.failed_count == 0 else "failed"

        return scenario

    def _test_exe_startup(self, scenario: TestScenario) -> None:
        """测试 exe 经启动器启动终末地。"""
        # 步骤 1: 等待启动器
        step = TestStep(name="等待启动器")
        step_start = time.time()

        launcher_ok = bool(
            self._launcher_inspector
            and self._launcher_inspector.main_window
            and self._launcher_inspector.main_window.exists()
        )
        if launcher_ok:
            step.status = "passed"
            step.message = f"启动器就绪，耗时 {self._launcher_startup_seconds or 0:.1f}s"
        else:
            step.status = "failed"
            step.message = "启动器窗口未找到"

        step.duration = time.time() - step_start
        scenario.steps.append(step)

        # 步骤 2: 等待主窗口（终末地）
        step = TestStep(name="等待主窗口")
        step_start = time.time()

        if self.inspector.main_window and self.inspector.main_window.exists():
            step.status = "passed"
            step.message = f"终末地就绪，累计 {self._endfield_startup_seconds or 0:.1f}s"
        else:
            step.status = "failed"
            step.message = "终末地窗口未找到"

        step.duration = time.time() - step_start
        scenario.steps.append(step)

        # 步骤 3: 截图
        step = TestStep(name="截图")
        step_start = time.time()

        screenshot_path = SCREENSHOT_PACKAGED_DIR / "exe_startup.png"
        try:
            self.inspector.screenshot(str(screenshot_path))
            step.status = "passed"
            step.screenshot = screenshot_path.name
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

        # 步骤 2: 确认计算（等待真实按钮状态变化，不用固定睡眠）
        step = TestStep(name="确认计算")
        step_start = time.time()

        confirm_btn = self.inspector.find_control(name="确认选择（待更新）")
        if confirm_btn is None:
            confirm_btn = self.inspector.find_control(name="确认选择")
        if confirm_btn is None:
            step.status = "failed"
            step.message = "未找到确认按钮"
        elif not self.inspector.click(confirm_btn, wait=0.2):
            step.status = "failed"
            step.message = "点击确认按钮失败"
        else:
            confirmed = self.inspector.wait_for_control(name="已确认", timeout=STEP_TIMEOUT)
            if confirmed is not None:
                step.status = "passed"
                step.message = "确认完成，乘区表已刷新"
            else:
                step.status = "failed"
                step.message = f"确认后 {STEP_TIMEOUT}s 内未出现「已确认」"

        step.duration = time.time() - step_start
        scenario.steps.append(step)

        # 步骤 3: 读取乘区表（确认后仍在计算页）
        step = TestStep(name="读取乘区表")
        step_start = time.time()

        zone_lines = self._read_zone_lines()
        if len(zone_lines) >= 2:
            zone_path = SCREENSHOT_PACKAGED_DIR / "zone_table.txt"
            zone_path.write_text("\n".join(zone_lines), encoding="utf-8")
            step.status = "passed"
            step.message = f"读取乘区行 {len(zone_lines)} 条"
        else:
            step.status = "failed"
            step.message = "未读取到乘区表内容"

        step.duration = time.time() - step_start
        scenario.steps.append(step)

        # 步骤 4: 切换高级页
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

        # 步骤 5: 检查基本功能
        step = TestStep(name="检查基本功能")
        step_start = time.time()

        # 检查是否有基本的 UI 元素
        missing = []

        # 检查搜索面板（按钮文案来自 zh-CN.json 的 desktop.endfield.fullSearch）
        search = self.inspector.find_control(name="全量遍历搜索")
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

        # 步骤 6: 截图
        step = TestStep(name="截图")
        step_start = time.time()

        screenshot_path = SCREENSHOT_PACKAGED_DIR / "exe_functionality.png"
        try:
            self.inspector.screenshot(str(screenshot_path))
            step.status = "passed"
            step.screenshot = screenshot_path.name
        except Exception as e:
            step.status = "failed"
            step.message = f"截图失败: {e}"

        step.duration = time.time() - step_start
        scenario.steps.append(step)

    def _read_zone_lines(self) -> list[str]:
        """读取确认后的乘区表文本行。

        Returns:
            乘区表各单元格文本；未找到乘区表时返回空列表。
        """
        header = self.inspector.find_control(name="=== 乘区数据 ===")
        if header is None:
            return []

        cells: list = []
        try:
            table = header.parent()
            # Qt 的 QTableWidget 单元格在 UIA 下可能是 DataItem 或 Text
            for control_type in ("DataItem", "Text"):
                found = table.descendants(control_type=control_type)
                if found:
                    cells = found
                    break
        except Exception as e:
            logger.warning("读取乘区表失败: %s", e)
            return []

        lines: list[str] = []
        for cell in cells:
            text = (cell.element_info.name or "").strip()
            if text:
                lines.append(text)
        return lines

    def run_all(self) -> TestReport:
        """运行所有测试场景。

        Returns:
            测试报告
        """
        ensure_dirs()
        self.report.start_time = time.time()

        # 打包
        if not self.build_exe():
            self.report.mark_infra_failed("打包失败或未找到 exe，未执行测试场景")
            self.report.end_time = time.time()
            return self.report

        # 启动 exe
        if not self.start_exe():
            self.report.mark_infra_failed("exe 启动失败，未执行测试场景")
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
    if report.infra_failed:
        print(f"基础设施失败: {report.infra_error}")
    if report.total_scenarios == 0:
        print("警告: 未执行任何测试场景")
    print(f"报告已保存: {report_path}")
    print("=" * 60)

    # 返回退出码：启动失败、0 场景、失败场景都会返回非零
    sys.exit(report.exit_code)


if __name__ == "__main__":
    main()
