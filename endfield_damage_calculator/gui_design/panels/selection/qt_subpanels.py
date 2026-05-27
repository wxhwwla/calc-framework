#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PySide6 选择面板子组件：信赖等级 / 技能等级 / 特殊能力。

替代 CTk 版 ``TrustPanel`` / ``SkillLevelPanel`` / ``SpecialAbilityPanel``。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QSlider,
    QVBoxLayout,
    QWidget,
)


_SLIDER_STYLE = """
    QSlider::groove:horizontal {
        background: #3A3A3A; height: 6px; border-radius: 3px;
    }
    QSlider::handle:horizontal {
        background: #2B6CB6; width: 14px; height: 14px;
        margin: -4px 0; border-radius: 7px;
    }
    QSlider::sub-page:horizontal { background: #2B6CB6; border-radius: 3px; }
"""

_LABEL_STYLE = "color: #AAAAAA; padding: 2px 0;"
_VALUE_STYLE = "color: #D1D1D1;"


def _make_row(parent: QWidget, label_text: str, slider_min: int, slider_max: int,
              slider_val: int, font: QFont) -> tuple[QLabel, QSlider]:
    """创建一行 标签 + 滑块 + 数值 水平布局。

    返回 (value_label, slider)。
    """
    row = QHBoxLayout()
    row.setContentsMargins(0, 0, 0, 0)

    val_lbl = QLabel(str(slider_val))
    val_lbl.setFont(font)
    val_lbl.setStyleSheet(_VALUE_STYLE)
    val_lbl.setFixedWidth(30)
    val_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

    slider = QSlider(Qt.Orientation.Horizontal)
    slider.setMinimum(slider_min)
    slider.setMaximum(slider_max)
    slider.setValue(slider_val)
    slider.setStyleSheet(_SLIDER_STYLE)

    row.addWidget(slider, stretch=1)
    row.addWidget(val_lbl)

    return val_lbl, slider


# ═══════════════════════════════════════════════════════
#  1. 信赖等级
# ═══════════════════════════════════════════════════════

