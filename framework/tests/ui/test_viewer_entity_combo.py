# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""CalcPackViewer 实体下拉 — 宽度回归测试。

回归：QComboBox 默认按最长条目计算 sizeHint。571 条「舰船 · 武器」名称会
把左侧「选择实体」面板撑到 800px 以上，挤压中间计算区并截断输入控件。
"""

from __future__ import annotations

import json
import sys
import zipfile
from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication

from calc_framework.ui.viewer import CalcPackViewer

_MAX_COMBO_WIDTH = 300
_RECORD_COUNT = 300


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


def _write_pack(path: Path) -> Path:
    meta = {
        "name": "下拉宽度测试",
        "game": "测试",
        "version": "0.0.1",
        "schema_version": "dag-v1",
        "entry_dag": "dag/formula.dag.json",
        "entry_data": ["data/weapons.json"],
    }
    dag = {
        "schema_version": "dag-v1",
        "name": "测试",
        "variables": {
            "user_input.atk": {
                "type": "float",
                "source": "user_input",
                "description": "攻击力",
                "default": 1,
            }
        },
        "nodes": {"atk": {"type": "var", "path": "user_input.atk"}},
        "outputs": {"攻击力": {"node": "atk", "label": "攻击力"}},
    }
    layout = {
        "schema_version": "ui-v1",
        "name": "测试",
        "sections": [
            {"id": "inputs", "type": "inputs", "title": "输入", "variables": ["user_input.atk"]},
            {"id": "outputs", "type": "outputs", "title": "输出", "outputs": ["攻击力"]},
        ],
    }
    records = [{"名称": f"舰船{i}·超长武器名称用于验证下拉不会撑宽面板", "攻击": i} for i in range(_RECORD_COUNT)]

    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("meta.json", json.dumps(meta, ensure_ascii=False))
        zf.writestr("dag/formula.dag.json", json.dumps(dag, ensure_ascii=False))
        zf.writestr("ui/layout.json", json.dumps(layout, ensure_ascii=False))
        zf.writestr("data/weapons.json", json.dumps(records, ensure_ascii=False))
    return path


def test_entity_combo_does_not_stretch_left_panel(qapp, tmp_path: Path) -> None:
    pack = _write_pack(tmp_path / "wide.calcpack")
    viewer = CalcPackViewer()
    viewer.load_calcpack(pack)

    combo = viewer._entity_selectors["weapon"]  # noqa: SLF001

    assert combo.count() == _RECORD_COUNT
    assert combo.maximumWidth() <= _MAX_COMBO_WIDTH
    assert combo.sizeHint().width() <= _MAX_COMBO_WIDTH
