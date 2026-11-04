# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""GeneratorEngine — 生成结果可加载性测试。"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from calc_framework.config.adapter import AdapterPackage
from tools.generator.engine import GeneratorEngine


def _write_files(root: Path, files: dict[str, str]) -> Path:
    for rel, content in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    return root


def test_generate_without_template_produces_loadable_adapter(tmp_path: Path) -> None:
    engine = GeneratorEngine(adapters_dir=tmp_path / "templates")
    files = engine.generate(
        None,
        "Demo",
        variables=[
            {"name": "atk", "type": "float", "source": "user_input", "default": 100, "description": "攻击"},
            {"name": "def", "type": "float", "source": "enemy", "default": 10, "description": "防御"},
        ],
        formula_steps=[{"id": "damage", "op": "-", "lhs": "atk", "rhs": "def", "label": "伤害"}],
        outputs=[{"name": "damage", "node": "damage", "label": "伤害"}],
    )

    assert files
    meta = json.loads(files["meta.json"])
    assert meta["entry_dag"] == "dag/demo.dag.json"
    assert "dag/demo.dag.json" in files

    adapter_dir = _write_files(tmp_path / "adapters" / "demo", files)
    pkg = AdapterPackage(adapter_dir)
    result = pkg.dag_service.evaluate({"user_input": {"atk": 100}})
    assert result.outputs["damage"] == pytest.approx(90.0)


def test_unbound_enemy_becomes_user_input(tmp_path: Path) -> None:
    engine = GeneratorEngine(adapters_dir=tmp_path)
    files = engine.generate(
        None,
        "Demo",
        variables=[{"name": "def", "type": "float", "source": "enemy", "default": 10, "description": "防御"}],
        formula_steps=[{"id": "double", "op": "*", "lhs": "def", "rhs": "2"}],
        outputs=[{"name": "double", "node": "double"}],
    )

    dag = json.loads(files["dag/demo.dag.json"])
    assert "user_input.def" in dag["variables"]
    assert "enemy.def" not in dag["variables"]
    assert dag["variables"]["user_input.def"]["source"] == "user_input"
    assert dag["nodes"]["def"]["path"] == "user_input.def"

    schema = json.loads(files["attr_schema.json"])
    assert schema["attributes"][0]["source"] == "user_input"


def test_layout_groups_by_original_source(tmp_path: Path) -> None:
    engine = GeneratorEngine(adapters_dir=tmp_path)
    files = engine.generate(
        None,
        "Demo",
        variables=[
            {"name": "atk", "source": "user_input", "default": 100},
            {"name": "char_atk", "source": "character", "default": 50},
            {"name": "wp_atk", "source": "weapon", "default": 30},
            {"name": "equip_atk", "source": "equipment", "default": 20},
            {"name": "def", "source": "enemy", "default": 10},
        ],
        formula_steps=[{"id": "out", "op": "*", "lhs": "atk", "rhs": "2"}],
        outputs=[{"name": "out", "node": "out"}],
    )

    sections = json.loads(files["ui/layout.json"])["sections"]
    input_sections = [s for s in sections if s["type"] == "inputs"]

    assert [s["title"] for s in input_sections] == ["输入参数", "角色参数", "武器参数", "装备参数", "目标参数"]
    assert [s["id"] for s in input_sections] == [
        "inputs",
        "inputs_character",
        "inputs_weapon",
        "inputs_equipment",
        "inputs_enemy",
    ]
    assert len({s["id"] for s in input_sections}) == len(input_sections)
    paths = [path for s in input_sections for path in s["variables"]]
    assert paths == [
        "user_input.atk",
        "user_input.char_atk",
        "user_input.wp_atk",
        "user_input.equip_atk",
        "user_input.def",
    ]


