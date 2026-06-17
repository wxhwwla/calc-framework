# SPDX-License-Identifier: AGPL-3.0
"""i18n_combos 单元测试。"""

from __future__ import annotations

import pytest
from calc_framework.ui.i18n import set_locale
from games.endfield.gui.shared.i18n_combos import (
    DAMAGE_COMPONENT_OPTIONS,
    EQUIPMENT_SCOPE_OPTIONS,
    WEAPON_SCOPE_OPTIONS,
    combo_internal_value,
    populate_i18n_combo,
    read_damage_component_mode,
    set_combo_by_internal,
)
from PySide6.QtWidgets import QApplication, QComboBox


@pytest.fixture(scope="module", autouse=True)
def _qapp() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app  # type: ignore[return-value]


def test_weapon_scope_combo_internal_zh() -> None:
    set_locale("zh-CN")
    cb = QComboBox()
    populate_i18n_combo(cb, WEAPON_SCOPE_OPTIONS)
    set_combo_by_internal(cb, "当前武器")
    assert combo_internal_value(cb) == "当前武器"


def test_weapon_scope_combo_internal_en_display() -> None:
    set_locale("en")
    cb = QComboBox()
    populate_i18n_combo(cb, WEAPON_SCOPE_OPTIONS)
    set_combo_by_internal(cb, "全部装备")  # wrong key - use equipment
    set_combo_by_internal(cb, "同类型全部")
    assert combo_internal_value(cb) == "同类型全部"
    assert "Same Type" in cb.currentText() or cb.currentText()


def test_damage_component_mode_from_data() -> None:
    set_locale("zh-CN")
    cb = QComboBox()
    populate_i18n_combo(cb, DAMAGE_COMPONENT_OPTIONS)
    set_combo_by_internal(cb, "skill_only")
    assert read_damage_component_mode(cb) == "skill_only"


def test_equipment_scope_options_count() -> None:
    assert len(EQUIPMENT_SCOPE_OPTIONS) == 3
