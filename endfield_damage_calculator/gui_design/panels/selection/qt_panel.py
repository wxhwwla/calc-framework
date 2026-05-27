#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PySide6 选择面板：类型/星级/名称/等级四级联动 + 子面板（信赖/技能/特殊能力）。

替代 CTk 版 ``ChooseTypesStarsNamesLevels``（panel.py + cascade.py + state.py + accessors.py 四合一的 mixin）。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from .qt_subpanels import (
    QtSpecialAbilityPanel,
    QtSkillLevelPanel,
    QtTrustPanel,
)


def _empty_list_cb() -> QComboBox:
    cb = QComboBox()
    cb.setStyleSheet(_COMBO_STYLE)
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


class QtSelectionPanel(QWidget):
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
        data_list: List[Dict[str, Any]],
        font: QFont,
        *,
        is_weapon_panel: bool = False,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.data_list: List[Dict[str, Any]] = data_list
        self.is_weapon_panel: bool = is_weapon_panel
        self._font = font

        self.trust_panel: Optional[QtTrustPanel] = None
        self.skill_panel: Optional[QtSkillLevelPanel] = None
        self.special_panel: Optional[QtSpecialAbilityPanel] = None

        self._build_gui()
        self._connect_signals()
        self._init_values()

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

        self._lvl80_btn = QPushButton("80")
        self._lvl90_btn = QPushButton("90")
        self._skill9_btn = QPushButton("9")
        self._skill12_btn = QPushButton("12")

        for btn in (self._lvl80_btn, self._lvl90_btn, self._skill9_btn, self._skill12_btn):
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

    def _add_label(self, layout: QVBoxLayout, text: str, style: str) -> None:
        lbl = QLabel(text)
        lbl.setFont(self._font)
        lbl.setStyleSheet(style)
        layout.addWidget(lbl)

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

    def _init_values(self) -> None:
        types = sorted({item["类型"] for item in self.data_list if "类型" in item})
        if types:
            self.type_combo.addItems(types)
        else:
            self.type_combo.addItem("无数据")

    def _on_type_changed(self) -> None:
        sel_type = self.type_combo.currentText()
        if not sel_type or sel_type == "无数据":
            self.star_combo.clear()
            return
        filtered = [ch for ch in self.data_list if ch.get("类型") == sel_type]
        stars = sorted({str(ch["星级"]) for ch in filtered if "星级" in ch}, key=int)
        self.star_combo.clear()
        self.star_combo.addItems(stars)

    def _on_star_changed(self) -> None:
        sel_type = self.type_combo.currentText()
        sel_star = self.star_combo.currentText()
        if not sel_type or not sel_star:
            self.name_combo.clear()
            return
        filtered = [
            ch for ch in self.data_list
            if ch.get("类型") == sel_type and str(ch.get("星级", "")) == sel_star
        ]
        names = [ch["名称"] for ch in filtered if "名称" in ch]
        self.name_combo.clear()
        self.name_combo.addItems(names)

    def _on_name_changed(self) -> None:
        name = self.name_combo.currentText()
        if not name:
            return
        entry = next((ch for ch in self.data_list if ch.get("名称") == name), None)
        if entry:
            max_level = len(entry.get("等级", []))
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

    def _on_level_changed(self, value: int) -> None:
        self.level_label_widget.setText(str(value))

    def _apply_level_preset(self, target: int) -> None:
        max_lvl = self.level_slider.maximum()
        clamped = max(1, min(target, max_lvl))
        self.level_slider.setValue(clamped)
        self.level_label_widget.setText(str(clamped))

    def _apply_skill_preset(self, target: int) -> None:
        if self.is_weapon_panel and self.special_panel:
            self.special_panel.apply_skill_preset(target)
        elif self.skill_panel:
            self.skill_panel.apply_preset(target)

    # ── 对外读取接口 ──────────────────────────────────

    def get_selected_data(self) -> Optional[Dict[str, Any]]:
        name = self.name_combo.currentText()
        if not name:
            return None
        return next((ch for ch in self.data_list if ch.get("名称") == name), None)

    def get_level(self) -> int:
        return self.level_slider.value()

    def get_skill_1_level(self) -> int:
        if self.skill_panel:
            return self.skill_panel.skill_1_level
        return 0

    def get_skill_2_level(self) -> int:
        if self.skill_panel:
            return self.skill_panel.skill_2_level
        return 0

    def get_skill_3_level(self) -> int:
        if self.skill_panel:
            return self.skill_panel.skill_3_level
        return 0

    def get_trust_level(self) -> int:
        if self.trust_panel:
            return self.trust_panel.trust_level
        return 0

    def get_normal_skill_1_name(self) -> str:
        if self.special_panel:
            return self.special_panel.current_special_ability_1_name
        return ""

    def get_normal_skill_1_level(self) -> int:
        if self.special_panel:
            return self.special_panel.get_normal_skill_level(0)
        return 0

    def get_normal_skill_2_name(self) -> str:
        if self.special_panel:
            return self.special_panel.current_special_ability_2_name
        return ""

    def get_normal_skill_2_level(self) -> int:
        if self.special_panel:
            return self.special_panel.get_normal_skill_level(1)
        return 0

    def get_normal_skill_3_name(self) -> str:
        if self.special_panel:
            return self.special_panel.current_special_ability_3_name
        return ""

    def get_normal_skill_3_level(self) -> int:
        if self.special_panel:
            return self.special_panel.get_normal_skill_level(2)
        return 0

    def get_special_skill_1_name(self) -> str:
        if self.special_panel:
            return self.special_panel.current_weapon_special_name
        return ""

    def get_special_skill_1_level(self) -> int:
        if self.special_panel:
            return self.special_panel.get_special_skill_level(0)
        return 1

    def get_special_skill_1_stack(self) -> int:
        if self.special_panel:
            return self.special_panel.get_special_skill_stack(0)
        return 0

    def get_special_skill_2_name(self) -> str:
        if self.special_panel:
            return self.special_panel.current_weapon_special_2_name
        return ""

    def get_special_skill_2_level(self) -> int:
        if self.special_panel:
            return self.special_panel.get_special_skill_level(1)
        return 1

    def get_special_skill_2_stack(self) -> int:
        if self.special_panel:
            return self.special_panel.get_special_skill_stack(1)
        return 0

    # ── 兼容旧命名 ──────────────────────────────────

    def get_special_ability_1_name(self) -> str:
        return self.get_normal_skill_1_name()

    def get_special_ability_1_level(self) -> int:
        return self.get_normal_skill_1_level()

    def get_special_ability_2_name(self) -> str:
        return self.get_normal_skill_2_name()

    def get_special_ability_2_level(self) -> int:
        return self.get_normal_skill_2_level()

    def get_special_ability_3_name(self) -> str:
        return self.get_normal_skill_3_name()

    def get_special_ability_3_level(self) -> int:
        return self.get_normal_skill_3_level()

    def get_weapon_special_name(self) -> str:
        return self.get_special_skill_1_name()

    def get_weapon_special_level(self) -> int:
        return self.get_special_skill_1_level()

    def get_weapon_special_stack(self) -> int:
        return self.get_special_skill_1_stack()

    def get_weapon_special_2_name(self) -> str:
        return self.get_special_skill_2_name()

    def get_weapon_special_2_level(self) -> int:
        return self.get_special_skill_2_level()

    def get_weapon_special_2_stack(self) -> int:
        return self.get_special_skill_2_stack()
