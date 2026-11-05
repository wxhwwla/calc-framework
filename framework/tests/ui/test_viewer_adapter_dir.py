# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""CalcPackViewer 直接加载适配器目录（无需先打包 .calcpack）。"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication

from calc_framework.ui.viewer import CalcPackViewer
from calc_framework.ui.viewer_pack_utils import (
    extract_assets_from_adapter_dir,
    load_adapter_dir,
)

_REPO_ROOT = Path(__file__).resolve().parents[3]
_WJDLGLR_DIR = _REPO_ROOT / "framework" / "adapters" / "wjdlglr"


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


def _write_adapter(
    root: Path,
    *,
    meta: dict[str, object],
    dag: dict[str, object] | None = None,
    layout: dict[str, object] | None = None,
) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    (root / "meta.json").write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")
    if dag is not None:
        dag_path = root / "dag" / "formula.dag.json"
        dag_path.parent.mkdir(parents=True, exist_ok=True)
        dag_path.write_text(json.dumps(dag, ensure_ascii=False), encoding="utf-8")
    if layout is not None:
        layout_path = root / "ui" / "layout.json"
        layout_path.parent.mkdir(parents=True, exist_ok=True)
        layout_path.write_text(json.dumps(layout, ensure_ascii=False), encoding="utf-8")
    return root


_MIN_DAG: dict[str, object] = {
    "schema_version": "dag-v1",
    "name": "测试",
    "variables": {
        "user_input.系数": {
            "type": "float",
            "source": "user_input",
            "description": "系数",
            "default": 1,
        }
    },
    "nodes": {"value": {"type": "var", "path": "user_input.系数"}},
    "outputs": {"结果": {"node": "value", "label": "结果"}},
}

_MIN_LAYOUT: dict[str, object] = {
    "schema_version": "ui-v1",
    "name": "测试",
    "sections": [
        {"id": "inputs", "type": "inputs", "title": "输入", "variables": ["user_input.系数"]},
        {"id": "outputs", "type": "outputs", "title": "输出", "outputs": ["结果"]},
    ],
}


class TestLoadAdapterDir:
    def test_maps_wjdlglr_directory_to_calcpack_shape(self) -> None:
        data = load_adapter_dir(_WJDLGLR_DIR)

        assert data["meta.json"]["name"] == "无尽的拉格朗日 武器输出计算器"
        assert data["dag/formula.dag.json"]["schema_version"] == "dag-v1"
        assert data["ui/layout.json"]["sections"]
        assert len(data["data/weapons.json"]) == 571

    def test_missing_meta_raises(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            load_adapter_dir(tmp_path / "empty")

    def test_missing_dag_raises(self, tmp_path: Path) -> None:
        root = _write_adapter(
            tmp_path / "adapter",
            meta={"name": "测试", "entry_dag": "dag/formula.dag.json", "entry_data": []},
        )

        with pytest.raises(FileNotFoundError):
            load_adapter_dir(root)

    def test_entry_dag_traversal_rejected(self, tmp_path: Path) -> None:
        outside = tmp_path / "evil.json"
        outside.write_text(json.dumps(_MIN_DAG), encoding="utf-8")
        root = _write_adapter(
            tmp_path / "adapter",
            meta={"name": "测试", "entry_dag": "../evil.json", "entry_data": []},
            layout=_MIN_LAYOUT,
        )

        with pytest.raises(ValueError):
            load_adapter_dir(root)

    def test_entry_data_traversal_rejected(self, tmp_path: Path) -> None:
        root = _write_adapter(
            tmp_path / "adapter",
            meta={"name": "测试", "entry_dag": "dag/formula.dag.json", "entry_data": ["../evil.json"]},
            dag=_MIN_DAG,
            layout=_MIN_LAYOUT,
        )
        (tmp_path / "evil.json").write_text("[]", encoding="utf-8")

        with pytest.raises(ValueError):
            load_adapter_dir(root)

    def test_entry_data_must_be_list(self, tmp_path: Path) -> None:
        root = _write_adapter(
            tmp_path / "adapter",
            meta={"name": "测试", "entry_dag": "dag/formula.dag.json", "entry_data": "data/x.json"},
            dag=_MIN_DAG,
            layout=_MIN_LAYOUT,
        )

        with pytest.raises(ValueError):
            load_adapter_dir(root)

    def test_loads_optional_attr_schema_and_theme(self, tmp_path: Path) -> None:
        root = _write_adapter(
            tmp_path / "adapter",
            meta={
                "name": "测试",
                "entry_dag": "dag/formula.dag.json",
                "ui_layout": "ui/layout.json",
                "attr_schema": "attr_schema.json",
            },
            dag=_MIN_DAG,
            layout=_MIN_LAYOUT,
        )
        (root / "attr_schema.json").write_text('{"attributes": []}', encoding="utf-8")
        (root / "ui").mkdir(exist_ok=True)
        (root / "ui" / "theme.json").write_text('{"name": "test"}', encoding="utf-8")

        data = load_adapter_dir(root)

        assert data["attr_schema.json"] == {"attributes": []}
        assert data["ui/theme.json"] == {"name": "test"}

    def test_extract_assets_returns_asset_map(self, tmp_path: Path) -> None:
        root = _write_adapter(
            tmp_path / "adapter",
            meta={"name": "测试", "entry_dag": "dag/formula.dag.json", "entry_data": []},
            dag=_MIN_DAG,
            layout=_MIN_LAYOUT,
        )
        (root / "assets").mkdir()
        (root / "assets" / "logo.txt").write_text("logo", encoding="utf-8")

        asset_map = extract_assets_from_adapter_dir(root, tmp_path / "extracted")

        assert asset_map == {"assets/logo.txt": str(tmp_path / "extracted" / "assets" / "logo.txt")}
        assert (tmp_path / "extracted" / "assets" / "logo.txt").read_text(encoding="utf-8") == "logo"


class TestViewerLoadAdapterDir:
    def test_loads_real_adapter_and_builds_cascade(self, qapp) -> None:
        assert QApplication.instance() is qapp
        viewer = CalcPackViewer()

        assert viewer.is_loaded is False
        assert viewer.load_adapter_dir(_WJDLGLR_DIR, show_errors=False) is True
        assert viewer.is_loaded is True
        assert viewer.windowTitle() == "无尽的拉格朗日 武器输出计算器"

        combos = viewer._cascade_combos["weapon"]  # noqa: SLF001
        assert len(combos) == 3
        assert combos[0].count() > 0
        assert viewer._level_spin is None  # noqa: SLF001
        assert viewer._detail_value_labels  # noqa: SLF001
        assert "base_damage" in viewer._detail_value_labels  # noqa: SLF001

        context = viewer._build_current_context()  # noqa: SLF001
        assert context["weapon"]["base_damage"] > 0
        assert "满命中每分钟伤害" in viewer._dag_service.dag.outputs  # noqa: SLF001

    def test_missing_adapter_returns_false_and_stays_unloaded(self, qapp, tmp_path: Path) -> None:
        assert QApplication.instance() is qapp
        viewer = CalcPackViewer()

        assert viewer.load_adapter_dir(tmp_path / "missing", show_errors=False) is False
        assert viewer.is_loaded is False
