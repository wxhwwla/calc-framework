# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""generate_adapter.layout_sections — 自定义分页/列数/分组测试。"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from tools.calc_mcp.build import BuildError, generate_adapter
from tools.calc_mcp.safety import ProjectScope
from tools.calc_mcp.spec import SpecError
from tools.generator.layout_sections import LayoutSectionsError, normalize_layout_sections


@pytest.fixture
def scope(tmp_path: Path) -> ProjectScope:
    (tmp_path / "framework" / "adapters").mkdir(parents=True)
    return ProjectScope(tmp_path)


def _variables() -> list[dict]:
    return [
        {"name": "atk", "type": "float", "source": "user_input", "default": 100},
        {"name": "mult", "type": "float", "source": "user_input", "default": 2},
    ]


def _steps() -> list[dict]:
    return [
        {"id": "final", "op": "*", "lhs": "atk", "rhs": "mult"},
        {"id": "zone_a", "op": "*", "lhs": "atk", "rhs": "2"},
        {"id": "zone_b", "op": "*", "lhs": "mult", "rhs": "3"},
    ]


def _outputs() -> list[dict]:
    return [
        {"name": "final", "node": "final", "label": "总伤害"},
        {"name": "zone_a", "node": "zone_a", "label": "乘区 A", "is_primary": False},
        {"name": "zone_b", "node": "zone_b", "label": "乘区 B", "is_primary": False},
    ]


def _two_page_sections() -> list[dict]:
    return [
        {"type": "inputs", "title": "输入参数", "source": "user_input", "tab": "计算"},
        {"type": "outputs", "title": "计算结果", "outputs": ["final"], "columns": 3, "tab": "计算"},
        {
            "type": "outputs",
            "title": "乘区明细",
            "outputs": ["zone_a", "zone_b"],
            "columns": 3,
            "tab": "乘区明细",
        },
    ]


def test_generate_adapter_writes_two_tab_layout(scope: ProjectScope, tmp_path: Path) -> None:
    """layout_sections 应一次生成带 tab/columns 的 layout，无需再手改文件。"""
    generate_adapter(
        scope,
        adapter_id="demo",
        variables=_variables(),
        formula_steps=_steps(),
        outputs=_outputs(),
        layout_sections=_two_page_sections(),
    )

    layout_path = tmp_path / "framework" / "adapters" / "demo" / "ui" / "layout.json"
    layout = json.loads(layout_path.read_text(encoding="utf-8"))
    sections = layout["sections"]

    assert [section["tab"] for section in sections] == ["计算", "计算", "乘区明细"]
    assert [section["columns"] for section in sections] == [2, 3, 3]
    assert sections[0]["variables"] == ["user_input.atk", "user_input.mult"]
    assert sections[1]["outputs"] == ["final"]
    assert sections[2]["outputs"] == ["zone_a", "zone_b"]
    assert len({section["id"] for section in sections}) == 3


def test_layout_sections_accepts_full_variable_path(scope: ProjectScope, tmp_path: Path) -> None:
    """variables 既可写裸变量名，也可写 user_input.<name>。"""
    generate_adapter(
        scope,
        adapter_id="demo",
        variables=_variables(),
        formula_steps=_steps(),
        outputs=_outputs(),
        layout_sections=[
            {"type": "inputs", "title": "输入", "variables": ["user_input.atk", "mult"]},
            {"type": "outputs", "title": "结果", "outputs": ["final"]},
        ],
    )

    layout = json.loads(
        (tmp_path / "framework" / "adapters" / "demo" / "ui" / "layout.json").read_text(encoding="utf-8")
    )
    assert layout["sections"][0]["variables"] == ["user_input.atk", "user_input.mult"]


def test_layout_sections_groups_unbound_sources_by_original_source(scope: ProjectScope, tmp_path: Path) -> None:
    """source 简写按原始 source 收集未绑定实体变量，并自动改写为 user_input 路径。"""
    generate_adapter(
        scope,
        adapter_id="demo",
        variables=[
            {"name": "atk", "type": "float", "source": "user_input", "default": 100},
            {"name": "def", "type": "float", "source": "enemy", "default": 10},
            {"name": "wdmg", "type": "float", "source": "weapon", "default": 5},
        ],
        formula_steps=[
            {"id": "final", "op": "+", "lhs": "atk", "rhs": "wdmg"},
            {"id": "extra", "op": "+", "lhs": "def", "rhs": "1"},
        ],
        outputs=[{"name": "final", "node": "final"}, {"name": "extra", "node": "extra"}],
        layout_sections=[
            {"type": "inputs", "title": "目标参数", "source": "enemy"},
            {"type": "inputs", "title": "武器参数", "source": "weapon"},
            {"type": "outputs", "title": "结果", "outputs": ["final", "extra"]},
        ],
    )

    layout = json.loads(
        (tmp_path / "framework" / "adapters" / "demo" / "ui" / "layout.json").read_text(encoding="utf-8")
    )
    assert layout["sections"][0]["variables"] == ["user_input.def"]
    assert layout["sections"][1]["variables"] == ["user_input.wdmg"]


