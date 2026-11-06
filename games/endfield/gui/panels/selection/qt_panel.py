#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# SPDX-License-Identifier: AGPL-3.0
"""

PySide6 选择面板：类型/星级/名称/等级四级联动 + 子面板（信赖/技能/特殊能力）。



替代 CTk 版 ``ChooseTypesStarsNamesLevels``（panel.py + cascade.py + state.py + accessors.py 四合一的 mixin）。

控件构建与级联事件分别见 ``qt_panel_build_mixin.py`` / ``qt_panel_events_mixin.py``。

"""

from __future__ import annotations

from typing import Any

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QWidget

from .qt_ability_panel import QtSpecialAbilityPanel
from .qt_panel_build_mixin import QtPanelBuildMixin
from .qt_panel_events_mixin import QtPanelEventsMixin
from .qt_panel_getters_mixin import PanelGettersMixin
from .qt_subpanels import QtSkillLevelPanel, QtTrustPanel


class QtSelectionPanel(QtPanelEventsMixin, QtPanelBuildMixin, PanelGettersMixin, QWidget):
    """通用的四级联动选择面板（角色/武器共用）。



    属性：

        data_list: 数据列表（get_characters() / get_weapons() 的返回值）

        is_weapon_panel: 是否为武器面板

        type_combo: 类型下拉框（QComboBox）

        star_combo: 星级下拉框

        name_combo: 名称下拉框

        level_slider: 等级滑块

        trust_panel: 信赖等级面板（仅角色侧，QtTrustPanel）

        skill_panel: 技能等级面板（仅角色侧，QtSkillLevelPanel）

        special_panel: 武器特殊能力面板（仅武器侧，QtSpecialAbilityPanel）

    """

    def __init__(
        self,
        data_list: list[dict[str, Any]],
        font: QFont,
        *,
        is_weapon_panel: bool = False,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)  # pyright: ignore[reportCallIssue]

        self.data_list: list[dict[str, Any]] = data_list

        self.is_weapon_panel: bool = is_weapon_panel

        self._font = font

        self.trust_panel: QtTrustPanel | None = None

        self.skill_panel: QtSkillLevelPanel | None = None

        self.special_panel: QtSpecialAbilityPanel | None = None

        self._build_gui()

        self._connect_signals()

        self._init_values()
        """初始化实例。"""
