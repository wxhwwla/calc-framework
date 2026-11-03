# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""MCP 生成与脚手架 — 单元测试。"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from calc_framework.config.adapter import AdapterPackage
from tools.calc_mcp.build import BuildError, generate_adapter, scaffold_adapter
from tools.calc_mcp.safety import ProjectScope


@pytest.fixture
def scope(tmp_path: Path) -> ProjectScope:
    (tmp_path / "framework" / "adapters").mkdir(parents=True)
    return ProjectScope(tmp_path)


def _variables() -> list[dict]:
    return [
        {"name": "atk", "type": "float", "source": "user_input", "default": 100},
        {"name": "def", "type": "float", "source": "enemy", "default": 10},
    ]


def _steps() -> list[dict]:
    return [{"id": "damage", "op": "-", "lhs": "atk", "rhs": "def"}]


def _outputs() -> list[dict]:
    return [{"name": "damage", "node": "damage", "label": "伤害"}]


def test_generate_adapter_writes_loadable_package(scope: ProjectScope, tmp_path: Path) -> None:
    result = generate_adapter(
        scope,
        adapter_id="demo",
        display_name="演示计算器",
        game="演示游戏",
        variables=_variables(),
        formula_steps=_steps(),
        outputs=_outputs(),
    )

    adapter_dir = tmp_path / "framework" / "adapters" / "demo"
    assert result["ok"] is True
    assert (adapter_dir / "meta.json").is_file()
    meta = json.loads((adapter_dir / "meta.json").read_text(encoding="utf-8"))
    assert meta["name"] == "演示计算器"
    assert meta["game"] == "演示游戏"

    pkg = AdapterPackage(adapter_dir)
    evaluated = pkg.dag_service.evaluate({"user_input": {"atk": 100}, "enemy": {"def": 10}})
    assert evaluated.outputs["damage"] == pytest.approx(90.0)


def test_generate_adapter_dry_run_does_not_write(scope: ProjectScope, tmp_path: Path) -> None:
    result = generate_adapter(
        scope,
        adapter_id="demo",
        variables=_variables(),
        formula_steps=_steps(),
        outputs=_outputs(),
        dry_run=True,
    )

    assert result["dry_run"] is True
    assert "meta.json" in result["files"]
    assert not (tmp_path / "framework" / "adapters" / "demo").exists()


def test_generate_adapter_refuses_existing_directory(scope: ProjectScope) -> None:
    generate_adapter(
        scope,
        adapter_id="demo",
        variables=_variables(),
        formula_steps=_steps(),
        outputs=_outputs(),
    )

    with pytest.raises(BuildError, match="已存在"):
        generate_adapter(
            scope,
            adapter_id="demo",
            variables=_variables(),
            formula_steps=_steps(),
            outputs=_outputs(),
        )


def test_generate_adapter_uses_template_functions(scope: ProjectScope, tmp_path: Path) -> None:
    template = tmp_path / "framework" / "adapters" / "tpl"
    template.mkdir()
    (template / "meta.json").write_text(
        json.dumps({"name": "模板", "schema_version": "dag-v1", "functions": {"double": "functions.py"}}),
        encoding="utf-8",
    )
    (template / "functions.py").write_text("def double(x):\n    return x * 2\n", encoding="utf-8")

    result = generate_adapter(
        scope,
        adapter_id="demo",
        template_id="tpl",
        variables=_variables(),
        formula_steps=_steps(),
        outputs=_outputs(),
    )

    assert "functions.py" in result["files"]
    meta = json.loads((tmp_path / "framework" / "adapters" / "demo" / "meta.json").read_text(encoding="utf-8"))
    assert meta["functions"] == {"double": "functions.py"}


def _raw_dag() -> dict:
    return {
        "schema_version": "dag-v1",
        "name": "Scaffold Demo",
        "variables": {
            "user_input.atk": {"type": "float", "source": "user_input", "default": 10},
            "enemy.def": {"type": "float", "source": "enemy", "default": 2},
        },
        "nodes": {
            "atk": {"type": "var", "path": "user_input.atk"},
            "def": {"type": "var", "path": "enemy.def"},
            "neg": {"type": "unary", "op": "neg", "input": "def"},
            "damage": {"type": "binary", "op": "+", "lhs": "atk", "rhs": "neg"},
        },
        "outputs": {"damage": {"node": "damage", "label": "伤害"}},
    }


def test_scaffold_adapter_supports_unary_nodes(scope: ProjectScope, tmp_path: Path) -> None:
    result = scaffold_adapter(
        scope,
        adapter_id="raw",
        display_name="原始 DAG",
        game="演示",
        description="脚手架测试",
        dag=_raw_dag(),
    )

    adapter_dir = tmp_path / "framework" / "adapters" / "raw"
    assert result["ok"] is True
    assert (adapter_dir / "raw.dag.json").is_file()

    pkg = AdapterPackage(adapter_dir)
    evaluated = pkg.dag_service.evaluate({"user_input": {"atk": 10}, "enemy": {"def": 2}})
    assert evaluated.outputs["damage"] == pytest.approx(8.0)


def test_scaffold_adapter_rejects_invalid_dag(scope: ProjectScope) -> None:
    dag = _raw_dag()
    dag["nodes"]["damage"]["lhs"] = "missing"

    with pytest.raises(BuildError, match="DAG"):
        scaffold_adapter(scope, adapter_id="raw", dag=dag)


def test_scaffold_adapter_refuses_overwrite(scope: ProjectScope) -> None:
    scaffold_adapter(scope, adapter_id="raw", dag=_raw_dag())

    with pytest.raises(BuildError, match="已存在"):
        scaffold_adapter(scope, adapter_id="raw", dag=_raw_dag())
