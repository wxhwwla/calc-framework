# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""
Web 前端自动化测试

封装 Cypress E2E 测试，提供统一的测试接口。

用法：
    python scripts/auto_test/web_test.py
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
    SCREENSHOT_WEB_DIR,
    VITE_PORT,
    WEB_FRONTEND_DIR,
    ensure_dirs,
)

from utils.report import TestReport, TestScenario, TestStep

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


class WebTestRunner:
    """Web 前端测试运行器。

    负责启动 Vite dev server、运行 Cypress 测试、解析结果、生成报告。
    """

    def __init__(self) -> None:
        self.report = TestReport(title="Web 前端测试报告")
        self._dev_server: subprocess.Popen | None = None

    def start_dev_server(self) -> bool:
        """启动 Vite dev server。

        Returns:
            是否启动成功
        """
        logger.info("启动 Vite dev server...")

        try:
            self._dev_server = subprocess.Popen(
                ["npm", "run", "dev"],
                cwd=str(WEB_FRONTEND_DIR),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=True,
            )

            # 等待服务器启动
            time.sleep(5)

            # 检查服务器是否运行
            if self._dev_server.poll() is None:
                logger.info("Vite dev server 已启动 (端口: %d)", VITE_PORT)
                return True
            else:
                logger.error("Vite dev server 启动失败")
                return False

        except Exception as e:
            logger.error("启动 Vite dev server 失败: %s", e)
            return False

    def stop_dev_server(self) -> None:
        """停止 Vite dev server。"""
        if self._dev_server:
            try:
                self._dev_server.terminate()
                self._dev_server.wait(timeout=5)
            except Exception:
                self._dev_server.kill()
            self._dev_server = None
            logger.info("Vite dev server 已停止")

    def run_cypress(self) -> tuple[bool, str]:
        """运行 Cypress 测试。

        Returns:
            (是否成功, 输出文本)
        """
        logger.info("运行 Cypress 测试...")

        try:
            result = subprocess.run(
                ["npx", "cypress", "run"],
                cwd=str(WEB_FRONTEND_DIR),
                capture_output=True,
                text=True,
                timeout=300,
                shell=True,
            )

            output = result.stdout + result.stderr
            success = result.returncode == 0

            if success:
                logger.info("Cypress 测试通过")
            else:
                logger.warning("Cypress 测试失败 (退出码: %d)", result.returncode)

            return success, output

        except subprocess.TimeoutExpired:
            logger.error("Cypress 测试超时")
            return False, "测试超时"
        except Exception as e:
            logger.error("运行 Cypress 失败: %s", e)
            return False, str(e)

    def parse_cypress_output(self, output: str) -> list[dict]:
        """解析 Cypress 输出。

        Args:
            output: Cypress 输出文本

        Returns:
            解析后的测试结果列表
        """
        results = []
        current_spec = None
        current_test = None

        for line in output.split("\n"):
            line = line.strip()

            # 检测 spec 文件
            if line.startswith("Running:") or line.startswith("✓"):
                if ".cy.ts" in line or ".cy.tsx" in line:
                    current_spec = line.split("/")[-1].split(" ")[0]

            # 检测测试用例
            if line.startswith("✓") or line.startswith("✗"):
                status = "passed" if line.startswith("✓") else "failed"
                name = line[1:].strip().split("(")[0].strip()
                current_test = {
                    "spec": current_spec,
                    "name": name,
                    "status": status,
                }
                results.append(current_test)

            # 检测失败详情
            if current_test and current_test["status"] == "failed":
                if "AssertionError" in line or "Error" in line:
                    current_test["error"] = line

        return results

    def run_scenario(self, cypress_results: list[dict]) -> TestScenario:
        """将 Cypress 结果转换为测试场景。

        Args:
            cypress_results: Cypress 测试结果

        Returns:
            测试场景
        """
        scenario = TestScenario(
            name="Cypress E2E 测试",
            description="Web 前端端到端测试",
        )
        scenario.start_time = time.time()

        for result in cypress_results:
            step = TestStep(
                name=f"[{result.get('spec', '?')}] {result['name']}",
                status=result["status"],
                message=result.get("error", ""),
            )
            scenario.steps.append(step)

        scenario.end_time = time.time()
        scenario.status = "passed" if scenario.failed_count == 0 else "failed"

        return scenario

    def collect_screenshots(self) -> None:
        """收集 Cypress 失败截图。"""
        cypress_screenshots = WEB_FRONTEND_DIR / "cypress" / "screenshots"
        if not cypress_screenshots.exists():
            return

        # 复制截图到测试报告目录
        import shutil

        for screenshot in cypress_screenshots.rglob("*.png"):
            dest = SCREENSHOT_WEB_DIR / screenshot.name
            shutil.copy2(screenshot, dest)
            logger.info("收集截图: %s", dest)

    def run_all(self) -> TestReport:
        """运行所有测试。

        Returns:
            测试报告
        """
        ensure_dirs()
        self.report.start_time = time.time()

        # 启动 dev server
        if not self.start_dev_server():
            self.report.end_time = time.time()
            return self.report

        # 运行 Cypress
        _success, output = self.run_cypress()

        # 解析结果
        cypress_results = self.parse_cypress_output(output)
        scenario = self.run_scenario(cypress_results)
        self.report.scenarios.append(scenario)

        # 收集截图
        self.collect_screenshots()

        # 停止 dev server
        self.stop_dev_server()
        self.report.end_time = time.time()

        return self.report


def main() -> None:
    """主入口。"""
    runner = WebTestRunner()
    report = runner.run_all()

    # 保存报告
    report_path = SCREENSHOT_WEB_DIR / "report.md"
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
