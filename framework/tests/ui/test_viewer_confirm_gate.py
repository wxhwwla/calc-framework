# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""CalcPackViewer 共享外壳与确认门控 — 单元测试。"""

from __future__ import annotations

import json
import sys
import zipfile
from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication

from calc_framework.ui.viewer import CalcPackViewer

_RECORDS: list[dict[str, object]] = [
    {"名称": "A · 炮", "舰船分类": ["战机"], "舰船": "A", "武器标签": "炮", "攻击": 1.0},
    {"名称": "B · 炮", "舰船分类": ["护卫舰"], "舰船": "B", "武器标签": "炮", "攻击": 2.0},
]

_CASCADE = [
    {
        "source": "weapon",
        "data_file": "weapons",
        "steps": [
            {"field": "舰船分类", "label": "舰船种类"},
            {"field": "舰船", "label": "舰船"},
            {"field": "名称", "label": "武器", "display_field": "武器标签"},
        ],
    }
]

_DETAIL = {
    "source": "weapon",
    "title": "武器数据",
    "sections": [
        {"title": "基础", "columns": 2, "fields": [{"field": "攻击", "label": "攻击"}]},
    ],
}


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


def _write_pack(path: Path) -> Path:
    dag = {
        "schema_version": "dag-v1",
        "name": "确认门控测试",
        "variables": {
            "weapon.攻击": {"type": "float", "source": "weapon", "default": 0.0},
            "user_input.系数": {
                "type": "float",
                "source": "user_input",
                "description": "系数",
                "default": 1.0,
            },
        },
        "nodes": {
            "weapon_value": {"type": "var", "path": "weapon.攻击"},
            "input_value": {"type": "var", "path": "user_input.系数"},
        },
        "outputs": {
            "结果": {"node": "weapon_value", "label": "结果"},
            "系数结果": {"node": "input_value", "label": "系数结果"},
        },
    }
    layout = {
        "schema_version": "ui-v1",
        "name": "确认门控测试",
        "sections": [
            {
                "id": "inputs",
                "type": "inputs",
                "title": "参数",
                "variables": ["user_input.系数"],
                "tab": "计算",
            },
            {"id": "outputs", "type": "outputs", "title": "输出", "outputs": ["结果"], "tab": "计算"},
            {
                "id": "zones",
                "type": "outputs",
                "title": "乘区",
                "outputs": ["系数结果"],
                "tab": "乘区明细",
            },
        ],
    }
    meta = {
        "name": "确认门控测试",
        "game": "测试",
        "version": "0.0.1",
        "schema_version": "dag-v1",
        "entry_dag": "dag/formula.dag.json",
        "entry_data": ["data/weapons.json"],
        "entity_selectors": _CASCADE,
        "entity_detail": _DETAIL,
    }
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("meta.json", json.dumps(meta, ensure_ascii=False))
        zf.writestr("dag/formula.dag.json", json.dumps(dag, ensure_ascii=False))
        zf.writestr("ui/layout.json", json.dumps(layout, ensure_ascii=False))
        zf.writestr("data/weapons.json", json.dumps(_RECORDS, ensure_ascii=False))
    return path


def _viewer(tmp_path: Path) -> CalcPackViewer:
    viewer = CalcPackViewer()
    viewer.load_calcpack(_write_pack(tmp_path / "confirm.calcpack"))
    return viewer


def _output_text(viewer: CalcPackViewer, name: str) -> str:
    return viewer._compute_sheet._output_labels[name].text()  # noqa: SLF001


class TestShellLayout:
    def test_toolbar_replaces_menu_bar(self, qapp, tmp_path: Path) -> None:
        viewer = _viewer(tmp_path)

        assert viewer.menuBar().actions() == []
        texts = [action.text() for action in viewer._shell.toolbar.actions() if action.text()]  # noqa: SLF001
        assert "计算包信息" in texts
        assert "使用说明" in texts
        assert "自愿捐赠" in texts

    def test_layout_tabs_become_bottom_tabs(self, qapp, tmp_path: Path) -> None:
        viewer = _viewer(tmp_path)

        assert viewer._shell.tab_texts() == ["计算", "乘区明细"]  # noqa: SLF001
        assert viewer._shell.page_count == 2  # noqa: SLF001

    def test_inputs_and_detail_are_placed_in_page_zones(self, qapp, tmp_path: Path) -> None:
        viewer = _viewer(tmp_path)
        page = viewer._shell.page_stack.widget(0)  # noqa: SLF001

        input_widget = viewer._compute_sheet._input_widgets["user_input.系数"][0]  # noqa: SLF001
        assert page.zone("top_right").isAncestorOf(input_widget)
        assert page.zone("bottom_left").isAncestorOf(viewer._detail_container)  # noqa: SLF001


class TestConfirmGate:
    def test_entity_change_does_not_update_until_confirm(self, qapp, tmp_path: Path) -> None:
        viewer = _viewer(tmp_path)
        assert viewer._detail_value_labels["攻击"].text() == "1"  # noqa: SLF001
        assert _output_text(viewer, "结果") == "1.0000"

        combos = viewer._cascade_combos["weapon"]  # noqa: SLF001
        combos[0].setCurrentIndex(combos[0].findData("护卫舰"))

        assert viewer._detail_value_labels["攻击"].text() == "1"  # noqa: SLF001
        assert _output_text(viewer, "结果") == "1.0000"
        assert viewer._shell.status_text() == "有未确认的更改"  # noqa: SLF001

        viewer.confirm()

        assert viewer._detail_value_labels["攻击"].text() == "2"  # noqa: SLF001
        assert _output_text(viewer, "结果") == "2.0000"

    def test_input_change_does_not_update_until_confirm(self, qapp, tmp_path: Path) -> None:
        viewer = _viewer(tmp_path)
        assert _output_text(viewer, "系数结果") == "1.0000"

        spin = viewer._compute_sheet._input_widgets["user_input.系数"][0]  # noqa: SLF001
        spin.setValue(2.0)

        assert _output_text(viewer, "系数结果") == "1.0000"
        assert viewer._shell.status_text() == "有未确认的更改"  # noqa: SLF001

        viewer.confirm()

        assert _output_text(viewer, "系数结果") == "2.0000"

    def test_confirm_button_triggers_same_path(self, qapp, tmp_path: Path) -> None:
        viewer = _viewer(tmp_path)
        spin = viewer._compute_sheet._input_widgets["user_input.系数"][0]  # noqa: SLF001
        spin.setValue(3.0)

        viewer._shell.confirm_button.click()  # noqa: SLF001

        assert _output_text(viewer, "系数结果") == "3.0000"
        assert viewer._shell.status_text().startswith("已确认")  # noqa: SLF001