def test_computed_source_not_resourced(tmp_path: Path) -> None:
    engine = GeneratorEngine(adapters_dir=tmp_path)
    files = engine.generate(
        None,
        "Demo",
        variables=[
            {"name": "atk", "source": "user_input", "default": 100},
            {"name": "bonus", "source": "computed", "default": 5},
        ],
        formula_steps=[{"id": "out", "op": "+", "lhs": "atk", "rhs": "bonus"}],
        outputs=[{"name": "out", "node": "out"}],
    )

    dag = json.loads(files["dag/demo.dag.json"])
    assert "computed.bonus" in dag["variables"]
    assert "user_input.bonus" not in dag["variables"]

    input_sections = [s for s in json.loads(files["ui/layout.json"])["sections"] if s["type"] == "inputs"]
    paths = [path for s in input_sections for path in s["variables"]]
    assert paths == ["user_input.atk"]

    schema = json.loads(files["attr_schema.json"])
    sources = {attr["name"]: attr["source"] for attr in schema["attributes"]}
    assert sources["bonus"] == "computed"


def test_input_alias_normalized(tmp_path: Path) -> None:
    engine = GeneratorEngine(adapters_dir=tmp_path)
    files = engine.generate(
        None,
        "Demo",
        variables=[{"name": "x", "source": "input", "default": 1}],
        formula_steps=[{"id": "out", "op": "*", "lhs": "x", "rhs": "2"}],
        outputs=[{"name": "out", "node": "out"}],
    )

    dag = json.loads(files["dag/demo.dag.json"])
    assert "user_input.x" in dag["variables"]
    assert dag["variables"]["user_input.x"]["source"] == "user_input"
    assert "input.x" not in dag["variables"]


def test_bound_source_keeps_namespace_and_excluded_from_layout(tmp_path: Path) -> None:
    engine = GeneratorEngine(adapters_dir=tmp_path)
    files = engine.generate(
        None,
        "Demo",
        variables=[
            {"name": "atk", "source": "weapon", "default": 1},
            {"name": "mult", "source": "user_input", "default": 1},
        ],
        formula_steps=[
            {
                "id": "out",
                "op": "expr",
                "expr": "atk * mult",
                "input_map": {"atk": "atk", "mult": "mult"},
            }
        ],
        outputs=[{"name": "out", "node": "out"}],
        data_files={"weapon": [{"名称": "剑", "atk": 65}]},
    )

    dag = json.loads(files["dag/demo.dag.json"])
    assert "weapon.atk" in dag["variables"]
    assert dag["variables"]["weapon.atk"]["source"] == "weapon"

    input_sections = [s for s in json.loads(files["ui/layout.json"])["sections"] if s["type"] == "inputs"]
    assert [path for s in input_sections for path in s["variables"]] == ["user_input.mult"]

    assert json.loads(files["data/weapons.json"]) == [{"名称": "剑", "atk": 65}]

    adapter_dir = _write_files(tmp_path / "adapters" / "demo", files)
    pkg = AdapterPackage(adapter_dir)
    result = pkg.dag_service.evaluate({"weapon": {"atk": 65}, "user_input": {"mult": 2}})
    assert result.outputs["out"] == pytest.approx(130.0)


def test_data_files_written_with_conventional_names_and_entry_data(tmp_path: Path) -> None:
    engine = GeneratorEngine(adapters_dir=tmp_path)
    files = engine.generate(
        None,
        "Demo",
        variables=[{"name": "atk", "source": "user_input", "default": 1}],
        formula_steps=[{"id": "out", "op": "*", "lhs": "atk", "rhs": "2"}],
        outputs=[{"name": "out", "node": "out"}],
        data_files={
            "enemy": [{"名称": "Boss", "def": 10}],
            "character": [{"名称": "英雄", "base": 100}],
        },
    )

    assert json.loads(files["data/characters.json"]) == [{"名称": "英雄", "base": 100}]
    assert json.loads(files["data/enemies.json"]) == [{"名称": "Boss", "def": 10}]
    meta = json.loads(files["meta.json"])
    assert meta["entry_data"] == ["data/characters.json", "data/enemies.json"]


def test_no_data_files_omits_entry_data(tmp_path: Path) -> None:
    engine = GeneratorEngine(adapters_dir=tmp_path)
    files = engine.generate(
        None,
        "Demo",
        variables=[{"name": "x", "source": "user_input", "default": 1}],
        formula_steps=[{"id": "out", "op": "*", "lhs": "x", "rhs": "2"}],
        outputs=[{"name": "out", "node": "out"}],
    )

    assert "entry_data" not in json.loads(files["meta.json"])


