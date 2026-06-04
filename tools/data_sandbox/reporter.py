#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""报告生成器 — 生成包含校验结果 + 测试结果 + 差异摘要的 Markdown 报告。

在隔离环境中生成报告，不会修改任何真实数据文件。
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from tools.data_pipeline.diff import (
    compare_entities,
    render_text as _render_diff_text,
)

from .tester import Tester, TestResult
from .validator import Validator, ValidationResult


@dataclass
class DiffSummary:
    """差异摘要。"""

    total_old: int
    total_new: int
    added: int
    removed: int
    modified: int
    detail_lines: List[str] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        """has_changes 实现。"""
        return self.added > 0 or self.removed > 0 or self.modified > 0


@dataclass
class Report:
    """完整的 Sandbox 报告。"""

    source_file: str
    validation: ValidationResult
    test: TestResult
    diff: DiffSummary | None = None
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    @property
    def summary(self) -> str:
        """summary 实现。"""
        parts = []
        parts.append(
            "✅ 校验通过" if self.validation.passed else f"❌ 校验失败 ({self.validation.total_errors} 个错误)"
        )
        parts.append(
            "✅ 测试通过" if self.test.passed else f"❌ 测试失败 ({self.test.failed_count}/{self.test.total} 项未通过)"
        )
        if self.diff:
            if self.diff.has_changes:
                parts.append("🔍 有差异")
            else:
                parts.append("✅ 无差异")
        return " | ".join(parts)


class Reporter:
    """报告生成器 — 整合校验、测试、差异结果生成 Markdown 报告。"""

    def __init__(self) -> None:
        self._validator = Validator()
        self._tester = Tester()

    def generate(
        self,
        data: List[Dict[str, Any]],
        source_file: str = "(内存数据)",
        reference_data: List[Dict[str, Any]] | None = None,
        reference_label: str = "local reference",
    ) -> Report:
        """生成完整报告。

        Args:
            data: 待测试的实体列表
            source_file: 源文件名（用于报告标题）
            reference_data: 可选，参考数据用于差异比较
            reference_label: 参考数据的描述标签

        Returns:
            Report 对象
        """
        vr = self._validator.validate(data)
        tr = self._tester.test(data)

        diff_summary: DiffSummary | None = None
        if reference_data is not None:
            diff_summary = self._compute_diff(data, reference_data, reference_label)

        return Report(
            source_file=source_file,
            validation=vr,
            test=tr,
            diff=diff_summary,
        )

    def generate_from_file(
        self,
        path: str | Path,
        reference_path: str | Path | None = None,
        reference_label: str = "local reference",
    ) -> Report:
        """从文件生成完整报告。

        Args:
            path: JSON 数据文件路径
            reference_path: 可选，参考 JSON 文件路径
            reference_label: 参考数据的描述标签

        Returns:
            Report 对象
        """
        from .validator import Validator

        v = Validator()
        data = v._load_json(path)

        ref_data: List[Dict[str, Any]] | None = None
        if reference_path:
            ref_data = v._load_json(reference_path)

        return self.generate(
            data,
            source_file=str(path),
            reference_data=ref_data,
            reference_label=reference_label,
        )

    def render_markdown(self, report: Report) -> str:
        """将 Report 渲染为 Markdown 字符串。

        Args:
            report: Report 对象

        Returns:
            Markdown 格式的报告文本
        """
        lines: List[str] = []
        lines.append("# 数据沙箱报告")
        lines.append("")
        lines.append(f"- **源文件**: `{report.source_file}`")
        lines.append(f"- **生成时间**: {report.timestamp}")
        lines.append(f"- **状态**: {report.summary}")
        lines.append("")

        self._render_validation_section(lines, report.validation)
        self._render_test_section(lines, report.test)
        if report.diff:
            self._render_diff_section(lines, report.diff)

        return "\n".join(lines)

    @staticmethod
    def _render_validation_section(
        lines: List[str],
        vr: ValidationResult,
    ) -> None:
        """_render_validation_section 实现。"""
        lines.append("## 一、Schema 校验")
        lines.append("")

        if vr.parse_error:
            lines.append(f"**解析错误**: {vr.parse_error}")
            lines.append("")
            return

        if vr.passed:
            lines.append(f"✅ **通过** — 共 {vr.total_entities} 个实体，0 个错误")
            lines.append("")
            return

        lines.append(f"❌ **失败** — 共 {vr.total_entities} 个实体，{vr.total_errors} 个错误")
        lines.append("")

        for entity in vr.entities:
            if entity.errors:
                lines.append(f"### 实体 [{entity.index}]: {entity.name}")
                for err in entity.errors:
                    lines.append(f"- ❌ {err}")
                lines.append("")

    @staticmethod
    def _render_test_section(
        lines: List[str],
        tr: TestResult,
    ) -> None:
        """_render_test_section 实现。"""
        lines.append("## 二、健全性测试")
        lines.append("")

        if tr.load_error:
            lines.append(f"**加载错误**: {tr.load_error}")
            lines.append("")
            return

        lines.append(f"共 {tr.total} 项测试，✅ {tr.passed_count} 项通过，❌ {tr.failed_count} 项未通过")
        lines.append("")

        failed = [item for item in tr.items if not item.passed]
        if failed:
            lines.append("### 失败项")
            lines.append("")
            for item in failed:
                lines.append(f"- ❌ **{item.entity_name}**: {item.test_name} — {item.detail}")
            lines.append("")

        passed = [item for item in tr.items if item.passed]
        if passed:
            lines.append("### 通过项")
            lines.append("")
            for item in passed:
                lines.append(f"- ✅ **{item.entity_name}**: {item.test_name} — {item.detail}")
            lines.append("")

    @staticmethod
    def _render_diff_section(
        lines: List[str],
        diff: DiffSummary,
    ) -> None:
        """_render_diff_section 实现。"""
        lines.append("## 三、差异摘要")
        lines.append("")

        lines.append("| 指标 | 值 |")
        lines.append("|------|----|")
        lines.append(f"| 参考数据 | {diff.total_old} 条 |")
        lines.append(f"| 测试数据 | {diff.total_new} 条 |")
        lines.append(f"| 新增 | {diff.added} |")
        lines.append(f"| 删除 | {diff.removed} |")
        lines.append(f"| 修改 | {diff.modified} |")
        lines.append("")

        if diff.has_changes:
            lines.append("### 详细差异")
            lines.append("")
            lines.append("```")
            for line in diff.detail_lines:
                lines.append(line)
            lines.append("```")
            lines.append("")

    @staticmethod
    def _compute_diff(
        data: List[Dict[str, Any]],
        reference_data: List[Dict[str, Any]],
        reference_label: str,
    ) -> DiffSummary:
        """_compute_diff 实现。"""
        result = compare_entities(reference_data, data)
        detail = _render_diff_text(result)

        return DiffSummary(
            total_old=result.total_old,
            total_new=result.total_new,
            added=len(result.added),
            removed=len(result.removed),
            modified=len(result.modified),
            detail_lines=detail.split("\n"),
        )
