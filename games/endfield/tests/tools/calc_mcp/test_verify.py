# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""MCP 校验与冒烟求值 — 单元测试。"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from tools.calc_mcp.build import scaffold_adapter
from tools.calc_mcp.safety import ProjectScope
from tools.calc_mcp.verify import VerifyError, smoke_test_adapter, validate_adapter


@pytest.fixture
def scope(tmp_path: Path) -> ProjectScope:
    (tmp_path / "framework" / "adapters").mkdir(parents=True)
    return ProjectScope(tmp_path)


def _dag() -> dict:
    return {
        "schema_version": "dag-v1",
        "name": "Verify Demo",
        "variables": {
            "user_input.atk": {"type": "float", "source": "user_input", "default": 10},
            "enemy.def": {"type": "float", "source": "enemy", "default": 2},
        },
        "nodes": {
            "atk": {"type": "var", "path": "user_input.atk"},
            "def": {"type": "var", "path": "enemy.def"},
            "damage": {"type": "binary", "op": "-", "lhs": "atk", "rhs": "def"},
        },
        "outputs": {"damage": {"node": "damage", "label": "伤害"}},
    }


@pytest.fixture
def adapter(scope: ProjectScope) -> str:
    scaffold_adapter(
        scope,
        adapter_id="demo",
        display_name="演示",
        game="演示游戏",
        dag=_dag(),
    )
    return "demo"


def test_validate_adapter_reports_stats(scope: ProjectScope, adapter: str) -> None:
    result = validate_adapter(scope, adapter)

    assert result["ok"] is True
    assert result["valid"] is True
    assert result["errors"] == []
    assert result["stats"]["variables"] == 2
    assert result["stats"]["nodes"] == 3
    assert result["stats"]["outputs"] == 1


def test_validate_adapter_missing_meta(scope: ProjectScope, tmp_path: Path) -> None:
    (tmp_path / "framework" / "adapters" / "broken").mkdir()

    result = validate_adapter(scope, "broken")

    assert result["valid"] is False
    assert any(item["code"] == "META_MISSING" for item in result["errors"])


def test_validate_adapter_invalid_dag(scope: ProjectScope, tmp_path: Path) -> None:
    target = tmp_path / "framework" / "adapters" / "broken"
    target.mkdir()
    (target / "meta.json").write_text(
        json.dumps(
            {
                "name": "Broken",
                "schema_version": "dag-v1",
                "entry_dag": "broken.dag.json",
            }
        ),
        encoding="utf-8",
    )
    (target / "broken.dag.json").write_text(
        json.dumps({"schema_version": "dag-v1", "name": "Broken", "nodes": {"x": {"type": "unknown"}}}),
        encoding="utf-8",
    )

    result = validate_adapter(scope, "broken")

    assert result["valid"] is False
    assert any(item["code"] == "DAG_INVALID" for item in result["errors"])


def test_validate_adapter_reports_layout_errors(scope: ProjectScope, adapter: str, tmp_path: Path) -> None:
    layout_path = tmp_path / "framework" / "adapters" / adapter / "ui" / "layout.json"
    layout = json.loads(layout_path.read_text(encoding="utf-8"))
    layout["sections"][-1]["outputs"].append("missing_output")
    layout_path.write_text(json.dumps(layout, ensure_ascii=False), encoding="utf-8")

    result = validate_adapter(scope, adapter)

    assert result["valid"] is False
    assert any("missing_output" in item["message"] for item in result["errors"])


def test_validate_adapter_reports_data_file_missing_name(scope: ProjectScope, adapter: str, tmp_path: Path) -> None:
    data_path = tmp_path / "framework" / "adapters" / adapter / "data" / "enemies.json"
    data_path.write_text(json.dumps([{"def": 10}], ensure_ascii=False), encoding="utf-8")

    result = validate_adapter(scope, adapter)

    assert result["valid"] is False
    assert any(item["code"] == "DATA_INVALID" and "名称" in item["message"] for item in result["errors"])


def test_validate_adapter_reports_duplicate_entity_names(scope: ProjectScope, adapter: str, tmp_path: Path) -> None:
    data_path = tmp_path / "framework" / "adapters" / adapter / "data" / "enemies.json"
    data_path.write_text(json.dumps([{"名称": "Boss"}, {"名称": "Boss"}], ensure_ascii=False), encoding="utf-8")

    result = validate_adapter(scope, adapter)

    assert result["valid"] is False
    assert any(item["code"] == "DATA_INVALID" and "重复" in item["message"] for item in result["errors"])


def test_validate_adapter_warns_empty_data_file(scope: ProjectScope, adapter: str) -> None:
    result = validate_adapter(scope, adapter)

    assert result["valid"] is True
    assert any(item["code"] == "DATA_EMPTY" for item in result["warnings"])


def test_validate_adapter_ignores_unrecognized_data_file_records(
    scope: ProjectScope, adapter: str, tmp_path: Path
) -> None:
    data_path = tmp_path / "framework" / "adapters" / adapter / "data" / "operators_standard.json"
    data_path.write_text(json.dumps([{"名称": "同名"}, {"名称": "同名"}], ensure_ascii=False), encoding="utf-8")

    result = validate_adapter(scope, adapter)

    assert result["valid"] is True
    assert any(item["code"] == "DATA_UNKNOWN" for item in result["warnings"])


