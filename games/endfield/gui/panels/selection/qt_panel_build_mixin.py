#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# SPDX-License-Identifier: AGPL-3.0
"""选择面板控件构建 Mixin（从 QtSelectionPanel 抽离以控制文件长度）。"""

from __future__ import annotations

from calc_framework.ui.i18n import tr
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QVBoxLayout,
)

from .qt_ability_panel import QtSpecialAbilityPanel
from .qt_subpanels import QtSkillLevelPanel, QtTrustPanel
from .selection_model import extract_types


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


class QtPanelBuildMixin:
    """负责创建选择面板的控件与初始选项。"""

    def _build_gui(self) -> None:
        layout = QVBoxLayout(self)  # pyright: ignore[reportArgumentType]

        layout.setContentsMargins(0, 0, 0, 0)

        layout.setSpacing(2)

        label_style = "color: #AAAAAA; padding: 2px 0;"

        self._add_label(layout, tr("desktop.endfield.selectionType"), label_style)

        self.type_combo = _empty_list_cb()

        self.type_combo.setFont(self._font)

        layout.addWidget(self.type_combo)

        self._add_label(layout, tr("desktop.endfield.selectionStar"), label_style)

        self.star_combo = _empty_list_cb()

        self.star_combo.setFont(self._font)

        layout.addWidget(self.star_combo)

        name_text = (
            tr("desktop.endfield.selectionWeapon")
            if self.is_weapon_panel
            else tr("desktop.endfield.selectionCharacter")
        )

        self._add_label(layout, name_text, label_style)

        self.name_combo = _empty_list_cb()

        self.name_combo.setFont(self._font)

        layout.addWidget(self.name_combo)

        self._add_label(layout, tr("desktop.endfield.selectionLevel"), label_style)

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

        self._lvl80_btn = QPushButton(tr("desktop.endfield.presetLevel80"))

        self._lvl90_btn = QPushButton(tr("desktop.endfield.presetLevel90"))

        self._skill9_btn = QPushButton(tr("desktop.endfield.presetSkill9"))

        self._skill12_btn = QPushButton(tr("desktop.endfield.presetSkill12"))

        preset_btns: list[QPushButton] = [self._lvl80_btn, self._lvl90_btn, self._skill9_btn, self._skill12_btn]

        if not self.is_weapon_panel:
            self._trust4_btn = QPushButton(tr("desktop.endfield.presetTrust4"))

            preset_btns.append(self._trust4_btn)

        self._max_all_btn = QPushButton(tr("desktop.endfield.presetMaxAll"))

        self._min_all_btn = QPushButton(tr("desktop.endfield.presetMinAll"))

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
            self.trust_panel = QtTrustPanel(self._font, parent=self)  # pyright: ignore[reportArgumentType]

            layout.addWidget(self.trust_panel)

            self.skill_panel = QtSkillLevelPanel(self._font, parent=self)  # pyright: ignore[reportArgumentType]

            self.skill_panel.setVisible(False)

            layout.addWidget(self.skill_panel)

        else:
            self.special_panel = QtSpecialAbilityPanel(self._font, parent=self)  # pyright: ignore[reportArgumentType]

            self.special_panel.setVisible(False)

            layout.addWidget(self.special_panel)
        """build gui。"""

    def _add_label(self, layout: QVBoxLayout, text: str, style: str) -> None:
        lbl = QLabel(text)

        lbl.setFont(self._font)

        lbl.setStyleSheet(style)

        layout.addWidget(lbl)
        """add label。"""

    def _init_values(self) -> None:
        types = extract_types(self.data_list)

        if types:
            self.type_combo.addItems(types)

        else:
            self.type_combo.addItem(tr("desktop.endfield.selectionNoData"))
        """init values。"""
