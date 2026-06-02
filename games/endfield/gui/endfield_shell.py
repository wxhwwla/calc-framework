# SPDX-License-Identifier: AGPL-3.0
"""ShellMixin — 终末地伤害计算主窗口面板创建与布局。

P2 迁移目标：所有面板最终使用 ComputeSheet + layout.json。
"""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QSizePolicy,
    QSplitter,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from games.endfield.data_loading.equipment_catalog import get_equipment_catalog
from games.endfield.data_loading.loader import get_characters, get_weapons
from games.endfield.framework_bridge import ComputeSheet
from games.endfield.gui.shared.calc_mode_labels import calculation_mode_from_label
from games.endfield.gui.shared.display_view.qt_columns import QtAttributeColumns
from games.endfield.gui.panels.selection.qt_panel import QtSelectionPanel
from games.endfield.gui.shell.qt_control_dock import QtControlDock
from games.endfield.gui.presentation.total_damage_panel import TotalDamagePanel


class ShellMixin:
    """面板创建与布局混合类。

    提供计算页/高级页构建、角色/武器选择面板联动、控件面板初始化。
    由 EndfieldApp 继承使用。
    """

    def _show_main_page(self) -> None:
        self.tabs.setCurrentIndex(0)
        """show main page。"""

    def _build_calc_page(self) -> None:
        calc_page = QWidget()
        calc_layout = QVBoxLayout(calc_page)
        calc_layout.setContentsMargins(0, 0, 0, 0)
        calc_layout.setSpacing(4)

        characters = get_characters()
        weapons = get_weapons()
        self.all_weapons: list[dict[str, Any]] = list(weapons)

        panels_frame = QFrame()
        panels_frame.setStyleSheet("QFrame { background-color: #1E1E1E; border-radius: 8px; }")
        panels_row = QHBoxLayout(panels_frame)
        panels_row.setContentsMargins(8, 8, 8, 8)
        panels_row.setSpacing(12)

        self.char_panel = QtSelectionPanel(characters, self.big_font, parent=None)
        self.weapon_panel = QtSelectionPanel(weapons, self.big_font, is_weapon_panel=True, parent=None)

        panels_row.addWidget(self.char_panel, stretch=1)
        line = QFrame()
        line.setFrameShape(QFrame.Shape.VLine)
        line.setStyleSheet("color: #333333;")
        panels_row.addWidget(line)
        panels_row.addWidget(self.weapon_panel, stretch=1)

        calc_layout.addWidget(panels_frame)

        content_split = QSplitter(Qt.Orientation.Horizontal)
        calc_layout.addWidget(content_split, stretch=1)

        self.columns: QtAttributeColumns = QtAttributeColumns(big_font=self.big_font, small_font=self.small_font)
        content_split.addWidget(self.columns)

        self._compute_sheet: ComputeSheet | None = None
        self._compute_sheet_widget: QWidget = QWidget()
        sheet_layout = QVBoxLayout(self._compute_sheet_widget)
        sheet_layout.setContentsMargins(0, 0, 0, 0)
        sheet_layout.addWidget(QLabel("按「确认选择」加载乘区数据"))

        self._total_damage_panel = TotalDamagePanel(self.big_font, self.small_font)
        sheet_layout.addWidget(self._total_damage_panel)

        sheet_scroll = QScrollArea()
        sheet_scroll.setWidgetResizable(True)
        sheet_scroll.setWidget(self._compute_sheet_widget)

        right_wrapper = QWidget()
        right_layout = QVBoxLayout(right_wrapper)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(6)
        right_layout.addWidget(sheet_scroll, stretch=1)

        content_split.addWidget(right_wrapper)
        content_split.setSizes([400, 400])

        self.tabs.addTab(calc_page, "计算页")
        """build calc page。"""

    def _build_adv_page(self) -> None:
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

        adv_page = QWidget()
        adv_layout = QVBoxLayout(adv_page)
        adv_layout.setContentsMargins(0, 0, 0, 0)

        self.control_dock.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        adv_layout.addWidget(self.control_dock, stretch=1)

        self.status_label = QLabel("就绪")
        self.status_label.setFont(self.small_font)
        self.status_label.setStyleSheet("color: #828282; padding: 4px 12px;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        adv_layout.addWidget(self.status_label)

        self.tabs.addTab(adv_page, "高级页")
        """build adv page。"""

    def _on_char_name_change(self) -> None:
        char_data = self.char_panel.get_selected_data()
        if not char_data:
            self.weapon_panel.update_data_list(list(self.all_weapons))
            self._rebuild_segment_rows()
            return
        char_weapon_type = char_data.get("武器", "")
        if not char_weapon_type:
            self.weapon_panel.update_data_list(list(self.all_weapons))
            self._rebuild_segment_rows()
            return
        filtered = [w for w in self.all_weapons if w.get("类型") == char_weapon_type]
        if not filtered:
            self.weapon_panel.update_data_list(list(self.all_weapons))
            self._rebuild_segment_rows()
            return
        self.weapon_panel.update_data_list(filtered)
        self._rebuild_segment_rows()
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

    def _on_calc_mode_changed(self, label: str) -> None:
        self._current_calc_mode = calculation_mode_from_label(label)
        self._on_loadout_changed()
        """on calc mode changed。"""

    def _on_loadout_changed(self) -> None:
        self.status_label.setText("待确认")
        self.confirm_btn.setText("确认选择（待更新）")
        self.confirm_btn.setStyleSheet("""
            QPushButton { background-color: #7C3AED; color: white;
                          border: none; border-radius: 4px;
                          font-size: 14px; font-weight: bold; }
            QPushButton:hover { background-color: #6D28D9; }
            QPushButton:disabled { background-color: #444; color: #888; }
        """)
        self._rebuild_segment_rows()
        self._total_damage_panel.hide_damage()
        """on loadout changed。"""

    def _init_control_dock(self) -> None:
        dock = self.control_dock

        self._confirm_btn_default_style = dock.confirm_btn.styleSheet()

        dock._enemy_panel.enemy_params_changed.connect(self._on_enemy_params_changed)
        initial_params = dock._enemy_panel.get_params()
        self._apply_enemy_params(initial_params)

        self._equipment_catalog: dict[str, list[dict[str, Any]]] = get_equipment_catalog()
        dock.populate_fixed_loadout_slots(self._equipment_catalog)

        self._search_cancel_token = None
        self._search_estimated_total_seconds: float = 0.0

        dock.equipment_scope_combo.currentTextChanged.connect(self._on_equipment_scope_changed)

        dock._enemy_panel.setVisible(False)

        dock._manual_buff_btn.clicked.connect(self._on_manual_buff)
        dock._survival_btn.clicked.connect(self._on_survival_estimate)
        """init control dock。"""

    def _on_equipment_scope_changed(self, scope_label: str) -> None:
        self._equipment_catalog = get_equipment_catalog(scope_label=scope_label)
        self.control_dock.populate_fixed_loadout_slots(self._equipment_catalog)
        self._on_loadout_changed()
        """on equipment scope changed。"""
