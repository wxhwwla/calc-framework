# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""查看器实体详情面板与条件禁用输入测试。"""

from __future__ import annotations

import json
import sys
import zipfile
from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication

from calc_framework.ui.viewer import CalcPackViewer

_RECORDS: list[dict[str, object]] = [
    {
        "名称": "A · 实弹炮",
        "舰船分类": ["战机"],
        "舰船": "A",
        "武器标签": "实弹炮",
        "攻击": 1,
        "damage_type": "实弹",
        "is_energy": 0.0,
        "needs_mothership": 0.0,
        "crit_rate": 0.0,
        "crit_damage": 0.0,
        "crit_target": "",
        "hit_fighter": 22.0,
        "hit_frigate": 85.0,
    },
    {
        "名称": "B · 能量炮",
        "舰船分类": ["护卫舰"],
        "舰船": "B",
        "武器标签": "能量炮",
        "攻击": 2,
        "damage_type": "能量",
        "is_energy": 1.0,
        "needs_mothership": 1.0,
        "crit_rate": 15.0,
        "crit_damage": 170.0,
        "crit_target": "舰船",
        "hit_fighter": 50.0,
        "hit_frigate": 100.0,
    },
    {
        "名称": "C · 未知舰",
        "舰船分类": ["未分类"],
        "舰船": "C",
        "武器标签": "未知炮",
        "攻击": 3,
        "damage_type": "实弹",
        "is_energy": 0.0,
        "crit_rate": 0.0,
        "crit_damage": 0.0,
        "crit_target": "",
        "hit_fighter": 10.0,
        "hit_frigate": 20.0,
    },
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
        {
            "title": "基础",
            "columns": 2,
            "fields": [
                {"field": "舰船", "label": "舰船"},
                {"field": "damage_type", "label": "伤害类型"},
                {"field": "攻击", "label": "攻击"},
                {"field": "crit_rate", "label": "暴击率"},
                {"field": "crit_damage", "label": "暴击伤害"},
                {"field": "crit_target", "label": "暴击目标"},
            ],
        },
        {
            "title": "命中率（%）",
            "columns": 2,
            "fields": [
                {"field": "hit_fighter", "label": "战机"},
                {"field": "hit_frigate", "label": "护卫舰"},
            ],
        },
    ],
}

_RULES = [
    {
        "source": "weapon",
        "field": "needs_mothership",
        "equals": 0,
        "disable": ["user_input.mothership_flight_bonus"],
        "reason": "该舰船不需要母舰",
    },
    {
        "source": "weapon",
        "field": "is_energy",
        "equals": 0,
        "disable": ["user_input.energy_armor"],
        "reason": "实弹武器使用物理护甲",
    },
    {
        "source": "weapon",
        "field": "is_energy",
        "equals": 1,
        "disable": ["user_input.physical_armor"],
        "reason": "能量武器使用能量护甲",
    },
]


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


def _write_pack(path: Path) -> Path:
    dag = {
        "schema_version": "dag-v1",
        "name": "实体详情测试",
        "variables": {
            "weapon.攻击": {"type": "float", "source": "weapon", "default": 0.0},
            "weapon.is_energy": {"type": "float", "source": "weapon", "default": 0.0},
            "weapon.needs_mothership": {"type": "float", "source": "weapon", "default": 0.0},
            "user_input.mothership_flight_bonus": {
                "type": "float",
                "source": "user_input",
                "default": 0.0,
                "description": "母舰飞行加成",
            },
            "user_input.physical_armor": {
                "type": "float",
                "source": "user_input",
                "default": 0.0,
                "description": "物理护甲",
            },
            "user_input.energy_armor": {
                "type": "float",
                "source": "user_input",
                "default": 0.0,
                "description": "能量护甲",
            },
        },
        "nodes": {"value": {"type": "var", "path": "weapon.攻击"}},
        "outputs": {"结果": {"node": "value", "label": "结果"}},
    }
    layout = {
        "schema_version": "ui-v1",
        "name": "实体详情测试",
        "sections": [
            {
                "id": "inputs",
                "type": "inputs",
                "title": "参数",
                "variables": [
                    "user_input.mothership_flight_bonus",
                    "user_input.physical_armor",
                    "user_input.energy_armor",
                ],
                "tab": "计算",
            },
            {"id": "outputs", "type": "outputs", "title": "输出", "outputs": ["结果"], "tab": "乘区明细"},
        ],
    }
    meta = {
        "name": "实体详情测试",
        "game": "测试",
        "version": "0.0.1",
        "schema_version": "dag-v1",
        "entry_dag": "dag/formula.dag.json",
        "entry_data": ["data/weapons.json"],
        "entity_selectors": _CASCADE,
        "entity_detail": _DETAIL,
        "entity_input_rules": _RULES,
    }
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("meta.json", json.dumps(meta, ensure_ascii=False))
        zf.writestr("dag/formula.dag.json", json.dumps(dag, ensure_ascii=False))
        zf.writestr("ui/layout.json", json.dumps(layout, ensure_ascii=False))
        zf.writestr("data/weapons.json", json.dumps(_RECORDS, ensure_ascii=False))
    return path