class QtTrustPanel(QWidget):
    """角色信赖等级滑块（0-4 级）。"""

    def __init__(self, font: QFont, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._font = font
        self._level = 0

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        lbl = QLabel("信赖")
        lbl.setFont(font)
        lbl.setStyleSheet(_LABEL_STYLE)
        layout.addWidget(lbl)

        self._val_lbl, self._slider = _make_row(self, "信赖", 0, 4, 0, font)
        self._slider.valueChanged.connect(self._on_change)
        layout.addLayout(self._make_row_container())

    def _make_row_container(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.addWidget(self._slider, stretch=1)
        row.addWidget(self._val_lbl)
        return row

    def _on_change(self, value: int) -> None:
        self._level = value
        self._val_lbl.setText(str(value))

    @property
    def trust_level(self) -> int:
        return self._level

    def reset(self) -> None:
        self._level = 0
        self._slider.setValue(0)
        self._val_lbl.setText("0")


# ═══════════════════════════════════════════════════════
#  2. 技能等级（战技/连携/终结）
# ═══════════════════════════════════════════════════════

class QtSkillLevelPanel(QWidget):
    """角色战技/连携/终结技等级滑块（1-12 级）。"""

    def __init__(self, font: QFont, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._font = font
        self._visible = False

        self._names: list[str] = ["战技", "连携技", "终结技"]
        self._levels: list[int] = [1, 1, 1]
        self._has_data: list[bool] = [True, True, True]
        self._sliders: list[QSlider] = []
        self._value_labels: list[QLabel] = []
        self._name_labels: list[QLabel] = []
        self._rows: list[QWidget] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        for i, name in enumerate(self._names):
            name_lbl = QLabel(name)
            name_lbl.setFont(font)
            name_lbl.setStyleSheet(_LABEL_STYLE)
            layout.addWidget(name_lbl)
            self._name_labels.append(name_lbl)

            row_w = QWidget()
            row_layout = QHBoxLayout(row_w)
            row_layout.setContentsMargins(0, 0, 0, 0)

            val_lbl = QLabel("1")
            val_lbl.setFont(font)
            val_lbl.setStyleSheet(_VALUE_STYLE)
            val_lbl.setFixedWidth(30)
            val_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

            slider = QSlider(Qt.Orientation.Horizontal)
            slider.setMinimum(1)
            slider.setMaximum(12)
            slider.setValue(1)
            slider.setStyleSheet(_SLIDER_STYLE)
            slider.valueChanged.connect(lambda v, idx=i: self._on_skill_change(idx, v))

            row_layout.addWidget(slider, stretch=1)
            row_layout.addWidget(val_lbl)
            layout.addWidget(row_w)

            self._sliders.append(slider)
            self._value_labels.append(val_lbl)
            self._rows.append(row_w)

    def _on_skill_change(self, idx: int, value: int) -> None:
        self._levels[idx] = value
        self._value_labels[idx].setText(str(value))

    def refresh(self, char_data: Dict[str, Any]) -> None:
        skill_keys = ["战技倍率", "连携技倍率", "终结技倍率"]
        for i, key in enumerate(skill_keys):
            data = char_data.get(key, [])
            has_data = len(data) >= 1
            self._has_data[i] = has_data
            self._name_labels[i].setVisible(has_data)
            self._rows[i].setVisible(has_data)
            if has_data:
                self._levels[i] = 1
                self._sliders[i].setValue(1)
                self._value_labels[i].setText("1")
        self._visible = any(self._has_data)

    def show_panel(self) -> None:
        self.setVisible(True)

    def hide_panel(self) -> None:
        self.setVisible(False)

    @property
    def skill_1_level(self) -> int:
        return self._levels[0]

    @property
    def skill_2_level(self) -> int:
        return self._levels[1]

    @property
    def skill_3_level(self) -> int:
        return self._levels[2]

    def apply_preset(self, level: int) -> None:
        clamped = max(1, min(level, 12))
        for i in range(3):
            if self._has_data[i]:
                self._sliders[i].setValue(clamped)
                self._levels[i] = clamped
                self._value_labels[i].setText(str(clamped))

    def apply_levels(self, s1: int, s2: int, s3: int) -> None:
        for idx, val in enumerate([s1, s2, s3]):
            if self._has_data[idx]:
                self._sliders[idx].setValue(val)
                self._levels[idx] = val
                self._value_labels[idx].setText(str(val))


# ═══════════════════════════════════════════════════════
#  3. 武器特殊能力（附加属性 + 特殊技能）
# ═══════════════════════════════════════════════════════

class QtSpecialAbilityPanel(QWidget):
    """武器附加属性与特殊能力选择面板。

    最多显示 3 条附加属性（第一/第二/第三技能）+ 2 个特殊能力（特殊一/特殊二），
    每个特殊能力附带可选的层数滑块。
    """

    def __init__(self, font: QFont, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._font = font
        self._rows: list[dict] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        # 3 条附加属性行
        self._normal_rows: list[dict] = []
        for i in range(3):
            rd = self._create_skill_row(layout, f"技能{i+1}", 1, 9, font)
            self._normal_rows.append(rd)

        # 分隔线
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #333333;")
        layout.addWidget(sep)

        # 2 个特殊能力（每个带等级 + 可选层数）
        self._special_rows: list[dict] = []
        for i in range(2):
            rd = self._create_special_row(layout, f"特殊{i+1}", font)
            self._special_rows.append(rd)

        self._all_hidden()

    @staticmethod
    def _create_skill_row(layout: QVBoxLayout, title: str, vmin: int, vmax: int,
                          font: QFont) -> dict:
        """创建一行附加属性：名称标签 + 滑块 + 数值。"""
        name_lbl = QLabel(title)
        name_lbl.setFont(font)
        name_lbl.setStyleSheet(_LABEL_STYLE)
        layout.addWidget(name_lbl)

        row_w = QWidget()
        row_layout = QHBoxLayout(row_w)
        row_layout.setContentsMargins(0, 0, 0, 0)

        val_lbl = QLabel("1")
        val_lbl.setFont(font)
        val_lbl.setStyleSheet(_VALUE_STYLE)
        val_lbl.setFixedWidth(30)
        val_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setMinimum(vmin)
        slider.setMaximum(vmax)
        slider.setValue(vmin)
        slider.setStyleSheet(_SLIDER_STYLE)

        row_layout.addWidget(slider, stretch=1)
        row_layout.addWidget(val_lbl)
        layout.addWidget(row_w)

        return {
            "name_lbl": name_lbl,
            "val_lbl": val_lbl,
            "slider": slider,
            "row_w": row_w,
            "level": vmin,
        }

    @staticmethod
    def _create_special_row(layout: QVBoxLayout, title: str, font: QFont) -> dict:
        """创建一行特殊能力：名称 + 等级滑块 + 层数滑块。"""
        name_lbl = QLabel(title)
        name_lbl.setFont(font)
        name_lbl.setStyleSheet(_LABEL_STYLE)
        layout.addWidget(name_lbl)

        row_w = QWidget()
        row_layout = QHBoxLayout(row_w)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(4)

        # 等级
        lvl_val_lbl = QLabel("1")
        lvl_val_lbl.setFont(font)
        lvl_val_lbl.setStyleSheet(_VALUE_STYLE)
        lvl_val_lbl.setFixedWidth(24)
        lvl_val_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        lvl_slider = QSlider(Qt.Orientation.Horizontal)
        lvl_slider.setMinimum(1)
        lvl_slider.setMaximum(9)
        lvl_slider.setValue(1)
        lvl_slider.setStyleSheet(_SLIDER_STYLE)

        row_layout.addWidget(lvl_slider, stretch=3)
        row_layout.addWidget(lvl_val_lbl)

        # 层数
        stk_lbl = QLabel("层")
        stk_lbl.setFont(font)
        stk_lbl.setStyleSheet(_LABEL_STYLE)

        stk_val_lbl = QLabel("0")
        stk_val_lbl.setFont(font)
        stk_val_lbl.setStyleSheet(_VALUE_STYLE)
        stk_val_lbl.setFixedWidth(24)
        stk_val_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        stk_slider = QSlider(Qt.Orientation.Horizontal)
        stk_slider.setMinimum(0)
        stk_slider.setMaximum(1)
        stk_slider.setValue(0)
        stk_slider.setStyleSheet(_SLIDER_STYLE)

        row_layout.addWidget(stk_lbl)
        row_layout.addWidget(stk_slider, stretch=2)
        row_layout.addWidget(stk_val_lbl)

        layout.addWidget(row_w)

        return {
            "name_lbl": name_lbl,
            "lvl_val_lbl": lvl_val_lbl,
            "lvl_slider": lvl_slider,
            "stk_lbl": stk_lbl,
            "stk_val_lbl": stk_val_lbl,
            "stk_slider": stk_slider,
            "row_w": row_w,
        }

    def refresh(self, weapon_data: Dict[str, Any]) -> None:
        """根据武器数据刷新面板显示。"""
        bonus = self._extract_bonus_attributes(weapon_data)

        for i in range(3):
            rd = self._normal_rows[i]
            visible = i < len(bonus) and bool(bonus[i])
            rd["name_lbl"].setVisible(visible)
            rd["row_w"].setVisible(visible)
            if visible:
                rd["name_lbl"].setText(f"{['第一', '第二', '第三'][i]}技能·{bonus[i]}")

        special_slots = self._read_special_slots(weapon_data)
        for i in range(2):
            rd = self._special_rows[i]
            if i < len(special_slots):
                available, name, _, max_stack = special_slots[i]
                rd["name_lbl"].setVisible(available)
                rd["row_w"].setVisible(available)
                if available:
                    rd["name_lbl"].setText(name)
                    rd["lvl_slider"].setValue(1)
                    rd["lvl_val_lbl"].setText("1")
                    if max_stack > 1:
                        rd["stk_slider"].setMaximum(max_stack)
                        rd["stk_slider"].setValue(0)
                        rd["stk_val_lbl"].setText("0")
                        rd["stk_lbl"].setVisible(True)
                        rd["stk_slider"].setVisible(True)
                        rd["stk_val_lbl"].setVisible(True)
                    else:
                        rd["stk_lbl"].setVisible(False)
                        rd["stk_slider"].setVisible(False)
                        rd["stk_val_lbl"].setVisible(False)
            else:
                rd["name_lbl"].setVisible(False)
                rd["row_w"].setVisible(False)

        self.setVisible(True)

    @staticmethod
    def _extract_bonus_attributes(weapon_data: Dict[str, Any]) -> list[str]:
        """从 normal_skills 或旧式 xxx+ 字段中提取最多 3 条附加属性名。"""
        normal_raw = weapon_data.get("normal_skills")
        if isinstance(normal_raw, list):
            out: list[str] = []
            for item in normal_raw:
                if not isinstance(item, dict):
                    continue
                effect = str(item.get("effect", "")).strip()
                if effect:
                    out.append(effect)
            return out[:3]

        keys = list(weapon_data.keys())
        try:
            start = keys.index("基础攻击力") + 1
        except ValueError:
            return []
        special_keys = frozenset({"特殊能力", "特殊能力1", "特殊能力2"})
        out = []
        for key in keys[start:]:
            if key in special_keys:
                break
            if key.endswith("+") and isinstance(weapon_data.get(key), list):
                out.append(key)
        return out[:3]

    @staticmethod
    def _read_special_slots(weapon_data: Dict[str, Any]) -> list[tuple]:
        """返回 [(available, name, level, max_stack), ...] 最多 2 项。"""
        special_raw = weapon_data.get("special_skills")
        if isinstance(special_raw, list):
            slots: list[tuple] = []
            for idx in range(2):
                if idx < len(special_raw) and isinstance(special_raw[idx], dict):
                    item = special_raw[idx]
                    name = str(item.get("name", "")).strip()
                    effect = str(item.get("effect", "")).strip()
                    curve = item.get("curve")
                    max_stack = max(1, int(item.get("max_stack", 1)))
                    display_name = name or effect
                    available = bool(display_name) and isinstance(curve, list) and len(curve) > 0
                    slots.append((available, display_name, 1, max_stack))
                else:
                    slots.append((False, "", 1, 1))
            return slots

        result: list[tuple] = []
        for key in ("特殊能力1", "特殊能力2"):
            entry = weapon_data.get(key, {})
            if isinstance(entry, dict):
                name = entry.get("名称", "")
                available = bool(name) and name != "无"
                max_stack = int(entry.get("最多叠加层数", 1))
                result.append((available, name, 1, max_stack))
            else:
                result.append((False, "", 1, 1))
        return result

    def _all_hidden(self) -> None:
        for rd in self._normal_rows:
            rd["name_lbl"].setVisible(False)
            rd["row_w"].setVisible(False)
        for rd in self._special_rows:
            rd["name_lbl"].setVisible(False)
            rd["row_w"].setVisible(False)
        self.setVisible(False)

    def show_panel(self) -> None:
        self.setVisible(True)

    def hide_panel(self) -> None:
        self._all_hidden()

    # ── 对外读取 ──────────────────────────────────

    @property
    def _ability_1_slider(self):
        if not self._normal_rows[0]["row_w"].isHidden():
            return self._normal_rows[0]["slider"]
        return None

    @property
    def current_special_ability_1_name(self) -> str:
        if not self._normal_rows[0]["row_w"].isHidden():
            txt = self._normal_rows[0]["name_lbl"].text()
            return txt.split("·", 1)[-1] if "·" in txt else ""
        return ""

    @property
    def current_special_ability_2_name(self) -> str:
        if not self._normal_rows[1]["row_w"].isHidden():
            txt = self._normal_rows[1]["name_lbl"].text()
            return txt.split("·", 1)[-1] if "·" in txt else ""
        return ""

    @property
    def current_special_ability_3_name(self) -> str:
        if not self._normal_rows[2]["row_w"].isHidden():
            txt = self._normal_rows[2]["name_lbl"].text()
            return txt.split("·", 1)[-1] if "·" in txt else ""
        return ""

    def get_normal_skill_level(self, idx: int) -> int:
        if idx < 0 or idx > 2:
            return 0
        rd = self._normal_rows[idx]
        if not rd["row_w"].isHidden():
            return rd["slider"].value()
        return 0

    def get_special_skill_level(self, idx: int) -> int:
        if idx < 0 or idx > 1:
            return 1
        rd = self._special_rows[idx]
        if not rd["row_w"].isHidden():
            return rd["lvl_slider"].value()
        return 1

    def get_special_skill_stack(self, idx: int) -> int:
        if idx < 0 or idx > 1:
            return 0
        rd = self._special_rows[idx]
        if not rd["row_w"].isHidden() and not rd["stk_slider"].isHidden():
            return rd["stk_slider"].value()
        return 0

    @property
    def current_weapon_special_name(self) -> str:
        rd = self._special_rows[0]
        if not rd["row_w"].isHidden():
            return rd["name_lbl"].text()
        return ""

    @property
    def current_weapon_special_2_name(self) -> str:
        rd = self._special_rows[1]
        if not rd["row_w"].isHidden():
            return rd["name_lbl"].text()
        return ""

    def apply_skill_preset(self, level: int) -> None:
        clamped = max(1, min(level, 9))
        for rd in self._normal_rows:
            if rd["row_w"].isVisible():
                rd["slider"].setValue(clamped)
                rd["val_lbl"].setText(str(clamped))
        for rd in self._special_rows:
            if rd["row_w"].isVisible():
                rd["lvl_slider"].setValue(clamped)
                rd["lvl_val_lbl"].setText(str(clamped))
