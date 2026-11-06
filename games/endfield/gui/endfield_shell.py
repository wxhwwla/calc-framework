# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""ShellMixin — 终末地伤害计算主窗口面板创建与布局。

采用共享 ``CalculatorShell``：

- 顶部工具条：帮助、捐赠、数据来源、搜索历史、日志与工具菜单。
- 计算页 2×2：角色选择 | 武器选择 / 角色基础数据 | 武器加成数据。
- 高级页 2×2：敌人与装备参数 | 技能与加成参数 / 乘区明细 | 总伤害。
- 底部固定确认按钮与页签；选择/输入变更只标记待确认。
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, cast

from calc_framework.ui.calculator_shell import CalculatorPage, CalculatorShell
from calc_framework.ui.i18n import tr
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMenu,
    QPushButton,
    QScrollArea,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from games.endfield.data_loading.equipment_catalog import get_equipment_catalog
from games.endfield.data_loading.loader import get_characters, get_weapons
from games.endfield.gui.panels.selection.qt_panel import QtSelectionPanel
from games.endfield.gui.presentation.total_damage_panel import TotalDamagePanel
from games.endfield.gui.shared.display_view.qt_columns import QtAttributeColumns
from games.endfield.gui.shared.weapon_filter import filter_weapons_for_character
from games.endfield.gui.shell.qt_control_dock import QtControlDock

_CONFIRM_PENDING_STYLE = """
    QPushButton { background-color: #7C3AED; color: white;
                  border: none; border-radius: 4px;
                  font-size: 14px; font-weight: bold; }
    QPushButton:hover { background-color: #6D28D9; }
    QPushButton:disabled { background-color: #444; color: #888; }
"""


def _scrollable(widget: QWidget) -> QScrollArea:
    """把内容包进滚动区，避免固定 2×2 区域被长面板撑破。"""
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QFrame.Shape.NoFrame)
    scroll.setWidget(widget)
    return scroll