def test_layout_sections_rejects_bound_entity_as_input(scope: ProjectScope) -> None:
    """已绑定实体变量由查看器实体下拉提供，不能放进 inputs 段。"""
    with pytest.raises(BuildError, match="不可作为输入"):
        generate_adapter(
            scope,
            adapter_id="demo",
            variables=[
                {"name": "atk", "type": "float", "source": "weapon", "default": 100},
            ],
            formula_steps=[{"id": "final", "op": "*", "lhs": "atk", "rhs": "2"}],
            outputs=[{"name": "final", "node": "final"}],
            data_files={"weapon": [{"名称": "测试武器", "atk": 100}]},
            layout_sections=[
                {"type": "inputs", "title": "武器参数", "variables": ["atk"]},
                {"type": "outputs", "title": "结果", "outputs": ["final"]},
            ],
        )


def test_layout_sections_rejects_unknown_variable(scope: ProjectScope) -> None:
    with pytest.raises(BuildError, match="不可作为输入"):
        generate_adapter(
            scope,
            adapter_id="demo",
            variables=_variables(),
            formula_steps=_steps(),
            outputs=_outputs(),
            layout_sections=[
                {"type": "inputs", "title": "输入", "variables": ["missing"]},
                {"type": "outputs", "title": "结果", "outputs": ["final"]},
            ],
        )


def test_layout_sections_rejects_duplicate_variable_across_sections(scope: ProjectScope) -> None:
    with pytest.raises(BuildError, match="重复"):
        generate_adapter(
            scope,
            adapter_id="demo",
            variables=_variables(),
            formula_steps=_steps(),
            outputs=_outputs(),
            layout_sections=[
                {"type": "inputs", "title": "输入 A", "variables": ["atk"]},
                {"type": "inputs", "title": "输入 B", "variables": ["atk"]},
                {"type": "outputs", "title": "结果", "outputs": ["final"]},
            ],
        )


def test_layout_sections_rejects_unknown_output(scope: ProjectScope) -> None:
    with pytest.raises(BuildError, match="未知输出"):
        generate_adapter(
            scope,
            adapter_id="demo",
            variables=_variables(),
            formula_steps=_steps(),
            outputs=_outputs(),
            layout_sections=[
                {"type": "inputs", "title": "输入", "source": "user_input"},
                {"type": "outputs", "title": "结果", "outputs": ["missing"]},
            ],
        )


def test_layout_sections_rejects_duplicate_output_across_sections(scope: ProjectScope) -> None:
    with pytest.raises(BuildError, match="重复"):
        generate_adapter(
            scope,
            adapter_id="demo",
            variables=_variables(),
            formula_steps=_steps(),
            outputs=_outputs(),
            layout_sections=[
                {"type": "inputs", "title": "输入", "source": "user_input"},
                {"type": "outputs", "title": "结果 A", "outputs": ["final"]},
                {"type": "outputs", "title": "结果 B", "outputs": ["final"]},
            ],
        )


def test_normalize_rejects_mixed_tabs() -> None:
    """tab 必须所有 section 都写或都不写。"""
    with pytest.raises(LayoutSectionsError, match="tab"):
        normalize_layout_sections(
            [
                {"type": "inputs", "title": "输入", "variables": ["atk"], "tab": "计算"},
                {"type": "outputs", "title": "结果", "outputs": ["final"]},
            ]
        )


@pytest.mark.parametrize(
    ("sections", "match"),
    [
        ([], "非空"),
        ([{"type": "widget", "title": "捐赠"}], "type"),
        ([{"type": ["inputs"], "title": "输入"}], "type"),
        ([{"type": "inputs", "title": ""}], "title"),
        ([{"type": "inputs", "title": "输入", "variables": ["atk"], "columns": 4}], "columns"),
        ([{"type": "inputs", "title": "输入"}], "variables 或 source"),
        ([{"type": "inputs", "title": "输入", "variables": ["atk"], "source": "user_input"}], "二选一"),
        ([{"type": "inputs", "title": "输入", "source": "unknown"}], "source"),
        ([{"type": "outputs", "title": "结果"}], "outputs"),
        ([{"type": "outputs", "title": "结果", "outputs": []}], "outputs"),
        ([{"type": "inputs", "title": "输入", "variables": ["atk", "atk"]}], "重复"),
    ],
)
def test_normalize_rejects_invalid_sections(sections: list[dict], match: str) -> None:
    with pytest.raises(LayoutSectionsError, match=match):
        normalize_layout_sections(sections)


def test_normalize_warns_unknown_fields() -> None:
    normalized, warnings = normalize_layout_sections(
        [{"type": "inputs", "title": "输入", "variables": ["atk"], "unexpected": 1}]
    )
    assert normalized[0]["variables"] == ["atk"]
    assert any("unexpected" in warning for warning in warnings)


def test_spec_wraps_invalid_layout_sections() -> None:
    from tools.calc_mcp.spec import normalize_spec

    with pytest.raises(SpecError, match="layout_sections"):
        normalize_spec(
            variables=[{"name": "atk", "source": "user_input"}],
            formula_steps=[{"id": "final", "op": "*", "lhs": "atk", "rhs": "2"}],
            layout_sections=[{"type": "inputs", "title": "输入", "variables": ["atk"], "columns": 9}],
        )