def _viewer(tmp_path: Path) -> CalcPackViewer:
    viewer = CalcPackViewer()
    viewer.load_calcpack(_write_pack(tmp_path / "meta.calcpack"))
    return viewer


def _widget(viewer: CalcPackViewer, path: str):
    return viewer._compute_sheet._input_widgets[path][0]  # noqa: SLF001


class TestEntityDetailPanel:
    def test_detail_panel_shows_default_record(self, qapp, tmp_path: Path) -> None:
        viewer = _viewer(tmp_path)

        labels = viewer._detail_value_labels  # noqa: SLF001
        assert labels["舰船"].text() == "A"
        assert labels["damage_type"].text() == "实弹"
        assert labels["攻击"].text() == "1"
        assert labels["crit_rate"].text() == "0"
        assert labels["crit_target"].text() == "—"
        assert labels["hit_fighter"].text() == "22"

    def test_detail_panel_updates_with_selection(self, qapp, tmp_path: Path) -> None:
        viewer = _viewer(tmp_path)
        combos = viewer._cascade_combos["weapon"]  # noqa: SLF001

        combos[0].setCurrentIndex(combos[0].findData("护卫舰"))

        labels = viewer._detail_value_labels  # noqa: SLF001
        assert labels["舰船"].text() == "B"
        assert labels["damage_type"].text() == "能量"
        assert labels["攻击"].text() == "2"
        assert labels["crit_rate"].text() == "15"
        assert labels["crit_damage"].text() == "170"
        assert labels["crit_target"].text() == "舰船"
        assert labels["hit_fighter"].text() == "50"

    def test_detail_values_scroll_when_panel_is_full(self, qapp, tmp_path: Path) -> None:
        from PySide6.QtWidgets import QScrollArea

        viewer = _viewer(tmp_path)

        scroll = viewer.findChild(QScrollArea, "detailScroll")
        assert scroll is not None
        assert scroll.widget() is viewer._detail_container  # noqa: SLF001

    def test_viewer_renders_layout_tabs(self, qapp, tmp_path: Path) -> None:
        from PySide6.QtWidgets import QTabWidget

        viewer = _viewer(tmp_path)

        tabs = viewer._compute_sheet.widget.findChild(QTabWidget)  # noqa: SLF001
        assert tabs is not None
        assert [tabs.tabText(index) for index in range(tabs.count())] == ["计算", "乘区明细"]


class TestEntityInputRules:
    def test_mothership_inputs_disabled_when_not_needed(self, qapp, tmp_path: Path) -> None:
        viewer = _viewer(tmp_path)

        assert not _widget(viewer, "user_input.mothership_flight_bonus").isEnabled()
        assert _widget(viewer, "user_input.mothership_flight_bonus").toolTip() == "该舰船不需要母舰"

    def test_mothership_inputs_enabled_when_needed(self, qapp, tmp_path: Path) -> None:
        viewer = _viewer(tmp_path)
        combos = viewer._cascade_combos["weapon"]  # noqa: SLF001

        combos[0].setCurrentIndex(combos[0].findData("护卫舰"))

        assert _widget(viewer, "user_input.mothership_flight_bonus").isEnabled()

    def test_unknown_mothership_requirement_keeps_input_enabled(self, qapp, tmp_path: Path) -> None:
        viewer = _viewer(tmp_path)
        combos = viewer._cascade_combos["weapon"]  # noqa: SLF001

        combos[0].setCurrentIndex(combos[0].findData("未分类"))

        assert _widget(viewer, "user_input.mothership_flight_bonus").isEnabled()

    def test_energy_weapon_switches_armor_input(self, qapp, tmp_path: Path) -> None:
        viewer = _viewer(tmp_path)

        assert _widget(viewer, "user_input.physical_armor").isEnabled()
        assert not _widget(viewer, "user_input.energy_armor").isEnabled()

        combos = viewer._cascade_combos["weapon"]  # noqa: SLF001
        combos[0].setCurrentIndex(combos[0].findData("护卫舰"))

        assert not _widget(viewer, "user_input.physical_armor").isEnabled()
        assert _widget(viewer, "user_input.energy_armor").isEnabled()
