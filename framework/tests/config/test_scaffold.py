# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""适配器脚手架 — 单元测试。"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from calc_framework.config.scaffold import (
    AdapterScaffoldConfig,
    ScaffoldResult,
    scaffold_adapter_directory,
)


def _write_dag(path: Path) -> Path:
    path.write_text(
        json.dumps(
            {
                "schema_version": "dag-v1",
                "name": "Demo",
                "variables": {
                    "user_input.atk": {"type": "float", "source": "user_input", "default": 100, "description": "攻击"},
                    "enemy.def": {"type": "float", "source": "enemy", "default": 10, "description": "防御"},
                    "computed.bonus": {"type": "float", "source": "computed", "default": 5, "description": "加成"},
                },
                "nodes": {
                    "atk": {"type": "var", "path": "user_input.atk"},
                    "def": {"type": "var", "path": "enemy.def"},
                    "damage": {"type": "binary", "op": "-", "lhs": "atk", "rhs": "def"},
                },
                "outputs": {"damage": {"node": "damage", "label": "伤害"}},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return path


def test_scaffold_creates_adapter_package(tmp_path: Path) -> None:
    dag_file = _write_dag(tmp_path / "demo.dag.json")

    result = scaffold_adapter_directory(
        AdapterScaffoldConfig(
            name="Demo Calculator",
            adapter_id="demo",
            game="Demo Game",
            description="测试适配器",
            dag_file=dag_file,
            output_root=tmp_path / "adapters",
        )
    )

    assert isinstance(result, ScaffoldResult)
    assert result.success is True
    assert result.adapter_dir == tmp_path / "adapters" / "demo"
    assert set(result.files) == {
        "demo/demo.dag.json",
        "demo/meta.json",
        "demo/attr_schema.json",
        "demo/ui/layout.json",
        "demo/functions.py",
    }

    meta = json.loads((result.adapter_dir / "meta.json").read_text(encoding="utf-8"))
    assert meta["name"] == "Demo Calculator"
    assert meta["game"] == "Demo Game"
    assert meta["entry_dag"] == "demo.dag.json"

    layout = json.loads((result.adapter_dir / "ui" / "layout.json").read_text(encoding="utf-8"))
    assert layout["schema_version"] == "ui-v1"
    assert layout["sections"][0]["variables"] == ["user_input.atk", "enemy.def"]

    data_dir = result.adapter_dir / "data"
    assert (data_dir / "enemies.json").exists()
    assert not (data_dir / "enemys.json").exists()
    assert not (data_dir / "computeds.json").exists()


def test_scaffold_rejects_invalid_adapter_id(tmp_path: Path) -> None:
    dag_file = _write_dag(tmp_path / "demo.dag.json")

    result = scaffold_adapter_directory(
        AdapterScaffoldConfig(
            name="Demo",
            adapter_id="../escape",
            dag_file=dag_file,
            output_root=tmp_path / "adapters",
        )
    )

    assert result.success is False
    assert "adapter_id" in result.error


def test_scaffold_missing_dag_returns_error(tmp_path: Path) -> None:
    result = scaffold_adapter_directory(
        AdapterScaffoldConfig(name="Demo", adapter_id="demo", dag_file=tmp_path / "missing.json", output_root=tmp_path)
    )

    assert result.success is False
    assert result.error


def test_dev_toolkit_shim_reexports_same_objects() -> None:
    from calc_framework.dev_toolkit.adapter_creator import (
        AdapterScaffoldConfig as ShimConfig,
    )
    from calc_framework.dev_toolkit.adapter_creator import (
        scaffold_adapter_directory as shim_scaffold,
    )

    assert ShimConfig is AdapterScaffoldConfig
    assert shim_scaffold is scaffold_adapter_directory


def test_config_scaffold_import_does_not_load_pyside6() -> None:
    code = (
        "import sys; import calc_framework.config.scaffold; "
        "assert 'PySide6' not in sys.modules, sorted(m for m in sys.modules if m.startswith('PySide6'))"
    )
    env = dict(os.environ)
    env.setdefault("PYTHONPATH", str(Path(__file__).resolve().parents[3] / "src"))
    subprocess.run([sys.executable, "-c", code], check=True, env=env, capture_output=True, text=True)
