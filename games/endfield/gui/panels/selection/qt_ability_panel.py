#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""
PySide6 武器特殊能力面板（独立子面板）。

替代 CTk 版 ``SpecialAbilityPanel``（build_mixin + handlers_mixin + refresh_mixin + panel）。
"""

from __future__ import annotations

from typing import Any

from calc_framework.ui.i18n import tr
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

from games.endfield.gui.shared.weapon_data_model import extract_bonus_attributes, read_special_slots

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


def _make_slider(vmin: int, vmax: int, val: int) -> QSlider:
    """创建水平滑块控件。"""
    s = QSlider(Qt.Orientation.Horizontal)
    s.setMinimum(vmin)
    s.setMaximum(vmax)
    s.setValue(val)
    s.setStyleSheet(_SLIDER_STYLE)
    return s


def _make_val_lbl(text: str, font: QFont) -> QLabel:
    """创建数值标签控件。"""
    lbl = QLabel(text)
    lbl.setFont(font)
    lbl.setStyleSheet(_VALUE_STYLE)
    lbl.setFixedWidth(30)
    lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
    return lbl


# ═══════════════════════════════════════════════════════
#  QtSpecialAbilityPanel
# ═══════════════════════════════════════════════════════


class QtSpecialAbilityPanel(QWidget):
    """武器附加属性与特殊能力选择面板。

    最多显示 3 条附加属性（普通技能）+ 2 个特殊能力（特殊一/特殊二），
    每个特殊能力附带可选的层数滑块。
    """

    def __init__(self, font: QFont, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._font = font

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        # 3 条附加属性（普通技能）
        self._normal_rows: list[dict] = []
        for i in range(3):
            rd = self._create_skill_row(
                layout,
                tr("desktop.endfield.abilitySkillN", n=i + 1),
                1,
                9,
                font,
            )
            self._normal_rows.append(rd)

        # 分隔线
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #333333;")
        layout.addWidget(sep)

        # 2 个特殊能力（等级 + 可选层数）
        self._special_rows: list[dict] = []
        for i in range(2):
            rd = self._create_special_row(
                layout,
                tr("desktop.endfield.abilitySpecialN", n=i + 1),
                font,
            )
            self._special_rows.append(rd)

        self._all_hidden()

    # ── 构建辅助 ──────────────────────────────────

    def _create_skill_row(self, layout: QVBoxLayout, title: str, vmin: int, vmax: int, font: QFont) -> dict:
        """创建普通技能行（名称 + 滑块 + 数值）。"""
        name_lbl = QLabel(title)
        name_lbl.setFont(font)
        name_lbl.setStyleSheet(_LABEL_STYLE)
        layout.addWidget(name_lbl)

        row_w = QWidget()
        row_layout = QHBoxLayout(row_w)
        row_layout.setContentsMargins(0, 0, 0, 0)

        val_lbl = _make_val_lbl(str(vmin), font)

        slider = _make_slider(vmin, vmax, vmin)
        slider.valueChanged.connect(lambda v, lb=val_lbl: lb.setText(str(v)))

        row_layout.addWidget(slider, stretch=1)
        row_layout.addWidget(val_lbl)
        layout.addWidget(row_w)

        return {
            "name_lbl": name_lbl,
            "val_lbl": val_lbl,
            "slider": slider,
            "row_w": row_w,
        }

    def _create_special_row(self, layout: QVBoxLayout, title: str, font: QFont) -> dict:
        """创建特殊能力行（名称 + 等级滑块 + 层数滑块）。"""
        name_lbl = QLabel(title)
        name_lbl.setFont(font)
        name_lbl.setStyleSheet(_LABEL_STYLE)
        layout.addWidget(name_lbl)

        row_w = QWidget()
        row_layout = QHBoxLayout(row_w)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(4)

        lvl_val_lbl = _make_val_lbl("1", font)

        lvl_slider = _make_slider(1, 9, 1)
        lvl_slider.valueChanged.connect(lambda v, lb=lvl_val_lbl: lb.setText(str(v)))

        row_layout.addWidget(lvl_slider, stretch=3)
        row_layout.addWidget(lvl_val_lbl)

        stk_lbl = QLabel(tr("desktop.endfield.stackLabel"))
        stk_lbl.setFont(font)
        stk_lbl.setStyleSheet(_LABEL_STYLE)

        stk_val_lbl = _make_val_lbl("0", font)

        stk_slider = _make_slider(0, 1, 0)
        stk_slider.valueChanged.connect(lambda v, lb=stk_val_lbl: lb.setText(str(v)))

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

    def _all_hidden(self) -> None:
        for rd in self._normal_rows:
            rd["name_lbl"].setVisible(False)
            rd["row_w"].setVisible(False)
        for rd in self._special_rows:
            rd["name_lbl"].setVisible(False)
            rd["row_w"].setVisible(False)
        self.setVisible(False)
        """all hidden。"""

    # ── 刷新 ──────────────────────────────────

    def refresh(self, weapon_data: dict[str, Any]) -> None:
        bonus = self._extract_bonus_attributes(weapon_data)

        for i in range(3):
            rd = self._normal_rows[i]
            visible = i < len(bonus) and bool(bonus[i])
            rd["name_lbl"].setVisible(visible)
            rd["row_w"].setVisible(visible)
            if visible:
                ordinal = tr(f"desktop.endfield.abilityOrdinal{i + 1}")
                rd["name_lbl"].setText(tr("desktop.endfield.abilitySkillBonusFmt", ordinal=ordinal, bonus=bonus[i]))
                rd["slider"].setValue(1)
                rd["val_lbl"].setText("1")

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
        """刷新界面状态。"""

    @staticmethod
    def _extract_bonus_attributes(weapon_data: dict[str, Any]) -> list[str]:
        """从武器数据中提取附加属性名称（委托 weapon_data_model）。"""
        return extract_bonus_attributes(weapon_data)

    @staticmethod
    def _read_special_slots(weapon_data: dict[str, Any]) -> list[tuple]:
        """从武器数据中读取特殊能力槽位（委托 weapon_data_model）。"""
        return read_special_slots(weapon_data)

    # ── 对外读取 ──────────────────────────────────

    @property
    def current_special_ability_1_name(self) -> str:
        """当前特殊能力 1 的名称。"""
        if not self._normal_rows[0]["row_w"].isHidden():
            txt = self._normal_rows[0]["name_lbl"].text()
            return txt.split("·", 1)[-1] if "·" in txt else ""
        return ""

    @property
    def current_special_ability_2_name(self) -> str:
        """当前特殊能力 2 的名称。"""
        if not self._normal_rows[1]["row_w"].isHidden():
            txt = self._normal_rows[1]["name_lbl"].text()
            return txt.split("·", 1)[-1] if "·" in txt else ""
        return ""

    @property
    def current_special_ability_3_name(self) -> str:
        """当前特殊能力 3 的名称。"""
        if not self._normal_rows[2]["row_w"].isHidden():
            txt = self._normal_rows[2]["name_lbl"].text()
            return txt.split("·", 1)[-1] if "·" in txt else ""
        return ""

    def get_normal_skill_level(self, idx: int) -> int:
        """获取普通技能等级。"""
        if idx < 0 or idx > 2:
            return 0
        rd = self._normal_rows[idx]
        if not rd["row_w"].isHidden():
            return rd["slider"].value()
        return 0

    def get_special_skill_level(self, idx: int) -> int:
        """获取特殊技能等级。"""
        if idx < 0 or idx > 1:
            return 1
        rd = self._special_rows[idx]
        if not rd["row_w"].isHidden():
            return rd["lvl_slider"].value()
        return 1

    def get_special_skill_stack(self, idx: int) -> int:
        """获取特殊技能层数。"""
        if idx < 0 or idx > 1:
            return 0
        rd = self._special_rows[idx]
        if not rd["row_w"].isHidden() and not rd["stk_slider"].isHidden():
            return rd["stk_slider"].value()
        return 0

    @property
    def current_weapon_special_name(self) -> str:
        """当前武器特殊技能 1 的名称。"""
        rd = self._special_rows[0]
        if not rd["row_w"].isHidden():
            return rd["name_lbl"].text()
        return ""

    @property
    def current_weapon_special_2_name(self) -> str:
        """当前武器特殊技能 2 的名称。"""
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
        """应用skill preset。"""

    def apply_weapon_skill_state(
        self,
        *,
        normal_levels: list[int] | None = None,
        special_states: list[dict[str, int]] | None = None,
    ) -> None:
        """从预设恢复武器附加属性与特殊能力等级/层数。"""
        for i, level in enumerate(normal_levels or []):
            if i >= len(self._normal_rows):
                break
            rd = self._normal_rows[i]
            if rd["row_w"].isVisible():
                clamped = max(1, min(9, int(level)))
                rd["slider"].setValue(clamped)
                rd["val_lbl"].setText(str(clamped))
        for i, state in enumerate(special_states or []):
            if i >= len(self._special_rows):
                break
            rd = self._special_rows[i]
            if not rd["row_w"].isVisible():
                continue
            lvl = max(1, min(9, int(state.get("level", 1))))
            stk = max(0, int(state.get("stack", 0)))
            rd["lvl_slider"].setValue(lvl)
            rd["lvl_val_lbl"].setText(str(lvl))
            if not rd["stk_slider"].isHidden():
                rd["stk_slider"].setValue(stk)
                rd["stk_val_lbl"].setText(str(stk))
