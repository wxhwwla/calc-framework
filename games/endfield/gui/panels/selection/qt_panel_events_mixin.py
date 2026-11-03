#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# SPDX-License-Identifier: AGPL-3.0
"""选择面板级联事件与预设 Mixin（从 QtSelectionPanel 抽离以控制文件长度）。"""

from __future__ import annotations

from typing import Any

from .selection_model import (
    extract_max_level,
    extract_names,
    extract_stars,
    filter_by_star,
    filter_by_type,
    resolve_selected_entity,
)


class QtPanelEventsMixin:
    """负责四级级联、数据刷新与预设按钮。"""

    def _connect_signals(self) -> None:
        self.type_combo.currentIndexChanged.connect(self._on_type_changed)

        self.star_combo.currentIndexChanged.connect(self._on_star_changed)

        self.name_combo.currentIndexChanged.connect(self._on_name_changed)

        self.level_slider.valueChanged.connect(self._on_level_changed)

        self._lvl80_btn.clicked.connect(lambda: self._apply_level_preset(80))

        self._lvl90_btn.clicked.connect(lambda: self._apply_level_preset(90))

        self._skill9_btn.clicked.connect(lambda: self._apply_skill_preset(9))

        self._skill12_btn.clicked.connect(lambda: self._apply_skill_preset(12))

        if not self.is_weapon_panel:
            self._trust4_btn.clicked.connect(self._apply_trust_preset)

        self._max_all_btn.clicked.connect(self._apply_max_preset)

        self._min_all_btn.clicked.connect(self._apply_min_preset)
        """connect signals。"""

    def update_data_list(self, new_data: list[dict[str, Any]]) -> None:
        """动态更新数据列表并重置选择（角色→武器过滤用）。"""

        self.data_list = new_data

        self.type_combo.blockSignals(True)

        self.star_combo.blockSignals(True)

        self.name_combo.blockSignals(True)

        self.type_combo.clear()

        self.star_combo.clear()

        self.name_combo.clear()

        self.type_combo.blockSignals(False)

        self.star_combo.blockSignals(False)

        self.name_combo.blockSignals(False)

        self._init_values()

    def _on_type_changed(self) -> None:
        sel_type = self.type_combo.currentText()

        if not sel_type or sel_type == "无数据":
            self.star_combo.clear()

            return

        filtered = filter_by_type(self.data_list, sel_type)

        stars = extract_stars(filtered)

        self.star_combo.clear()

        self.star_combo.addItems(stars)
        """on type changed。"""

    def _on_star_changed(self) -> None:
        sel_type = self.type_combo.currentText()

        sel_star = self.star_combo.currentText()

        if not sel_type or not sel_star:
            self.name_combo.clear()

            return

        type_filtered = filter_by_type(self.data_list, sel_type)

        filtered = filter_by_star(type_filtered, sel_star)

        names = extract_names(filtered)

        self.name_combo.clear()

        self.name_combo.addItems(names)
        """on star changed。"""

    def _on_name_changed(self) -> None:
        name = self.name_combo.currentText()

        if not name:
            return

        entry = resolve_selected_entity(self.data_list, name)

        if entry:
            max_level = extract_max_level(entry)

            if max_level > 0:
                self.level_slider.setMaximum(max_level)

                current = min(self.level_slider.value(), max_level)

                self.level_slider.setValue(current)

                self.level_label_widget.setText(str(current))

            if self.is_weapon_panel and self.special_panel:
                self.special_panel.refresh(entry)

                self.special_panel.setVisible(True)

            else:
                if self.skill_panel:
                    self.skill_panel.refresh(entry)

                    self.skill_panel.setVisible(True)
        """on name changed。"""

    def _on_level_changed(self, value: int) -> None:
        self.level_label_widget.setText(str(value))
        """on level changed。"""

    def _apply_level_preset(self, target: int) -> None:
        max_lvl = self.level_slider.maximum()

        clamped = max(1, min(target, max_lvl))

        self.level_slider.setValue(clamped)

        self.level_label_widget.setText(str(clamped))
        """apply level preset。"""

    def _apply_skill_preset(self, target: int) -> None:
        if self.is_weapon_panel and self.special_panel:
            self.special_panel.apply_skill_preset(target)

        elif self.skill_panel:
            self.skill_panel.apply_preset(target)
        """apply skill preset。"""

    def _apply_trust_preset(self) -> None:
        if self.trust_panel:
            self.trust_panel.set_level(4)
        """apply trust preset。"""

    def _apply_max_preset(self) -> None:
        self.level_slider.setValue(self.level_slider.maximum())

        self.level_label_widget.setText(str(self.level_slider.maximum()))

        if not self.is_weapon_panel:
            if self.trust_panel:
                self.trust_panel.set_level(4)

            if self.skill_panel:
                self.skill_panel.apply_preset(12)

        else:
            if self.special_panel:
                self.special_panel.apply_skill_preset(9)

                for rd in self.special_panel._special_rows:
                    if rd["row_w"].isVisible() and not rd["stk_slider"].isHidden():
                        rd["stk_slider"].setValue(rd["stk_slider"].maximum())

                        rd["stk_val_lbl"].setText(str(rd["stk_slider"].maximum()))
        """apply max preset。"""

    def _apply_min_preset(self) -> None:
        self.level_slider.setValue(1)

        self.level_label_widget.setText("1")

        if not self.is_weapon_panel:
            if self.trust_panel:
                self.trust_panel.reset()

            if self.skill_panel:
                self.skill_panel.apply_preset(1)

        else:
            if self.special_panel:
                self.special_panel.apply_skill_preset(1)

                for rd in self.special_panel._special_rows:
                    if rd["row_w"].isVisible() and not rd["stk_slider"].isHidden():
                        rd["stk_slider"].setValue(0)

                        rd["stk_val_lbl"].setText("0")
        """apply min preset。"""

    def select_by_name(self, name: str) -> bool:
        """按名称选择角色/武器（触发级联）。"""

        entry = resolve_selected_entity(self.data_list, name)

        if entry:
            item_type = entry.get("类型", "")

            item_star = str(entry.get("星级", ""))

            idx_type = self.type_combo.findText(item_type)

            if idx_type >= 0:
                self.type_combo.setCurrentIndex(idx_type)

            idx_star = self.star_combo.findText(item_star)

            if idx_star >= 0:
                self.star_combo.setCurrentIndex(idx_star)

            idx_name = self.name_combo.findText(name)

            if idx_name >= 0:
                self.name_combo.setCurrentIndex(idx_name)

                return True

        return False
