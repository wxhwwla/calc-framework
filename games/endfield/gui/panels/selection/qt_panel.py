#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# SPDX-License-Identifier: AGPL-3.0
"""

PySide6 选择面板：类型/星级/名称/等级四级联动 + 子面板（信赖/技能/特殊能力）。



替代 CTk 版 ``ChooseTypesStarsNamesLevels``（panel.py + cascade.py + state.py + accessors.py 四合一的 mixin）。

"""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from .qt_ability_panel import QtSpecialAbilityPanel
from .qt_panel_getters_mixin import PanelGettersMixin
from .qt_subpanels import QtSkillLevelPanel, QtTrustPanel
from .selection_model import (
    extract_max_level,
    extract_names,
    extract_stars,
    extract_types,
    filter_by_star,
    filter_by_type,
    resolve_selected_entity,
)


def _empty_list_cb() -> QComboBox:
    cb = QComboBox()

    cb.setStyleSheet(_COMBO_STYLE)

    """empty list cb。"""
    return cb


_COMBO_STYLE = """

    QComboBox {

        background-color: #2B2B2B;

        color: #D1D1D1;

        border: 1px solid #464646;

        border-radius: 4px;

        padding: 4px 8px;

        min-height: 24px;

    }

    QComboBox:hover { border-color: #2B6CB6; }

    QComboBox::drop-down {

        border: none;

        width: 24px;

    }

    QComboBox QAbstractItemView {

        background-color: #2B2B2B;

        color: #D1D1D1;

        selection-background-color: #2B6CB6;

        outline: none;

    }

"""


class QtSelectionPanel(PanelGettersMixin, QWidget):
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

    # ── 控件创建 ──────────────────────────────────────

    def _build_gui(self) -> None:
        layout = QVBoxLayout(self)

        layout.setContentsMargins(0, 0, 0, 0)

        layout.setSpacing(2)

        label_style = "color: #AAAAAA; padding: 2px 0;"

        self._add_label(layout, "类型", label_style)

        self.type_combo = _empty_list_cb()

        self.type_combo.setFont(self._font)

        layout.addWidget(self.type_combo)

        self._add_label(layout, "星级", label_style)

        self.star_combo = _empty_list_cb()

        self.star_combo.setFont(self._font)

        layout.addWidget(self.star_combo)

        name_text = "武器" if self.is_weapon_panel else "角色"

        self._add_label(layout, name_text, label_style)

        self.name_combo = _empty_list_cb()

        self.name_combo.setFont(self._font)

        layout.addWidget(self.name_combo)

        self._add_label(layout, "等级", label_style)

        level_row = QHBoxLayout()

        level_row.setContentsMargins(0, 0, 0, 0)

        self.level_slider = QSlider(Qt.Orientation.Horizontal)

        self.level_slider.setMinimum(1)

        self.level_slider.setMaximum(90)

        self.level_slider.setValue(1)

        self.level_slider.setStyleSheet("""

            QSlider::groove:horizontal {

                background: #3A3A3A; height: 6px; border-radius: 3px;

            }

            QSlider::handle:horizontal {

                background: #2B6CB6; width: 16px; height: 16px;

                margin: -5px 0; border-radius: 8px;

            }

            QSlider::sub-page:horizontal {

                background: #2B6CB6; border-radius: 3px;

            }

        """)

        self.level_label_widget = QLabel("1")

        self.level_label_widget.setFont(self._font)

        self.level_label_widget.setStyleSheet("color: #D1D1D1;")

        self.level_label_widget.setFixedWidth(30)

        self.level_label_widget.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        level_row.addWidget(self.level_slider, stretch=1)

        level_row.addWidget(self.level_label_widget)

        layout.addLayout(level_row)

        # 预设按钮行

        preset_row = QHBoxLayout()

        preset_row.setContentsMargins(0, 0, 0, 0)

        preset_row.setSpacing(4)

        self._lvl80_btn = QPushButton("等级80")

        self._lvl90_btn = QPushButton("等级90")

        self._skill9_btn = QPushButton("技能9")

        self._skill12_btn = QPushButton("技能12")

        preset_btns: list[QPushButton] = [self._lvl80_btn, self._lvl90_btn, self._skill9_btn, self._skill12_btn]

        if not self.is_weapon_panel:
            self._trust4_btn = QPushButton("信赖4")

            preset_btns.append(self._trust4_btn)

        self._max_all_btn = QPushButton("满级")

        self._min_all_btn = QPushButton("归零")

        preset_btns.extend([self._max_all_btn, self._min_all_btn])

        for btn in preset_btns:
            btn.setFont(self._font)

            btn.setStyleSheet("""

                QPushButton {

                    background-color: #333333; color: #D1D1D1;

                    border: 1px solid #464646; border-radius: 4px;

                    padding: 2px 8px; min-height: 22px;

                }

                QPushButton:hover { background-color: #2B6CB6; border-color: #2B6CB6; }

            """)

            preset_row.addWidget(btn)

        preset_row.addStretch()

        layout.addLayout(preset_row)

        # 子面板：角色侧（信赖 + 技能等级） / 武器侧（特殊能力）

        if not self.is_weapon_panel:
            self.trust_panel = QtTrustPanel(self._font, parent=self)

            layout.addWidget(self.trust_panel)

            self.skill_panel = QtSkillLevelPanel(self._font, parent=self)

            self.skill_panel.setVisible(False)

            layout.addWidget(self.skill_panel)

        else:
            self.special_panel = QtSpecialAbilityPanel(self._font, parent=self)

            self.special_panel.setVisible(False)

            layout.addWidget(self.special_panel)
        """build gui。"""

    def _add_label(self, layout: QVBoxLayout, text: str, style: str) -> None:
        lbl = QLabel(text)

        lbl.setFont(self._font)

        lbl.setStyleSheet(style)

        layout.addWidget(lbl)
        """add label。"""

    # ── 级联信号 ──────────────────────────────────────

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

    def _init_values(self) -> None:
        types = extract_types(self.data_list)

        if types:
            self.type_combo.addItems(types)

        else:
            self.type_combo.addItem("无数据")
        """init values。"""

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
