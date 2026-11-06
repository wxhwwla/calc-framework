# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""CalcPackViewer 级联实体选择器 — 舰船种类 → 舰船 → 武器。

同时验证：没有任何数值列表字段时自动隐藏等级输入框；有列表字段时保留。
"""

from __future__ import annotations

import json
import sys
import zipfile
from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication

from calc_framework.ui.viewer import CalcPackViewer


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


_WEAPON_RECORDS: list[dict[str, object]] = [
    {
        "名称": "A · 炮1",
        "舰船分类": ["战机"],
        "舰船": "A",
        "武器标签": "炮1",
        "攻击": 1,
    },
    {
        "名称": "A · 炮2",
        "舰船分类": ["战机"],
        "舰船": "A",
        "武器标签": "炮2",
        "攻击": 2,
    },
    {
        "名称": "B · 炮1",
        "舰船分类": ["护卫舰", "登陆舰"],
        "舰船": "B",
        "武器标签": "炮1",
        "攻击": 3,
    },
    {
        "名称": "C · 刀",
        "舰船分类": ["未分类"],
        "舰船": "C",
        "武器标签": "刀",
        "攻击": 4,
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


def _dag(variable: str) -> dict[str, object]:
    return {
        "schema_version": "dag-v1",
        "name": "级联测试",
        "variables": {
            variable: {
                "type": "float",
                "source": variable.split(".", 1)[0],
                "description": "测试变量",
                "default": 0,
            },
            "user_input.系数": {
                "type": "float",
                "source": "user_input",
                "description": "系数",
                "default": 1,
            },
        },
        "nodes": {"value": {"type": "var", "path": variable}},
        "outputs": {"结果": {"node": "value", "label": "结果"}},
    }


def _layout() -> dict[str, object]:
    return {
        "schema_version": "ui-v1",
        "name": "级联测试",
        "sections": [
            {"id": "inputs", "type": "inputs", "title": "输入", "variables": ["user_input.系数"]},
            {"id": "outputs", "type": "outputs", "title": "输出", "outputs": ["结果"]},
        ],
    }


def _write_pack(
    path: Path,
    *,
    meta_extra: dict[str, object] | None = None,
    weapon_records: list[dict[str, object]] | None = None,
    character_records: list[dict[str, object]] | None = None,
    variable: str = "weapon.攻击",
) -> Path:
    meta: dict[str, object] = {
        "name": "级联测试",
        "game": "测试",
        "version": "0.0.1",
        "schema_version": "dag-v1",
        "entry_dag": "dag/formula.dag.json",
    }
    meta.update(meta_extra or {})

    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("meta.json", json.dumps(meta, ensure_ascii=False))
        zf.writestr("dag/formula.dag.json", json.dumps(_dag(variable), ensure_ascii=False))
        zf.writestr("ui/layout.json", json.dumps(_layout(), ensure_ascii=False))
        if weapon_records is not None:
            zf.writestr("data/weapons.json", json.dumps(weapon_records, ensure_ascii=False))
        if character_records is not None:
            zf.writestr("data/characters.json", json.dumps(character_records, ensure_ascii=False))
    return path


def _cascade_viewer(tmp_path: Path) -> CalcPackViewer:
    pack = _write_pack(
        tmp_path / "cascade.calcpack",
        meta_extra={"entity_selectors": _CASCADE, "entry_data": ["data/weapons.json"]},
        weapon_records=_WEAPON_RECORDS,
    )
    viewer = CalcPackViewer()
    viewer.load_calcpack(pack)
    return viewer


class TestCascadeSelectors:
    def test_three_linked_combos_are_built(self, qapp, tmp_path: Path) -> None:
        viewer = _cascade_viewer(tmp_path)

        combos = viewer._cascade_combos["weapon"]  # noqa: SLF001
        assert len(combos) == 3
        assert [combo.count() for combo in combos] == [4, 1, 2]
        assert viewer._entity_form.rowCount() == 3  # noqa: SLF001

    def test_final_combo_shows_weapon_label_and_stores_record_name(self, qapp, tmp_path: Path) -> None:
        viewer = _cascade_viewer(tmp_path)

        weapon_combo = viewer._cascade_combos["weapon"][-1]  # noqa: SLF001
        assert weapon_combo.currentText() == "炮1"
        assert weapon_combo.currentData() == "A · 炮1"

    def test_default_selection_builds_weapon_context(self, qapp, tmp_path: Path) -> None:
        viewer = _cascade_viewer(tmp_path)

        assert viewer._build_current_context()["weapon"]["攻击"] == 1.0  # noqa: SLF001

    def test_changing_ship_type_rebuilds_ship_and_weapon(self, qapp, tmp_path: Path) -> None:
        viewer = _cascade_viewer(tmp_path)
        combos = viewer._cascade_combos["weapon"]  # noqa: SLF001

        combos[0].setCurrentIndex(combos[0].findData("护卫舰"))

        assert combos[1].currentData() == "B"
        assert combos[2].currentText() == "炮1"
        assert combos[2].currentData() == "B · 炮1"
        assert viewer._build_current_context()["weapon"]["攻击"] == 3.0  # noqa: SLF001

    def test_composite_ship_type_finds_same_ship(self, qapp, tmp_path: Path) -> None:
        viewer = _cascade_viewer(tmp_path)
        combos = viewer._cascade_combos["weapon"]  # noqa: SLF001

        combos[0].setCurrentIndex(combos[0].findData("登陆舰"))

        assert combos[1].currentData() == "B"
        assert combos[2].currentData() == "B · 炮1"

    def test_changing_weapon_updates_context(self, qapp, tmp_path: Path) -> None:
        viewer = _cascade_viewer(tmp_path)
        combos = viewer._cascade_combos["weapon"]  # noqa: SLF001

        combos[2].setCurrentIndex(1)

        assert combos[2].currentData() == "A · 炮2"
        assert viewer._build_current_context()["weapon"]["攻击"] == 2.0  # noqa: SLF001

    def test_switching_type_to_unclassified_rebuilds_weapon(self, qapp, tmp_path: Path) -> None:
        viewer = _cascade_viewer(tmp_path)
        combos = viewer._cascade_combos["weapon"]  # noqa: SLF001

        combos[0].setCurrentIndex(combos[0].findData("未分类"))

        assert combos[1].currentData() == "C"
        assert combos[2].currentText() == "刀"
        assert viewer._build_current_context()["weapon"]["攻击"] == 4.0  # noqa: SLF001


class TestLevelVisibility:
    def test_level_spin_hidden_when_no_numeric_lists(self, qapp, tmp_path: Path) -> None:
        viewer = _cascade_viewer(tmp_path)

        assert viewer._level_spin is None  # noqa: SLF001
        for combo in viewer._entity_selectors.values():  # noqa: SLF001
            assert combo is not None

    def test_level_spin_kept_when_entity_has_numeric_list(self, qapp, tmp_path: Path) -> None:
        pack = _write_pack(
            tmp_path / "leveled.calcpack",
            weapon_records=None,
            character_records=[{"名称": "角色", "属性": [10, 20, 30]}],
            variable="character.属性",
        )
        viewer = CalcPackViewer()
        viewer.load_calcpack(pack)

        assert viewer._level_spin is not None  # noqa: SLF001
        assert viewer._level_spin.value() == 90  # noqa: SLF001
