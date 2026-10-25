# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""
测试报告生成

生成 Markdown 格式的测试报告。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass
class TestStep:
    """测试步骤。"""

    name: str
    status: str = "pending"  # pending, passed, failed, skipped
    message: str = ""
    screenshot: str | None = None
    duration: float = 0.0


@dataclass
class TestScenario:
    """测试场景。"""

    name: str
    description: str
    steps: list[TestStep] = field(default_factory=list)
    status: str = "pending"  # pending, running, passed, failed
    start_time: float | None = None
    end_time: float | None = None

    @property
    def duration(self) -> float:
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return 0.0

    @property
    def passed_count(self) -> int:
        return sum(1 for s in self.steps if s.status == "passed")

    @property
    def failed_count(self) -> int:
        return sum(1 for s in self.steps if s.status == "failed")

    @property
    def total_count(self) -> int:
        return len(self.steps)


@dataclass
class TestReport:
    """测试报告。"""

    title: str
    scenarios: list[TestScenario] = field(default_factory=list)
    start_time: float | None = None
    end_time: float | None = None

    @property
    def duration(self) -> float:
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return 0.0

    @property
    def total_scenarios(self) -> int:
        return len(self.scenarios)

    @property
    def passed_scenarios(self) -> int:
        return sum(1 for s in self.scenarios if s.status == "passed")

    @property
    def failed_scenarios(self) -> int:
        return sum(1 for s in self.scenarios if s.status == "failed")

    @property
    def total_steps(self) -> int:
        return sum(s.total_count for s in self.scenarios)

    @property
    def passed_steps(self) -> int:
        return sum(s.passed_count for s in self.scenarios)

    @property
    def failed_steps(self) -> int:
        return sum(s.failed_count for s in self.scenarios)

    def to_markdown(self) -> str:
        """生成 Markdown 格式的报告。"""
        lines = []
        lines.append(f"# {self.title}")
        lines.append("")
        lines.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"**总耗时**: {self.duration:.1f} 秒")
        lines.append("")

        # 摘要
        lines.append("## 测试摘要")
        lines.append("")
        lines.append("| 指标 | 数值 |")
        lines.append("|------|------|")
        lines.append(f"| 场景总数 | {self.total_scenarios} |")
        lines.append(f"| 通过场景 | {self.passed_scenarios} |")
        lines.append(f"| 失败场景 | {self.failed_scenarios} |")
        lines.append(f"| 步骤总数 | {self.total_steps} |")
        lines.append(f"| 通过步骤 | {self.passed_steps} |")
        lines.append(f"| 失败步骤 | {self.failed_steps} |")
        lines.append("")

        # 详细结果
        lines.append("## 详细结果")
        lines.append("")

        for scenario in self.scenarios:
            status_icon = "✅" if scenario.status == "passed" else "❌"
            lines.append(f"### {status_icon} {scenario.name}")
            lines.append("")
            lines.append(f"**描述**: {scenario.description}")
            lines.append(f"**耗时**: {scenario.duration:.1f} 秒")
            lines.append("")

            lines.append("| 步骤 | 状态 | 耗时 | 备注 |")
            lines.append("|------|------|------|------|")

            for step in scenario.steps:
                step_icon = {
                    "passed": "✅",
                    "failed": "❌",
                    "skipped": "⏭️",
                    "pending": "⏳",
                }.get(step.status, "❓")

                screenshot_link = ""
                if step.screenshot:
                    screenshot_link = f"[截图]({step.screenshot})"

                lines.append(f"| {step.name} | {step_icon} | {step.duration:.1f}s | {step.message} {screenshot_link} |")

            lines.append("")

            # 失败步骤详情
            failed_steps = [s for s in scenario.steps if s.status == "failed"]
            if failed_steps:
                lines.append("**失败详情**:")
                lines.append("")
                for step in failed_steps:
                    lines.append(f"- **{step.name}**: {step.message}")
                    if step.screenshot:
                        lines.append(f"  - 截图: {step.screenshot}")
                lines.append("")

        # 问题汇总
        all_failed = []
        for scenario in self.scenarios:
            for step in scenario.steps:
                if step.status == "failed":
                    all_failed.append((scenario.name, step))

        if all_failed:
            lines.append("## 问题汇总")
            lines.append("")
            lines.append("| 场景 | 步骤 | 问题描述 | 截图 |")
            lines.append("|------|------|----------|------|")
            for scenario_name, step in all_failed:
                screenshot = step.screenshot or "-"
                lines.append(f"| {scenario_name} | {step.name} | {step.message} | {screenshot} |")
            lines.append("")

        return "\n".join(lines)

    def save(self, output_path: Path | str) -> Path:
        """保存报告到文件。

        Args:
            output_path: 输出路径

        Returns:
            报告文件路径
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        content = self.to_markdown()
        output_path.write_text(content, encoding="utf-8")

        return output_path
