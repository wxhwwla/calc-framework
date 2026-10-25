# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""
一键运行所有自动化测试

按顺序执行：
1. Web 前端测试（Cypress E2E）
2. 桌面应用测试（PySide6）
3. 打包后测试（PyInstaller exe）

用法：
    python scripts/auto_test/run_all.py                  # 运行所有测试
    python scripts/auto_test/run_all.py --skip-web        # 跳过 Web 测试
    python scripts/auto_test/run_all.py --skip-desktop    # 跳过桌面测试
    python scripts/auto_test/run_all.py --skip-packaged   # 跳过打包测试
    python scripts/auto_test/run_all.py --skip-build      # 跳过打包步骤（使用已有 exe）
"""

from __future__ import annotations

import argparse
import logging
import sys
import time
from pathlib import Path

# 添加项目路径
_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from config import SCREENSHOT_DIR, ensure_dirs

from utils.report import TestReport

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def run_web_tests() -> TestReport | None:
    """运行 Web 测试。"""
    try:
        from web_test import WebTestRunner

        runner = WebTestRunner()
        return runner.run_all()
    except Exception as e:
        logger.error("Web 测试失败: %s", e)
        return None


def run_desktop_tests() -> TestReport | None:
    """运行桌面应用测试。"""
    try:
        from desktop_test import DesktopTestRunner

        runner = DesktopTestRunner()
        return runner.run_all()
    except Exception as e:
        logger.error("桌面应用测试失败: %s", e)
        return None


def run_packaged_tests(skip_build: bool = False) -> TestReport | None:
    """运行打包后测试。"""
    try:
        from packaged_test import PackagedTestRunner

        runner = PackagedTestRunner(skip_build=skip_build)
        return runner.run_all()
    except Exception as e:
        logger.error("打包后测试失败: %s", e)
        return None


def generate_summary_report(reports: dict[str, TestReport | None]) -> str:
    """生成汇总报告。

    Args:
        reports: 各层测试报告

    Returns:
        汇总报告文本
    """
    lines = []
    lines.append("# 自动化测试汇总报告")
    lines.append("")
    lines.append(f"**生成时间**: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")

    # 摘要表格
    lines.append("## 测试摘要")
    lines.append("")
    lines.append("| 测试层 | 状态 | 场景通过 | 步骤通过 | 耗时 |")
    lines.append("|--------|------|----------|----------|------|")

    total_scenarios = 0
    passed_scenarios = 0
    total_steps = 0
    passed_steps = 0
    total_duration = 0.0

    for name, report in reports.items():
        if report is None:
            lines.append(f"| {name} | ⏭️ 跳过 | - | - | - |")
            continue

        status = "✅ 通过" if report.failed_scenarios == 0 else "❌ 失败"
        lines.append(
            f"| {name} | {status} | "
            f"{report.passed_scenarios}/{report.total_scenarios} | "
            f"{report.passed_steps}/{report.total_steps} | "
            f"{report.duration:.1f}s |"
        )

        total_scenarios += report.total_scenarios
        passed_scenarios += report.passed_scenarios
        total_steps += report.total_steps
        passed_steps += report.passed_steps
        total_duration += report.duration

    lines.append("")
    lines.append(
        f"**总计**: {passed_scenarios}/{total_scenarios} 场景通过, "
        f"{passed_steps}/{total_steps} 步骤通过, "
        f"耗时 {total_duration:.1f}s"
    )
    lines.append("")

    # 问题汇总
    all_problems = []
    for name, report in reports.items():
        if report is None:
            continue
        for scenario in report.scenarios:
            for step in scenario.steps:
                if step.status == "failed":
                    all_problems.append(
                        {
                            "layer": name,
                            "scenario": scenario.name,
                            "step": step.name,
                            "message": step.message,
                            "screenshot": step.screenshot,
                        }
                    )

    if all_problems:
        lines.append("## 问题汇总")
        lines.append("")
        lines.append("| 测试层 | 场景 | 步骤 | 问题描述 | 截图 |")
        lines.append("|--------|------|------|----------|------|")
        for p in all_problems:
            screenshot = p["screenshot"] or "-"
            lines.append(f"| {p['layer']} | {p['scenario']} | {p['step']} | {p['message']} | {screenshot} |")
        lines.append("")

    return "\n".join(lines)


def main() -> None:
    """主入口。"""
    parser = argparse.ArgumentParser(description="一键运行所有自动化测试")
    parser.add_argument("--skip-web", action="store_true", help="跳过 Web 测试")
    parser.add_argument("--skip-desktop", action="store_true", help="跳过桌面应用测试")
    parser.add_argument("--skip-packaged", action="store_true", help="跳过打包后测试")
    parser.add_argument("--skip-build", action="store_true", help="跳过打包步骤")
    args = parser.parse_args()

    ensure_dirs()

    print("=" * 60)
    print("终末地计算器 - 自动化测试")
    print("=" * 60)
    print()

    reports: dict[str, TestReport | None] = {}

    # 1. Web 测试
    if args.skip_web:
        logger.info("跳过 Web 测试")
        reports["Web 前端"] = None
    else:
        print("\n[1/3] 运行 Web 前端测试...")
        print("-" * 40)
        reports["Web 前端"] = run_web_tests()

    # 2. 桌面应用测试
    if args.skip_desktop:
        logger.info("跳过桌面应用测试")
        reports["桌面应用"] = None
    else:
        print("\n[2/3] 运行桌面应用测试...")
        print("-" * 40)
        reports["桌面应用"] = run_desktop_tests()

    # 3. 打包后测试
    if args.skip_packaged:
        logger.info("跳过打包后测试")
        reports["打包后 exe"] = None
    else:
        print("\n[3/3] 运行打包后测试...")
        print("-" * 40)
        reports["打包后 exe"] = run_packaged_tests(skip_build=args.skip_build)

    # 生成汇总报告
    summary = generate_summary_report(reports)
    summary_path = SCREENSHOT_DIR / "summary_report.md"
    summary_path.write_text(summary, encoding="utf-8")

    # 输出汇总
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
    print()
    print(summary)
    print()
    print(f"汇总报告已保存: {summary_path}")
    print(f"详细截图目录: {SCREENSHOT_DIR}")

    # 检查是否有失败
    has_failure = any(report and report.failed_scenarios > 0 for report in reports.values())
    if has_failure:
        print("\n❌ 存在测试失败，请检查报告")
        sys.exit(1)
    else:
        print("\n✅ 所有测试通过")


if __name__ == "__main__":
    main()
