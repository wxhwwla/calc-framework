# SPDX-License-Identifier: AGPL-3.0
"""数据沙箱单元测试。

覆盖以下场景：
- validate: 合法数据、缺失字段、错误类型、空数据
- test: 实体命名、技能数量、倍率合理性、实体类型
- report: Markdown 生成、报告属性
- diff: 有差异 / 无差异比较
- error handling: 文件不存在、JSON 格式错误
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import pytest

from tools.data_sandbox import Validator, Tester, Reporter
from tools.data_sandbox.validator import ValidationResult, EntityError
from tools.data_sandbox.tester import TestResult, TestResultItem


# ── 测试辅助 ──


_VALID_ENTITY = {
    "名称": "测试角色",
    "_entity_type": "character",
    "星级": 5,
    "类型": "近卫",
    "技能": [
        {
            "名称": "战技",
            "标签": "主动",
            "百分比": True,
            "段": [
                {"倍率": [100, 110, 120], "伤害类型": "物理"},
            ],
        },
        {
            "名称": "主能力值+",
            "标签": "被动",
            "百分比": False,
            "段": [
                {"倍率": [50, 55, 60]},
            ],
        },
    ],
}

_VALID_ENTITY_2 = {
    "名称": "测试武器",
    "_entity_type": "weapon",
    "星级": 4,
    "类型": "单手剑",
    "技能": [
        {
            "名称": "攻击力+",
            "标签": "被动",
            "百分比": True,
            "段": [
                {"倍率": [200, 220, 240]},
            ],
        },
    ],
}

_INVALID_ENTITY_MISSING_FIELDS = {
    "名称": "坏角色",
    "技能": [
        {
            "名称": "",
            "标签": "未知",
            "段": [],
        },
    ],
}

_INVALID_ENTITY_WRONG_TYPES = {
    "名称": "类型错误",
    "技能": [
        {
            "名称": "技能1",
            "标签": "主动",
            "百分比": "yes",
            "段": [
                {"倍率": [1.5, 2.5, "abc"]},
            ],
        },
    ],
}


def _write_temp_json(data, suffix=".json"):
    """将数据写入临时 JSON 文件并返回路径。"""
    f = tempfile.NamedTemporaryFile(
        mode="w", suffix=suffix, delete=False, encoding="utf-8"
    )
    json.dump(data, f, ensure_ascii=False)
    f.close()
    return f.name


# ══════════════════════════════════════════════════════════════
# 1. Validator 测试
# ══════════════════════════════════════════════════════════════


class TestValidator:
    """Validator 单元测试。"""

    def test_validate_valid_data(self):
        """校验合法数据应通过。"""
        v = Validator()
        result = v.validate([_VALID_ENTITY, _VALID_ENTITY_2])
        assert result.passed
        assert result.total_entities == 2
        assert result.total_errors == 0

    def test_validate_missing_fields(self):
        """校验缺失字段的数据应报告错误。"""
        v = Validator()
        result = v.validate([_INVALID_ENTITY_MISSING_FIELDS])
        assert not result.passed
        assert result.total_errors > 0
        # 应包含标签错误
        assert any("标签" in err for err in result.entities[0].errors)

    def test_validate_wrong_types(self):
        """校验类型错误的数据应报告错误（严格模式）。"""
        v = Validator()
        result = v.validate([_INVALID_ENTITY_WRONG_TYPES])
        assert not result.passed
        assert result.total_errors > 0

    def test_validate_empty_list(self):
        """校验空列表应报告错误。"""
        v = Validator()
        result = v.validate([])
        assert not result.passed
        assert result.total_entities == 1
        assert "为空" in result.entities[0].errors[0]

    def test_validate_from_file(self):
        """从文件校验合法数据应通过。"""
        path = _write_temp_json([_VALID_ENTITY])
        try:
            v = Validator()
            result = v.validate_file(path)
            assert result.passed
        finally:
            os.unlink(path)

    def test_validate_from_file_missing(self):
        """从文件校验不存在的文件应返回 parse_error。"""
        v = Validator()
        result = v.validate_file("/tmp/不存在_文件_12345.json")
        assert not result.passed
        assert result.parse_error is not None
        assert "不存在" in result.parse_error

    def test_validate_malformed_json(self):
        """校验格式错误的 JSON 应返回 parse_error。"""
        f = tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        )
        f.write('{"名称": "缺少结束括号"')
        f.close()
        try:
            v = Validator()
            result = v.validate_file(f.name)
            assert not result.passed
            assert result.parse_error is not None
        finally:
            os.unlink(f.name)

    def test_validate_dict_as_single_entity(self):
        """顶层为对象（单个实体）应该能正确处理。"""
        data = dict(_VALID_ENTITY)
        v = Validator()
        result = v.validate([data])
        assert result.passed


# ══════════════════════════════════════════════════════════════
# 2. Tester 测试
# ══════════════════════════════════════════════════════════════


class TestTester:
    """Tester 单元测试。"""

    def test_tester_valid_data(self):
        """测试合法数据应全部通过。"""
        t = Tester()
        result = t.test([_VALID_ENTITY])
        assert result.passed
        assert result.passed_count > 0
        assert result.failed_count == 0
        # 至少包含实体名称和技能相关测试
        assert any("实体名称" in item.test_name for item in result.items)

    def test_tester_empty_name(self):
        """测试空实体名称应失败。"""
        data = [{"名称": "", "技能": [{"名称": "s1", "标签": "主动", "百分比": True, "段": [{"倍率": [100]}]}]}]
        t = Tester()
        result = t.test(data)
        name_items = [item for item in result.items if item.test_name == "实体名称"]
        assert name_items
        assert not name_items[0].passed

    def test_tester_empty_skills(self):
        """测试无技能实体应报告技能数量失败。"""
        data = [{"名称": "空技能角色", "技能": []}]
        t = Tester()
        result = t.test(data)
        skill_items = [item for item in result.items if "技能数量" in item.test_name]
        assert skill_items
        assert not skill_items[0].passed

    def test_tester_zero_rates(self):
        """测试倍率全为 0 应报告。"""
        data = [{"名称": "零倍率", "技能": [{"名称": "s1", "标签": "主动", "百分比": True, "段": [{"倍率": [0, 0, 0]}]}]}]
        t = Tester()
        result = t.test(data)
        assert not result.passed
        assert any("倍率有效" in item.test_name and not item.passed for item in result.items)

    def test_tester_negative_rates(self):
        """测试含负数倍率应报告。"""
        data = [{"名称": "负倍率", "技能": [{"名称": "s1", "标签": "主动", "百分比": True, "段": [{"倍率": [-10, 100]}]}]}]
        t = Tester()
        result = t.test(data)
        assert not result.passed
        assert any("倍率范围" in item.test_name for item in result.items)

    def test_tester_valid_entity_type(self):
        """测试合法实体类型应通过。"""
        data = [{"名称": "角色", "_entity_type": "character", "技能": [{"名称": "s1", "标签": "主动", "百分比": True, "段": [{"倍率": [100]}]}]}]
        t = Tester()
        result = t.test(data)
        type_items = [item for item in result.items if "实体类型" in item.test_name]
        assert type_items
        assert type_items[0].passed

    def test_tester_invalid_entity_type(self):
        """测试非法实体类型应失败。"""
        data = [{"名称": "角色", "_entity_type": "illegal_type", "技能": [{"名称": "s1", "标签": "主动", "百分比": True, "段": [{"倍率": [100]}]}]}]
        t = Tester()
        result = t.test(data)
        type_items = [item for item in result.items if "实体类型" in item.test_name]
        assert type_items
        assert not type_items[0].passed


# ══════════════════════════════════════════════════════════════
# 3. Reporter 测试
# ══════════════════════════════════════════════════════════════


class TestReporter:
    """Reporter 单元测试。"""

    def test_report_markdown_generation(self):
        """生成合法数据的 Markdown 报告应包含通过信息。"""
        r = Reporter()
        report = r.generate([_VALID_ENTITY], source_file="test.json")
        md = r.render_markdown(report)
        assert "数据沙箱报告" in md
        assert "Schema" in md
        assert "test.json" in md
        assert report.validation.passed
        assert report.test.passed

    def test_report_with_invalid_data(self):
        """生成非法数据的报告应包含错误信息。"""
        r = Reporter()
        report = r.generate([_INVALID_ENTITY_MISSING_FIELDS], source_file="bad.json")
        md = r.render_markdown(report)
        assert "校验失败" in md or "失败" in md

    def test_report_summary_property(self):
        """Report.summary 应返回有意义的文字。"""
        r = Reporter()
        report = r.generate([_VALID_ENTITY], source_file="t.json")
        summary = report.summary
        assert "校验通过" in summary
        assert "测试通过" in summary

    def test_report_diff_included(self):
        """生成报告时包含差异比较应输出差异章节。"""
        old_data = [dict(_VALID_ENTITY, 名称="旧角色")]
        new_data = [dict(_VALID_ENTITY, 名称="旧角色"), dict(_VALID_ENTITY_2)]
        r = Reporter()
        report = r.generate(new_data, source_file="new.json", reference_data=old_data)
        md = r.render_markdown(report)
        assert "差异摘要" in md
        assert report.diff is not None
        assert report.diff.has_changes

    def test_report_diff_no_changes(self):
        """生成报告时包含无差异比较应输出无差异信息。"""
        data = [_VALID_ENTITY]
        r = Reporter()
        report = r.generate(data, source_file="same.json", reference_data=list(data))
        md = r.render_markdown(report)
        assert report.diff is not None
        assert not report.diff.has_changes

    def test_report_from_file(self):
        """从文件生成报告应正常工作。"""
        path = _write_temp_json([_VALID_ENTITY])
        try:
            r = Reporter()
            report = r.generate_from_file(path)
            assert report.validation.passed
            assert report.test.passed
            assert str(path) in report.source_file
        finally:
            os.unlink(path)


# ══════════════════════════════════════════════════════════════
# 4. Integration / Edge cases
# ══════════════════════════════════════════════════════════════


class TestIntegration:
    """集成测试 — 多个模块协作场景。"""

    def test_full_workflow_valid(self):
        """完整工作流：合法数据 — validate + test + report 全部通过。"""
        data = [_VALID_ENTITY, _VALID_ENTITY_2]

        v = Validator()
        vr = v.validate(data)
        assert vr.passed

        t = Tester()
        tr = t.test(data)
        assert tr.passed

        r = Reporter()
        report = r.generate(data, source_file="full_test.json")
        assert report.validation.passed
        assert report.test.passed

    def test_full_workflow_invalid(self):
        """完整工作流：非法数据 — 应报告错误。"""
        data = [_INVALID_ENTITY_MISSING_FIELDS]

        v = Validator()
        vr = v.validate(data)
        assert not vr.passed

        t = Tester()
        tr = t.test(data)
        assert not tr.passed

        r = Reporter()
        report = r.generate(data, source_file="invalid.json")
        assert not report.validation.passed
        assert not report.test.passed

    def test_error_handling_file_not_found(self):
        """文件不存在 — 应优雅处理。"""
        t = Tester()
        tr = t.test_file("/tmp/不存在的文件.json")
        assert not tr.passed
        assert tr.load_error is not None

    def test_error_handling_empty_json_array(self):
        """空 JSON 数组 — 应返回加载后的空列表。"""
        path = _write_temp_json([])
        try:
            v = Validator()
            result = v.validate_file(path)
            assert not result.passed
            assert "为空" in result.entities[0].errors[0]
        finally:
            os.unlink(path)

    def test_error_handling_top_level_non_array(self):
        """顶层不是数组也不是对象 — 应返回 parse_error。"""
        path = _write_temp_json("just a string")
        try:
            v = Validator()
            result = v.validate_file(path)
            assert not result.passed
        finally:
            os.unlink(path)
