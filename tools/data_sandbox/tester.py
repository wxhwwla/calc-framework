#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""数据测试器 — 加载自定义数据并运行基本健全性测试。

在隔离环境中执行，不会修改任何真实数据文件。
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from tools.data_pipeline.schema import EntitySchema, SkillSchema, SegmentSchema


@dataclass
class TestResultItem:
    """单个测试项的详细结果。"""
    entity_name: str
    test_name: str
    passed: bool
    detail: str


@dataclass
class TestResult:
    """完整测试结果。"""
    items: List[TestResultItem] = field(default_factory=list)
    load_error: Optional[str] = None

    @property
    def passed(self) -> bool:
        if self.load_error:
            return False
        return all(item.passed for item in self.items)

    @property
    def total(self) -> int:
        return len(self.items)

    @property
    def passed_count(self) -> int:
        return sum(1 for item in self.items if item.passed)

    @property
    def failed_count(self) -> int:
        return sum(1 for item in self.items if not item.passed)


class Tester:
    """数据测试器 — 对 EntitySchema 数据执行基本健全性测试。

    测试内容包括：
    - 实体命名检查（名称非空）
    - 技能数量检查
    - 倍率值合理性检查（非负、类型正确）
    - 段完整性检查
    """
    __test__ = False  # 防止 pytest 自动发现

    def test_file(self, path: str | Path) -> TestResult:
        """读取并测试 JSON 文件中的数据。

        Args:
            path: JSON 文件路径

        Returns:
            TestResult 包含所有测试项结果
        """
        try:
            data = self._load_json(path)
        except ValueError as e:
            return TestResult(load_error=str(e))

        return self.test(data)

    def test(self, data: List[Dict[str, Any]]) -> TestResult:
        """测试内存中的 EntitySchema 列表。

        Args:
            data: 实体列表

        Returns:
            TestResult 包含所有测试项结果
        """
        result = TestResult()

        for i, entity in enumerate(data):
            name = entity.get("名称", f"[{i}]")
            self._test_entity_name(entity, name, result)
            self._test_skills(entity, name, result)
            self._test_entity_type(entity, name, result)

        return result

    def _test_entity_name(
        self, entity: Dict[str, Any], name: str, result: TestResult,
    ) -> None:
        item = TestResultItem(
            entity_name=name,
            test_name="实体名称",
            passed=bool(name.strip() if isinstance(name, str) else False),
            detail=f"名称为空" if not name else f"名称: {name}",
        )
        result.items.append(item)

    def _test_skills(
        self, entity: Dict[str, Any], name: str, result: TestResult,
    ) -> None:
        skills = entity.get("技能", [])

        if not skills:
            result.items.append(TestResultItem(
                entity_name=name,
                test_name="技能数量",
                passed=False,
                detail=f"技能列表为空，至少需要 1 个技能",
            ))
            return

        skill_names = []
        for j, skill in enumerate(skills):
            skill_name = skill.get("名称", f"技能[{j}]")
            skill_names.append(skill_name)
            self._test_skill_detail(skill, name, skill_name, j, result)

        result.items.append(TestResultItem(
            entity_name=name,
            test_name="技能数量",
            passed=True,
            detail=f"共 {len(skills)} 个技能: {', '.join(skill_names)}",
        ))

    def _test_skill_detail(
        self, skill: Dict[str, Any], entity_name: str,
        skill_name: str, index: int, result: TestResult,
    ) -> None:
        label = skill.get("标签", "")
        if label not in ("主动", "被动"):
            result.items.append(TestResultItem(
                entity_name=entity_name,
                test_name=f"技能 '{skill_name}' 标签",
                passed=False,
                detail=f"标签应为 '主动' 或 '被动', 实际 '{label}'",
            ))

        percent = skill.get("百分比")
        if percent is None:
            result.items.append(TestResultItem(
                entity_name=entity_name,
                test_name=f"技能 '{skill_name}' 百分比",
                passed=False,
                detail="缺少 '百分比' 字段",
            ))

        segments = skill.get("段", [])
        if not segments:
            result.items.append(TestResultItem(
                entity_name=entity_name,
                test_name=f"技能 '{skill_name}' 段完整性",
                passed=False,
                detail="段列表为空",
            ))
            return

        for k, seg in enumerate(segments):
            self._test_segment(seg, entity_name, skill_name, k, result)

    def _test_segment(
        self, seg: Dict[str, Any], entity_name: str,
        skill_name: str, seg_index: int, result: TestResult,
    ) -> None:
        rates = seg.get("倍率", [])
        if not rates:
            result.items.append(TestResultItem(
                entity_name=entity_name,
                test_name=f"技能 '{skill_name}' 段[{seg_index}] 倍率",
                passed=False,
                detail="倍率列表为空",
            ))
            return

        for v in rates:
            if not isinstance(v, int):
                result.items.append(TestResultItem(
                    entity_name=entity_name,
                    test_name=f"技能 '{skill_name}' 段[{seg_index}] 倍率类型",
                    passed=False,
                    detail=f"倍率值应为 int, 实际 {type(v).__name__} ({v})",
                ))
                break

        non_negative = all(v >= 0 for v in rates if isinstance(v, int))
        if not non_negative:
            result.items.append(TestResultItem(
                entity_name=entity_name,
                test_name=f"技能 '{skill_name}' 段[{seg_index}] 倍率范围",
                passed=False,
                detail="倍率值包含负数",
            ))

        has_positive = any(v > 0 for v in rates if isinstance(v, int))
        if not has_positive:
            result.items.append(TestResultItem(
                entity_name=entity_name,
                test_name=f"技能 '{skill_name}' 段[{seg_index}] 倍率有效",
                passed=False,
                detail="所有倍率值均为 0",
            ))

    def _test_entity_type(
        self, entity: Dict[str, Any], name: str, result: TestResult,
    ) -> None:
        etype = entity.get("_entity_type")
        valid_types = {"character", "weapon", "equipment", "mount", "other"}
        if etype is not None and etype not in valid_types:
            result.items.append(TestResultItem(
                entity_name=name,
                test_name="实体类型",
                passed=False,
                detail=f"实体类型 '{etype}' 不在标准集合中: {', '.join(sorted(valid_types))}",
            ))
        else:
            result.items.append(TestResultItem(
                entity_name=name,
                test_name="实体类型",
                passed=True,
                detail=f"实体类型: {etype or '(未指定)'}",
            ))

    @staticmethod
    def _load_json(path: str | Path) -> List[Dict[str, Any]]:
        path = Path(path)
        if not path.exists():
            raise ValueError(f"文件不存在: {path}")
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return [data]
        if isinstance(data, list):
            if not data:
                return []
            if isinstance(data[0], dict):
                return data
        raise ValueError(
            f"不支持的 JSON 格式：顶层须为对象或对象数组，"
            f"实际类型 {type(data).__name__}"
        )
