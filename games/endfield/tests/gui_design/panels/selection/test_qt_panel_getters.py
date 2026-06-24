# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""PanelGettersMixin 委托方法测试。"""

from __future__ import annotations

from unittest.mock import MagicMock

from games.endfield.gui.panels.selection.qt_panel_getters_mixin import PanelGettersMixin


def _make_mixin(
    *,
    has_skill_panel: bool = True,
    has_trust_panel: bool = True,
    has_special_panel: bool = True,
) -> PanelGettersMixin:
    mixin = PanelGettersMixin()

    mixin.level_slider = MagicMock()

    mixin.level_slider.value.return_value = 60

    if has_skill_panel:
        sp = MagicMock()

        sp.skill_1_level = 7

        sp.skill_2_level = 8

        sp.skill_3_level = 9

        mixin.skill_panel = sp

    else:
        mixin.skill_panel = None

    if has_trust_panel:
        tp = MagicMock()

        tp.trust_level = 3

        mixin.trust_panel = tp

    else:
        mixin.trust_panel = None

    if has_special_panel:
        spec = MagicMock()

        spec.current_special_ability_1_name = "技能A"

        spec.current_special_ability_2_name = "技能B"

        spec.current_special_ability_3_name = "技能C"

        spec.current_weapon_special_name = "特殊X"

        spec.current_weapon_special_2_name = "特殊Y"

        spec.get_normal_skill_level.side_effect = lambda idx: [5, 6, 7][idx]

        spec.get_special_skill_level.side_effect = lambda idx: [3, 4][idx]

        spec.get_special_skill_stack.side_effect = lambda idx: [2, 1][idx]

        mixin.special_panel = spec

    else:
        mixin.special_panel = None

    return mixin