class ShellMixin:
    """面板创建与布局混合类。

    提供共享外壳初始化、计算页/高级页 2×2 构建、角色/武器选择面板联动、
    控件面板初始化。由 EndfieldApp 继承使用。
    """

    def _tool_slot(self, method_name: str) -> Callable[[], None]:
        """把 mixin 方法包装为无参回调（供工具条复用）。"""

        def _invoke() -> None:
            getattr(self, method_name)()

        return _invoke

    def _init_shell(self) -> None:
        """创建顶部工具条 + 页面栈 + 底部确认/页签外壳。"""
        self._shell = CalculatorShell(cast(QWidget, self))
        self.setCentralWidget(self._shell)
        self.status_label = self._shell.status_label
        self._shell.confirmed.connect(self._on_confirm)
        self._shell.set_status(tr("common.ready"))
        self._build_toolbar()

    def _build_toolbar(self) -> None:
        """把所有与计算无关的入口收进顶部工具条。"""
        shell = self._shell
        shell.add_tool_action(tr("desktop.endfield.helpUsage"), self._tool_slot("_on_open_help"), shortcut="F1")
        shell.add_tool_action(tr("desktop.endfield.dataAttribution"), self._tool_slot("_on_attribution"))
        shell.add_tool_action(tr("desktop.endfield.donate"), self._tool_slot("_on_donation"))
        shell.add_tool_action(tr("desktop.endfield.searchHistory"), self._tool_slot("_on_search_history"))
        if callable(getattr(self, "_open_log_dialog", None)):
            shell.add_tool_action(tr("desktop.endfield.runtimeLogs"), self._tool_slot("_open_log_dialog"))
        shell.add_tool_separator()

        tools = QToolButton(shell.toolbar)
        tools.setText(tr("desktop.endfield.sectionTools"))
        tools.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        menu = QMenu(tools)
        tool_actions = (
            ("exportPreset", "_on_export_preset"),
            ("importPreset", "_on_import_preset"),
            ("comparePresets", "_on_compare_presets"),
            ("damageDashboard", "_on_damage_dashboard"),
            ("calcHistory", "_on_calc_history"),
            ("exportOpLog", "_on_export_log"),
            ("ocrDetect", "_on_ocr_detect"),
        )
        for i18n_key, method_name in tool_actions:
            slot = getattr(self, method_name, None)
            if not callable(slot):
                continue
            action = menu.addAction(tr(f"desktop.endfield.{i18n_key}"))
            action.triggered.connect(lambda *_, handler=slot: handler())
        tools.setMenu(menu)
        shell.add_tool_widget(tools)

    def _show_main_page(self) -> None:
        """切换回计算页。"""
        self._shell.set_current_page(0)

    def _build_calc_page(self) -> None:
        """计算页 2×2：角色选择 | 武器选择 / 角色基础 | 武器加成。"""
        characters = get_characters()
        weapons = get_weapons()
        self.all_weapons: list[dict[str, Any]] = list(weapons)

        self.char_panel = QtSelectionPanel(characters, self.big_font, parent=None)
        self.weapon_panel = QtSelectionPanel(weapons, self.big_font, is_weapon_panel=True, parent=None)
        self.columns: QtAttributeColumns = QtAttributeColumns(
            big_font=self.big_font,
            small_font=self.small_font,
            embedded=True,
        )

        page = CalculatorPage(
            top_left_title=tr("desktop.endfield.zoneCharSelect"),
            top_right_title=tr("desktop.endfield.zoneWeaponSelect"),
            bottom_left_title=tr("desktop.endfield.zoneCharBase"),
            bottom_right_title=tr("desktop.endfield.zoneWeaponBonus"),
        )
        page.zone("top_left").add_widget(_scrollable(self.char_panel))
        page.zone("top_right").add_widget(_scrollable(self.weapon_panel))
        page.zone("bottom_left").add_widget(self.columns.char_table)
        page.zone("bottom_right").add_widget(self.columns.weapon_table)

        self._calc_page = page
        self.calc_page = page
        self._shell.add_page(tr("desktop.endfield.tabCalc"), page)

    def _build_adv_page(self) -> None:
        """高级页 2×2：敌人/装备 | 技能/加成 / 乘区明细 | 总伤害。"""
        self.control_dock: QtControlDock = QtControlDock(
            big_font=self.big_font,
            small_font=self.small_font,
            on_back_to_main=self._show_main_page,
            on_confirm=self._on_confirm,
            on_attribution=self._on_attribution,
            on_donation=self._on_donation,
            on_open_help=self._on_open_help,
            on_ocr_detect=self._on_ocr_detect,
            on_search_history=self._on_search_history,
        )
        dock = self.control_dock

        enemy_body = QWidget()
        enemy_layout = QVBoxLayout(enemy_body)
        enemy_layout.setContentsMargins(0, 0, 0, 0)
        enemy_layout.setSpacing(4)
        enemy_layout.addWidget(dock._enemy_panel)
        mode_row = QHBoxLayout()
        mode_row.addWidget(QLabel(tr("desktop.endfield.calcModeLabel")))
        mode_row.addWidget(dock.calc_mode_menu, 1)
        enemy_layout.addLayout(mode_row)
        enemy_layout.addStretch()

        enemy_equipment = QWidget()
        enemy_equipment_layout = QVBoxLayout(enemy_equipment)
        enemy_equipment_layout.setContentsMargins(0, 0, 0, 0)
        enemy_equipment_layout.setSpacing(4)
        enemy_equipment_layout.addWidget(_scrollable(enemy_body), 1)
        enemy_equipment_layout.addWidget(dock._col_search, 1)

        page = CalculatorPage(
            top_left_title=tr("desktop.endfield.zoneEnemyEquip"),
            top_right_title=tr("desktop.endfield.zoneSkillBonus"),
            bottom_left_title=tr("desktop.endfield.zoneBreakdown"),
            bottom_right_title=tr("desktop.endfield.zoneTotalDamage"),
        )
        page.zone("top_left").add_widget(enemy_equipment)
        page.zone("top_right").add_widget(dock._col_multi)
        page.zone("bottom_left").add_widget(self.columns.zone_table)

        self._total_damage_panel = TotalDamagePanel(self.big_font, self.small_font)
        page.zone("bottom_right").add_widget(self._total_damage_panel)

        self._adv_page = page
        self.adv_page = page
        self._shell.add_page(tr("desktop.endfield.tabAdvanced"), page)

    def _confirm_buttons(self) -> list[QPushButton]:
        """当前可见的确认按钮（底部工具条固定按钮）。"""
        if hasattr(self, "_shell"):
            return [self._shell.confirm_button]
        return []

    def _set_confirm_ui_pending(self) -> None:
        """配装变更后：底部确认按钮显示待更新。"""
        self._shell.set_pending(tr("desktop.endfield.confirmPending"))
        self._shell.confirm_button.setStyleSheet(_CONFIRM_PENDING_STYLE)
        self._shell.set_status(tr("desktop.endfield.pendingConfirm"))

    def _set_confirm_ui_computing(self) -> None:
        """计算进行中。"""
        self._shell.set_confirm_enabled(False)
        self._shell.set_confirm_text(tr("desktop.endfield.computing"))
        self._shell.set_status(tr("desktop.endfield.computing"))

    def _set_confirm_ui_confirmed(self) -> None:
        """确认完成。"""
        self._shell.set_confirmed(tr("desktop.endfield.confirmed"))
        self._shell.confirm_button.setStyleSheet(getattr(self, "_confirm_btn_default_style", ""))
        self._shell.set_status(tr("desktop.endfield.confirmed"))

    def _on_char_name_change(self) -> None:
        char_data = self.char_panel.get_selected_data()
        filtered = filter_weapons_for_character(self.all_weapons, char_data)
        self.weapon_panel.update_data_list(filtered)
        self._rebuild_segment_rows()
        self._on_loadout_changed()
        """on char name change。"""

    def _rebuild_segment_rows(self) -> None:
        char_data = self.char_panel.get_selected_data()
        if not char_data:
            self.control_dock.rebuild_segment_rows(None, 1, 1, 1)
            return
        s1 = self.char_panel.get_skill_1_level()
        s2 = self.char_panel.get_skill_2_level()
        s3 = self.char_panel.get_skill_3_level()
        self.control_dock.rebuild_segment_rows(char_data, s1, s2, s3)
        """rebuild segment rows。"""

    def _on_calc_mode_changed(self, mode_id: str) -> None:
        self._current_calc_mode = mode_id
        self._on_loadout_changed()
        """on calc mode changed。"""

    def _on_loadout_changed(self) -> None:
        self._set_confirm_ui_pending()
        self._rebuild_segment_rows()
        self._total_damage_panel.hide_damage()
        """on loadout changed。"""

    def _init_control_dock(self) -> None:
        dock = self.control_dock

        self._confirm_btn_default_style = dock.confirm_btn.styleSheet()
        self._shell.confirm_button.setStyleSheet(self._confirm_btn_default_style)

        dock._enemy_panel.enemy_params_changed.connect(self._on_enemy_params_changed)
        initial_params = dock._enemy_panel.get_params()
        self._apply_enemy_params(initial_params)

        self._equipment_catalog: dict[str, list[dict[str, Any]]] = get_equipment_catalog()
        dock.populate_fixed_loadout_slots(self._equipment_catalog)

        self._search_cancel_token = None
        self._search_estimated_total_seconds: float = 0.0

        dock.equipment_scope_combo.currentTextChanged.connect(self._on_equipment_scope_changed)

        # 敌人参数现在位于高级页左上区域，不再藏在「更多设置」里。
        dock._enemy_panel.setVisible(True)

        dock._manual_buff_btn.clicked.connect(self._on_manual_buff)
        dock._survival_btn.clicked.connect(self._on_survival_estimate)
        """init control dock。"""

    def _on_equipment_scope_changed(self, scope_label: str) -> None:
        self._equipment_catalog = get_equipment_catalog(scope_label=scope_label)
        self.control_dock.populate_fixed_loadout_slots(self._equipment_catalog)
        self._on_loadout_changed()
        """on equipment scope changed。"""
