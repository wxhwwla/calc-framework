# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""Arknights ComputeSheet 工厂与上下文同步测试。"""

from __future__ import annotations

import sys
from collections.abc import Iterator

import pytest
from PySide6.QtWidgets import QApplication


@pytest.fixture(scope="module")
def qapp() -> Iterator[QApplication]:
    existing = QApplication.instance()
    if isinstance(existing, QApplication):
        app = existing
    else:
        app = QApplication(sys.argv)
    yield app


def test_create_and_evaluate_compute_sheet(qapp: QApplication, amiya_operator: dict) -> None:
    from calc_framework.config.adapter import AdapterPackage

    from games.arknights.framework_bridge import load_layout_json
    from games.arknights.gui.arknights_compute_sheet import (
        build_result_html,
        combo_index_to_skill_index,
        create_arknights_compute_sheet,
        populate_operator_context,
    )
    from utils.path_utils import get_resource_path

    adapter_dir = get_resource_path("framework/adapters/arknights")
    pkg = AdapterPackage(str(adapter_dir))
    layout_path = adapter_dir / "ui" / "layout.json"
    layout = load_layout_json(layout_path.read_text(encoding="utf-8"))

    sheet = create_arknights_compute_sheet(pkg.dag_service, layout)
    _ = sheet.widget  # 触发控件树构建

    populate_operator_context(
        sheet,
        amiya_operator,
        skill_multiplier=1.5,
        skill_level=7,
    )
    result = sheet.evaluate()

    assert result.outputs.get("最终攻击力") is not None
    html = build_result_html(result)
    assert "最终攻击力" in html
    assert combo_index_to_skill_index(0) == -1
    assert combo_index_to_skill_index(2) == 1


def test_merge_atk_percent_bonus() -> None:
    from games.arknights.gui.arknights_compute_sheet import merge_atk_percent_bonus

    assert merge_atk_percent_bonus(10.0, 0.15) == pytest.approx(25.0)
    assert merge_atk_percent_bonus(0.0, 0.0) == 0.0


def test_layout_for_damage_app(qapp: QApplication) -> None:
    from games.arknights.gui.arknights_compute_sheet import (
        DAMAGE_APP_BONUS_VARS,
        ensure_arknights_adapter,
        layout_for_damage_app,
    )

    _, full_layout = ensure_arknights_adapter()
    layout = layout_for_damage_app(full_layout)
    all_vars: list[str] = []
    for sec in layout.sections:
        all_vars.extend(sec.variables)
    for var in DAMAGE_APP_BONUS_VARS:
        assert var in all_vars
    assert "user_input.敌人防御" in all_vars
    assert "user_input.信赖攻击" in all_vars


def test_read_enemy_bonus_params(qapp: QApplication, amiya_operator: dict) -> None:
    from games.arknights.gui.arknights_compute_sheet import (
        create_arknights_compute_sheet,
        ensure_arknights_adapter,
        layout_for_damage_app,
        populate_operator_context,
        read_enemy_bonus_params,
    )

    pkg, full_layout = ensure_arknights_adapter()
    param_layout = layout_for_damage_app(full_layout)
    sheet = create_arknights_compute_sheet(pkg.dag_service, param_layout)
    _ = sheet.widget
    populate_operator_context(sheet, amiya_operator, skill_multiplier=1.0, skill_level=7)

    params = read_enemy_bonus_params(sheet)
    assert params["enemy_def"] == 200.0
    assert params["trust_atk"] == 70.0
    assert params["pot_atk"] == 30.0


def test_arknights_app_embedded_init(qapp: QApplication) -> None:
    from games.arknights.gui.ArknightsApp import ArknightsApp

    win = ArknightsApp(embedded=True)
    assert win._embedded is True
    assert win._compute_sheet is not None
    assert len(win._operator_index) >= 1