class TestPanelGettersMixin:
    def test_get_selected_data_none(self) -> None:
        mixin = PanelGettersMixin()

        mixin.name_combo = MagicMock()

        mixin.name_combo.currentText.return_value = ""

        mixin.data_list = [{"名称": "角色A"}]

        assert mixin.get_selected_data() is None

    def test_get_selected_data_found(self) -> None:
        mixin = PanelGettersMixin()

        mixin.name_combo = MagicMock()

        mixin.name_combo.currentText.return_value = "角色A"

        mixin.data_list = [{"名称": "角色A"}, {"名称": "角色B"}]

        result = mixin.get_selected_data()

        assert result == {"名称": "角色A"}

    def test_get_selected_data_empty_list(self) -> None:
        mixin = PanelGettersMixin()

        mixin.name_combo = MagicMock()

        mixin.name_combo.currentText.return_value = "不存在"

        mixin.data_list = []

        assert mixin.get_selected_data() is None

    def test_get_level(self) -> None:
        mixin = _make_mixin()

        assert mixin.get_level() == 60

    def test_get_skill_1_level_with_panel(self) -> None:
        mixin = _make_mixin(has_skill_panel=True)

        assert mixin.get_skill_1_level() == 7

    def test_get_skill_1_level_no_panel(self) -> None:
        mixin = _make_mixin(has_skill_panel=False)

        assert mixin.get_skill_1_level() == 0

    def test_get_skill_2_level_with_panel(self) -> None:
        mixin = _make_mixin(has_skill_panel=True)

        assert mixin.get_skill_2_level() == 8

    def test_get_skill_2_level_no_panel(self) -> None:
        mixin = _make_mixin(has_skill_panel=False)

        assert mixin.get_skill_2_level() == 0

    def test_get_skill_3_level_with_panel(self) -> None:
        mixin = _make_mixin(has_skill_panel=True)

        assert mixin.get_skill_3_level() == 9

    def test_get_skill_3_level_no_panel(self) -> None:
        mixin = _make_mixin(has_skill_panel=False)

        assert mixin.get_skill_3_level() == 0

    def test_get_trust_level_with_panel(self) -> None:
        mixin = _make_mixin(has_trust_panel=True)

        assert mixin.get_trust_level() == 3

    def test_get_trust_level_no_panel(self) -> None:
        mixin = _make_mixin(has_trust_panel=False)

        assert mixin.get_trust_level() == 0

    def test_get_normal_skill_1_name_with_panel(self) -> None:
        mixin = _make_mixin(has_special_panel=True)

        assert mixin.get_normal_skill_1_name() == "技能A"

    def test_get_normal_skill_1_name_no_panel(self) -> None:
        mixin = _make_mixin(has_special_panel=False)

        assert mixin.get_normal_skill_1_name() == ""

    def test_get_normal_skill_1_level_with_panel(self) -> None:
        mixin = _make_mixin(has_special_panel=True)

        assert mixin.get_normal_skill_1_level() == 5

    def test_get_normal_skill_1_level_no_panel(self) -> None:
        mixin = _make_mixin(has_special_panel=False)

        assert mixin.get_normal_skill_1_level() == 0

    def test_get_normal_skill_2_name(self) -> None:
        mixin = _make_mixin(has_special_panel=True)

        assert mixin.get_normal_skill_2_name() == "技能B"

    def test_get_normal_skill_2_name_no_panel(self) -> None:
        mixin = _make_mixin(has_special_panel=False)

        assert mixin.get_normal_skill_2_name() == ""

    def test_get_normal_skill_2_level_with_panel(self) -> None:
        mixin = _make_mixin(has_special_panel=True)

        assert mixin.get_normal_skill_2_level() == 6

    def test_get_normal_skill_2_level_no_panel(self) -> None:
        mixin = _make_mixin(has_special_panel=False)

        assert mixin.get_normal_skill_2_level() == 0

    def test_get_normal_skill_3_name(self) -> None:
        mixin = _make_mixin(has_special_panel=True)

        assert mixin.get_normal_skill_3_name() == "技能C"

    def test_get_normal_skill_3_name_no_panel(self) -> None:
        mixin = _make_mixin(has_special_panel=False)

        assert mixin.get_normal_skill_3_name() == ""

    def test_get_normal_skill_3_level_with_panel(self) -> None:
        mixin = _make_mixin(has_special_panel=True)

        assert mixin.get_normal_skill_3_level() == 7

    def test_get_normal_skill_3_level_no_panel(self) -> None:
        mixin = _make_mixin(has_special_panel=False)

        assert mixin.get_normal_skill_3_level() == 0

    def test_get_special_skill_1_name_with_panel(self) -> None:
        mixin = _make_mixin(has_special_panel=True)

        assert mixin.get_special_skill_1_name() == "特殊X"

    def test_get_special_skill_1_name_no_panel(self) -> None:
        mixin = _make_mixin(has_special_panel=False)

        assert mixin.get_special_skill_1_name() == ""

    def test_get_special_skill_1_level_with_panel(self) -> None:
        mixin = _make_mixin(has_special_panel=True)

        assert mixin.get_special_skill_1_level() == 3

    def test_get_special_skill_1_level_no_panel(self) -> None:
        mixin = _make_mixin(has_special_panel=False)

        assert mixin.get_special_skill_1_level() == 1

    def test_get_special_skill_1_stack_with_panel(self) -> None:
        mixin = _make_mixin(has_special_panel=True)

        assert mixin.get_special_skill_1_stack() == 2

    def test_get_special_skill_1_stack_no_panel(self) -> None:
        mixin = _make_mixin(has_special_panel=False)

        assert mixin.get_special_skill_1_stack() == 0

    def test_get_special_skill_2_name(self) -> None:
        mixin = _make_mixin(has_special_panel=True)

        assert mixin.get_special_skill_2_name() == "特殊Y"

    def test_get_special_skill_2_level_with_panel(self) -> None:
        mixin = _make_mixin(has_special_panel=True)

        assert mixin.get_special_skill_2_level() == 4

    def test_get_special_skill_2_level_no_panel(self) -> None:
        mixin = _make_mixin(has_special_panel=False)

        assert mixin.get_special_skill_2_level() == 1

    def test_get_special_skill_2_stack_with_panel(self) -> None:
        mixin = _make_mixin(has_special_panel=True)

        assert mixin.get_special_skill_2_stack() == 1

    def test_get_special_skill_2_stack_no_panel(self) -> None:
        mixin = _make_mixin(has_special_panel=False)

        assert mixin.get_special_skill_2_stack() == 0

    def test_compat_get_special_ability_1_name(self) -> None:
        mixin = _make_mixin(has_special_panel=True)

        assert mixin.get_special_ability_1_name() == mixin.get_normal_skill_1_name()

    def test_compat_get_special_ability_1_level(self) -> None:
        mixin = _make_mixin(has_special_panel=True)

        assert mixin.get_special_ability_1_level() == mixin.get_normal_skill_1_level()

    def test_compat_get_weapon_special_name(self) -> None:
        mixin = _make_mixin(has_special_panel=True)

        assert mixin.get_weapon_special_name() == mixin.get_special_skill_1_name()

    def test_compat_get_weapon_special_level(self) -> None:
        mixin = _make_mixin(has_special_panel=True)

        assert mixin.get_weapon_special_level() == mixin.get_special_skill_1_level()

    def test_compat_get_weapon_special_stack(self) -> None:
        mixin = _make_mixin(has_special_panel=True)

        assert mixin.get_weapon_special_stack() == mixin.get_special_skill_1_stack()

    def test_compat_get_weapon_special_2_name(self) -> None:
        mixin = _make_mixin(has_special_panel=True)

        assert mixin.get_weapon_special_2_name() == mixin.get_special_skill_2_name()

    def test_compat_get_weapon_special_2_level(self) -> None:
        mixin = _make_mixin(has_special_panel=True)

        assert mixin.get_weapon_special_2_level() == mixin.get_special_skill_2_level()

    def test_compat_get_weapon_special_2_stack(self) -> None:
        mixin = _make_mixin(has_special_panel=True)

        assert mixin.get_weapon_special_2_stack() == mixin.get_special_skill_2_stack()

    def test_compat_get_special_ability_1_name_no_panel(self) -> None:
        mixin = _make_mixin(has_special_panel=False)

        assert mixin.get_special_ability_1_name() == ""

    def test_compat_get_special_ability_1_level_no_panel(self) -> None:
        mixin = _make_mixin(has_special_panel=False)

        assert mixin.get_special_ability_1_level() == 0

    def test_compat_get_special_ability_2_name_no_panel(self) -> None:
        mixin = _make_mixin(has_special_panel=False)

        assert mixin.get_special_ability_2_name() == ""

    def test_compat_get_special_ability_2_level_no_panel(self) -> None:
        mixin = _make_mixin(has_special_panel=False)

        assert mixin.get_special_ability_2_level() == 0

    def test_compat_get_special_ability_3_name_no_panel(self) -> None:
        mixin = _make_mixin(has_special_panel=False)

        assert mixin.get_special_ability_3_name() == ""

    def test_compat_get_special_ability_3_level_no_panel(self) -> None:
        mixin = _make_mixin(has_special_panel=False)

        assert mixin.get_special_ability_3_level() == 0

    def test_compat_get_weapon_special_name_no_panel(self) -> None:
        mixin = _make_mixin(has_special_panel=False)

        assert mixin.get_weapon_special_name() == ""

    def test_compat_get_weapon_special_level_no_panel(self) -> None:
        mixin = _make_mixin(has_special_panel=False)

        assert mixin.get_weapon_special_level() == 1

    def test_compat_get_weapon_special_stack_no_panel(self) -> None:
        mixin = _make_mixin(has_special_panel=False)

        assert mixin.get_weapon_special_stack() == 0

    def test_compat_get_weapon_special_2_name_no_panel(self) -> None:
        mixin = _make_mixin(has_special_panel=False)

        assert mixin.get_weapon_special_2_name() == ""

    def test_compat_get_weapon_special_2_level_no_panel(self) -> None:
        mixin = _make_mixin(has_special_panel=False)

        assert mixin.get_weapon_special_2_level() == 1

    def test_compat_get_weapon_special_2_stack_no_panel(self) -> None:
        mixin = _make_mixin(has_special_panel=False)

        assert mixin.get_weapon_special_2_stack() == 0
