# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""MCP .calcpack 导出/导入 — 单元测试。"""

from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pytest
from calc_framework.config.adapter import AdapterPackage
from tools.calc_mcp.build import scaffold_adapter
from tools.calc_mcp.package import PackageError, export_calcpack, import_calcpack
from tools.calc_mcp.safety import ProjectScope


@pytest.fixture
def scope(tmp_path: Path) -> ProjectScope:
    (tmp_path / "framework" / "adapters").mkdir(parents=True)
    (tmp_path / "dist").mkdir()
    return ProjectScope(tmp_path)


def _dag() -> dict:
    return {
        "schema_version": "dag-v1",
        "name": "Pack Demo",
        "variables": {
            "user_input.atk": {"type": "float", "source": "user_input", "default": 10},
        },
        "subgraphs": {
            "scale": {
                "parameters": {"x": {"type": "float"}},
                "nodes": {
                    "x": {"type": "var", "path": "x"},
                    "two": {"type": "const", "value": 2},
                    "double": {"type": "binary", "op": "*", "lhs": "x", "rhs": "two"},
                },
                "outputs": {"result": {"node": "double", "label": "倍率"}},
            }
        },
        "nodes": {
            "atk": {"type": "var", "path": "user_input.atk"},
            "scaled": {"type": "call", "subgraph": "scale", "bindings": {"x": "atk"}},
        },
        "outputs": {"damage": {"node": "scaled", "label": "伤害"}},
    }


@pytest.fixture
def adapter(scope: ProjectScope) -> str:
    scaffold_adapter(scope, adapter_id="demo", display_name="打包演示", game="演示游戏", dag=_dag())
    return "demo"


def _add_data(scope: ProjectScope, adapter: str) -> None:
    data_dir = scope.adapter_dir(adapter) / "data"
    data_dir.mkdir(exist_ok=True)
    (data_dir / "characters.json").write_text(
        json.dumps([{"名称": "测试角色", "基础攻击": 100}], ensure_ascii=False),
        encoding="utf-8",
    )


def test_export_writes_pack_with_attr_schema_and_subgraphs(scope: ProjectScope, adapter: str) -> None:
    _add_data(scope, adapter)

    result = export_calcpack(scope, adapter_id=adapter, output_path="dist/demo.calcpack")

    pack = scope.root / "dist" / "demo.calcpack"
    assert result["ok"] is True
    assert result["path"] == "dist/demo.calcpack"
    assert result["size_bytes"] == pack.stat().st_size

    with zipfile.ZipFile(pack) as zf:
        names = set(zf.namelist())
        meta = json.loads(zf.read("meta.json"))
        dag = json.loads(zf.read("dag/formula.dag.json"))

    assert {
        "meta.json",
        "dag/formula.dag.json",
        "ui/layout.json",
        "attr_schema.json",
        "dag/subgraphs/scale.dag.json",
        "data/characters.json",
    } <= names
    assert meta["entry_dag"] == "dag/formula.dag.json"
    assert meta["ui_layout"] == "ui/layout.json"
    assert "functions" not in meta
    assert "scale" in dag["subgraphs"]


def test_export_refuses_invalid_adapter(scope: ProjectScope, adapter: str) -> None:
    layout_path = scope.adapter_dir(adapter) / "ui" / "layout.json"
    layout = json.loads(layout_path.read_text(encoding="utf-8"))
    layout["sections"][-1]["outputs"].append("missing_output")
    layout_path.write_text(json.dumps(layout, ensure_ascii=False), encoding="utf-8")

    with pytest.raises(PackageError, match="校验"):
        export_calcpack(scope, adapter_id=adapter, output_path="dist/demo.calcpack")

    forced = export_calcpack(scope, adapter_id=adapter, output_path="dist/demo.calcpack", force=True)
    assert forced["ok"] is True
    assert forced["validation"]["valid"] is False


def test_export_rejects_output_outside_project(scope: ProjectScope, adapter: str) -> None:
    with pytest.raises(PackageError):
        export_calcpack(scope, adapter_id=adapter, output_path="../escape.calcpack")


def test_import_roundtrip(scope: ProjectScope, adapter: str) -> None:
    _add_data(scope, adapter)
    export_calcpack(scope, adapter_id=adapter, output_path="dist/demo.calcpack")

    result = import_calcpack(scope, calcpack_path="dist/demo.calcpack", adapter_id="demo_copy")

    assert result["ok"] is True
    assert result["adapter_id"] == "demo_copy"
    assert result["validation"]["valid"] is True
    assert (scope.adapter_dir("demo_copy") / "attr_schema.json").is_file()
    assert (scope.adapter_dir("demo_copy") / "data" / "characters.json").is_file()

    package = AdapterPackage(scope.adapter_dir("demo_copy"))
    evaluated = package.dag_service.evaluate({"user_input": {"atk": 10}})
    assert evaluated.outputs["damage"] == pytest.approx(20.0)


def test_import_refuses_existing_adapter(scope: ProjectScope, adapter: str) -> None:
    export_calcpack(scope, adapter_id=adapter, output_path="dist/demo.calcpack")

    with pytest.raises(PackageError, match="已存在"):
        import_calcpack(scope, calcpack_path="dist/demo.calcpack", adapter_id=adapter)


def test_import_rejects_missing_meta(scope: ProjectScope) -> None:
    pack = scope.root / "dist" / "empty.calcpack"
    with zipfile.ZipFile(pack, "w") as zf:
        zf.writestr("dag/formula.dag.json", "{}")

    with pytest.raises(PackageError, match="meta.json"):
        import_calcpack(scope, calcpack_path="dist/empty.calcpack", adapter_id="empty")


def test_import_rejects_zip_slip(scope: ProjectScope) -> None:
    pack = scope.root / "dist" / "evil.calcpack"
    with zipfile.ZipFile(pack, "w") as zf:
        zf.writestr("meta.json", json.dumps({"name": "Evil", "schema_version": "dag-v1"}))
        zf.writestr("../evil.txt", "pwned")

    with pytest.raises(PackageError, match="越界"):
        import_calcpack(scope, calcpack_path="dist/evil.calcpack", adapter_id="evil")

    assert not (scope.root / "evil.txt").exists()
    assert not scope.adapter_dir("evil").exists()
