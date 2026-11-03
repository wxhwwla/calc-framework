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
    result = pkg.dag_service.evaluate({"user_input": {"atk": 100}, "enemy": {"def": 10}})
    assert result.outputs["damage"] == pytest.approx(90.0)


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
