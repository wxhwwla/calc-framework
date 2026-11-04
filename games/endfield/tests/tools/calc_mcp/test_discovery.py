# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""MCP 发现类工具 — 单元测试。"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from tools.calc_mcp.discovery import (
    DiscoveryError,
    describe_schemas,
    list_adapters,
    list_templates,
    read_guide,
)
from tools.calc_mcp.safety import ProjectScope


@pytest.fixture
def scope(tmp_path: Path) -> ProjectScope:
    adapters = tmp_path / "framework" / "adapters"
    for adapter_id, name, description in (
        ("simple", "简单伤害计算", "攻击×倍率-防御"),
        ("card_rpg", "卡牌RPG", "卡牌伤害"),
    ):
        target = adapters / adapter_id
        target.mkdir(parents=True)
        (target / "meta.json").write_text(
            json.dumps(
                {
                    "name": name,
                    "game": name,
                    "description": description,
                    "version": "1.0.0",
                    "schema_version": "dag-v1",
                    "entry_dag": f"dag/{adapter_id}.dag.json",
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
    hidden = adapters / "_template"
    hidden.mkdir(parents=True)
    (hidden / "meta.json").write_text("{}", encoding="utf-8")

    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "制造游戏计算器完整流程.md").write_text("完整流程内容", encoding="utf-8")
    return ProjectScope(tmp_path)


def test_list_templates_skips_underscore(scope: ProjectScope) -> None:
    result = list_templates(scope)

    ids = [item["id"] for item in result["templates"]]
    assert ids == ["card_rpg", "simple"]
    assert result["templates"][0]["name"] == "卡牌RPG"
    assert result["templates"][0]["available"] is True


def test_list_adapters_reports_entry(scope: ProjectScope) -> None:
    result = list_adapters(scope)

    entry = next(item for item in result["adapters"] if item["id"] == "simple")
    assert entry["name"] == "简单伤害计算"
    assert entry["version"] == "1.0.0"
    assert entry["entry_dag"] == "dag/simple.dag.json"


def test_describe_schemas_exposes_node_and_step_rules() -> None:
    result = describe_schemas()

    assert set(result["variables"]["types"]) == {"float", "int", "bool", "str"}
    assert "user_input" in result["variables"]["sources"]
    node_types = {item["type"] for item in result["nodes"]}
    assert {"binary", "expr", "call", "var"} <= node_types
    assert {"+", "-", "*", "/"} <= set(result["formula_steps"]["ops"])
    assert "变量 name" in result["formula_steps"]["reference_rule"]
    function_names = {item["name"] for item in result["expression_functions"]}
    assert {"sqrt", "integral"} <= function_names


def test_describe_schemas_exposes_data_files_and_expression_operators() -> None:
    result = describe_schemas()

    data_files = result["data_files"]
    assert data_files["allowed_sources"] == ["character", "weapon", "equipment", "enemy"]
    assert data_files["files"]["enemy"] == "data/enemies.json"
    assert data_files["max_bytes_per_file"] == 512 * 1024
    assert "非空" in data_files["binding_rule"]
    assert "名称" in data_files["validation_rule"]

    operators = result["expression_operators"]
    assert set(operators["comparison"]) == {"<", "<=", ">", ">=", "==", "!="}
    assert set(operators["boolean"]) == {"and", "or", "not"}
    assert "三元" in operators["ternary"]

    assert result["layout"]["section_types"] == ["inputs", "outputs", "widget"]
    assert result["layout"]["widget_types"] == ["donation"]


def test_read_guide_returns_content(scope: ProjectScope) -> None:
    result = read_guide(scope, "overview")

    assert result["title"] == "完整制造流程"
    assert result["path"] == "docs/制造游戏计算器完整流程.md"
    assert result["content"] == "完整流程内容"
    assert result["truncated"] is False


def test_read_guide_rejects_unknown_topic(scope: ProjectScope) -> None:
    with pytest.raises(DiscoveryError, match="topic"):
        read_guide(scope, "secrets")