def test_empty_data_file_written_as_empty_list(tmp_path: Path) -> None:
    engine = GeneratorEngine(adapters_dir=tmp_path)
    files = engine.generate(
        None,
        "Demo",
        variables=[{"name": "x", "source": "user_input", "default": 1}],
        formula_steps=[{"id": "out", "op": "*", "lhs": "x", "rhs": "2"}],
        outputs=[{"name": "out", "node": "out"}],
        data_files={"enemy": []},
    )

    assert json.loads(files["data/enemies.json"]) == []
    assert "entry_data" not in json.loads(files["meta.json"])


def test_empty_data_file_treated_as_unbound(tmp_path: Path) -> None:
    engine = GeneratorEngine(adapters_dir=tmp_path)
    files = engine.generate(
        None,
        "Demo",
        variables=[
            {"name": "def", "type": "float", "source": "enemy", "default": 10, "description": "防御"},
            {"name": "mult", "source": "user_input", "default": 2},
        ],
        formula_steps=[{"id": "out", "op": "*", "lhs": "def", "rhs": "mult"}],
        outputs=[{"name": "out", "node": "out"}],
        data_files={"enemy": []},
    )

    dag = json.loads(files["dag/demo.dag.json"])
    assert "user_input.def" in dag["variables"]
    assert "enemy.def" not in dag["variables"]

    input_sections = [s for s in json.loads(files["ui/layout.json"])["sections"] if s["type"] == "inputs"]
    assert [p for s in input_sections for p in s["variables"]] == ["user_input.mult", "user_input.def"]

    assert json.loads(files["data/enemies.json"]) == []
    assert "entry_data" not in json.loads(files["meta.json"])

    adapter_dir = _write_files(tmp_path / "adapters" / "demo", files)
    pkg = AdapterPackage(adapter_dir)
    result = pkg.dag_service.evaluate({"user_input": {"def": 10, "mult": 2}})
    assert result.outputs["out"] == pytest.approx(20.0)


def test_expr_comparison_ternary_end_to_end(tmp_path: Path) -> None:
    engine = GeneratorEngine(adapters_dir=tmp_path)
    files = engine.generate(
        None,
        "Demo",
        variables=[
            {"name": "atk", "source": "user_input", "default": 100},
            {"name": "def", "source": "enemy", "default": 50},
        ],
        formula_steps=[
            {
                "id": "out",
                "op": "expr",
                "expr": "atk * (1 if defense < 100 else 100 / (100 + defense))",
                "input_map": {"atk": "atk", "defense": "def"},
            }
        ],
        outputs=[{"name": "out", "node": "out"}],
    )

    adapter_dir = _write_files(tmp_path / "adapters" / "demo", files)
    pkg = AdapterPackage(adapter_dir)
    result = pkg.dag_service.evaluate({"user_input": {"atk": 100, "def": 200}})
    assert result.outputs["out"] == pytest.approx(100 * 100 / 300)


def test_generate_uses_injected_adapters_dir(tmp_path: Path) -> None:
    templates = tmp_path / "templates" / "tpl"
    templates.mkdir(parents=True)
    (templates / "meta.json").write_text(
        json.dumps(
            {
                "name": "模板",
                "description": "模板描述",
                "schema_version": "dag-v1",
                "functions": {"double": "functions.py"},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (templates / "functions.py").write_text("def double(x):\n    return x * 2\n", encoding="utf-8")

    engine = GeneratorEngine(adapters_dir=tmp_path / "templates")
    files = engine.generate(
        "tpl",
        "Demo",
        variables=[{"name": "atk", "default": 1}],
        formula_steps=[{"id": "out", "op": "*", "lhs": "atk", "rhs": "2"}],
        outputs=[{"name": "out", "node": "out"}],
    )

    meta = json.loads(files["meta.json"])
    assert meta["schema_version"] == "dag-v1"
    assert meta["functions"] == {"double": "functions.py"}
    assert "functions.py" in files


def test_generate_requires_steps(tmp_path: Path) -> None:
    engine = GeneratorEngine(adapters_dir=tmp_path)

    assert engine.generate(None, "Demo", variables=[], formula_steps=[], outputs=[]) == {}