def test_validate_adapter_reports_missing_entry_data(scope: ProjectScope, adapter: str, tmp_path: Path) -> None:
    meta_path = tmp_path / "framework" / "adapters" / adapter / "meta.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    meta["entry_data"] = ["data/missing.json"]
    meta_path.write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")

    result = validate_adapter(scope, adapter)

    assert result["valid"] is False
    assert any(item["code"] == "FILE_MISSING" and "missing.json" in item["message"] for item in result["errors"])


def _write_selector_data(tmp_path: Path, adapter: str) -> None:
    data_dir = tmp_path / "framework" / "adapters" / adapter / "data"
    data_dir.mkdir(exist_ok=True)
    (data_dir / "enemies.json").write_text(
        json.dumps([{"名称": "Boss", "种类": "精英", "def": 2}], ensure_ascii=False),
        encoding="utf-8",
    )


def _write_selector_meta(tmp_path: Path, adapter: str, selector: dict) -> None:
    meta_path = tmp_path / "framework" / "adapters" / adapter / "meta.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    meta["entity_selectors"] = [selector]
    meta_path.write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")


def test_validate_adapter_accepts_entity_selectors(scope: ProjectScope, adapter: str, tmp_path: Path) -> None:
    _write_selector_data(tmp_path, adapter)
    _write_selector_meta(
        tmp_path,
        adapter,
        {"source": "enemy", "steps": [{"field": "种类"}, {"field": "名称"}]},
    )

    result = validate_adapter(scope, adapter)

    assert result["valid"] is True, result["errors"]


def test_validate_adapter_reports_invalid_entity_selectors(scope: ProjectScope, adapter: str, tmp_path: Path) -> None:
    _write_selector_data(tmp_path, adapter)
    _write_selector_meta(
        tmp_path,
        adapter,
        {"source": "enemy", "steps": [{"field": "不存在"}, {"field": "名称"}]},
    )

    result = validate_adapter(scope, adapter)

    assert result["valid"] is False
    assert any(item["code"] == "SELECTOR_INVALID" for item in result["errors"])


def _write_entity_meta(tmp_path: Path, adapter: str, **entries: object) -> None:
    meta_path = tmp_path / "framework" / "adapters" / adapter / "meta.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    meta.update(entries)
    meta_path.write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")


def test_validate_adapter_accepts_entity_detail_and_input_rules(
    scope: ProjectScope, adapter: str, tmp_path: Path
) -> None:
    _write_selector_data(tmp_path, adapter)
    _write_entity_meta(
        tmp_path,
        adapter,
        entity_detail={
            "source": "enemy",
            "sections": [{"fields": [{"field": "def", "label": "防御"}]}],
        },
        entity_input_rules=[
            {
                "source": "enemy",
                "field": "def",
                "equals": 2,
                "disable": ["user_input.atk"],
            }
        ],
    )

    result = validate_adapter(scope, adapter)

    assert result["valid"] is True, result["errors"]


def test_validate_adapter_reports_invalid_entity_detail(scope: ProjectScope, adapter: str, tmp_path: Path) -> None:
    _write_selector_data(tmp_path, adapter)
    _write_entity_meta(
        tmp_path,
        adapter,
        entity_detail={"source": "enemy", "sections": [{"fields": [{"field": "不存在"}]}]},
    )

    result = validate_adapter(scope, adapter)

    assert result["valid"] is False
    assert any(item["code"] == "ENTITY_DETAIL_INVALID" for item in result["errors"])


def test_validate_adapter_reports_invalid_entity_input_rules(scope: ProjectScope, adapter: str, tmp_path: Path) -> None:
    _write_selector_data(tmp_path, adapter)
    _write_entity_meta(
        tmp_path,
        adapter,
        entity_input_rules=[{"source": "enemy", "field": "def", "equals": 2, "disable": ["user_input.missing"]}],
    )

    result = validate_adapter(scope, adapter)

    assert result["valid"] is False
    assert any(item["code"] == "INPUT_RULE_INVALID" for item in result["errors"])


def test_smoke_test_uses_defaults(scope: ProjectScope, adapter: str) -> None:
    result = smoke_test_adapter(scope, adapter)

    assert result["ok"] is True
    assert result["outputs"]["damage"] == pytest.approx(8.0)
    assert result["executed_nodes"] == 3


def test_smoke_test_applies_context_override(scope: ProjectScope, adapter: str) -> None:
    result = smoke_test_adapter(scope, adapter, context={"user_input": {"atk": 20}})

    assert result["outputs"]["damage"] == pytest.approx(18.0)


def test_smoke_test_include_node_values(scope: ProjectScope, adapter: str) -> None:
    result = smoke_test_adapter(scope, adapter, include_node_values=True)

    assert "damage" in result["node_values"]


def test_smoke_test_missing_adapter(scope: ProjectScope) -> None:
    with pytest.raises(VerifyError):
        smoke_test_adapter(scope, "missing")
