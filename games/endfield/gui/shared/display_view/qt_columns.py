#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# SPDX-License-Identifier: AGPL-3.0
"""

PySide6 属性三列无闪渲染。



用 ``QTableWidget`` 替代 CTk 版逐行 ``CTkLabel`` + ``grid`` 的销毁重建模式，

仅更新单元格文本/颜色，彻底消灭闪烁。

"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QFontMetrics
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QWidget,
)

from games.endfield.calc.zone_snapshot.types import ZoneDisplayLine
from games.endfield.gui.app.display_request import DisplayRequest
from games.endfield.gui.presentation.display_lines import (
    build_character_attribute_lines,
    build_weapon_attribute_lines,
    evaluate_display_state,
)


class _ColumnTable(QTableWidget):
    """单列只读表格，作为属性列的基础单元。



    特征：

    - 无表头、无网格线、无交替行色

    - 单元格只读、自动换行

    - 滚动时表头不跟随（已隐藏）

    - 内容变更时不闪（QTableWidget 原生双缓冲）

    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.verticalHeader().hide()

        self.horizontalHeader().hide()

        self.setShowGrid(False)

        self.setAlternatingRowColors(False)

        self.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        self.setSelectionMode(QTableWidget.SelectionMode.NoSelection)

        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        self.horizontalHeader().setStretchLastSection(True)

        self.verticalHeader().setDefaultSectionSize(24)

        self.setWordWrap(True)
        """初始化实例。"""

    def set_lines(
        self,
        lines: list[str],
        default_color: str,
        *,
        zone_data: list[ZoneDisplayLine] | None = None,
    ) -> None:
        """用文本行填充表格（原地更新，不销毁控件）。



        参数:

            lines: 文本行列表

            default_color: 默认文字颜色（如 ``"#B8B8B8"``）

            zone_data: 可选，乘区数据行（优先于 lines）

        """

        if zone_data is not None:
            source = zone_data

        else:
            source = [ZoneDisplayLine(text=t, color=default_color) for t in lines]

        self.setRowCount(len(source))

        self.setColumnCount(1)

        for row, item in enumerate(source):
            cell = QTableWidgetItem(item.text)

            cell.setFlags(cell.flags() & ~Qt.ItemFlag.ItemIsEditable)

            color = QColor(item.color) if item.color.startswith("#") else QColor(default_color)

            cell.setForeground(color)

            self.setItem(row, 0, cell)

        self.resizeColumnToContents(0)

    def set_font(self, font: QFont) -> None:
        """统一设置表格字体。"""

        self.setFont(font)

        row_height = max(24, QFontMetrics(font).height() + 6)

        self.verticalHeader().setDefaultSectionSize(row_height)


class QtAttributeColumns(QWidget):
    """三列属性展示组件（对应 CTk 版 char_attr_scroll / weapon_attr_scroll / right_scroll）。



    用法::



        columns = QtAttributeColumns(big_font=big_font, small_font=small_font)

        columns.refresh(display_request)

    """

    def __init__(
        self,
        big_font: QFont,
        small_font: QFont,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self._big_font = big_font

        self._small_font = small_font

        layout = QHBoxLayout(self)

        layout.setContentsMargins(4, 4, 4, 4)

        layout.setSpacing(8)

        self._char_table = _ColumnTable()

        self._char_table.set_font(small_font)

        self._weapon_table = _ColumnTable()

        self._weapon_table.set_font(small_font)

        self._zone_table = _ColumnTable()

        self._zone_table.set_font(small_font)

        for tbl in (self._char_table, self._weapon_table, self._zone_table):
            tbl.setFrameShape(QFrame.Shape.NoFrame)

            tbl.setStyleSheet("background-color: transparent;")

            layout.addWidget(tbl, stretch=1)

        self._show_empty()
        """初始化实例。"""

    def refresh(self, request: DisplayRequest) -> None:
        """用 DisplayRequest 刷新三列展示。"""

        loadout = request.loadout

        char_data = loadout.char_data

        weapon_data = loadout.weapon_data

        ui_state = evaluate_display_state(char_data, weapon_data)

        s1, s2, s3 = loadout.skill_levels

        if not ui_state["char_message"]:
            char_lines = build_character_attribute_lines(
                char_data,
                loadout.char_level,
                skill_1_level=s1,
                skill_2_level=s2,
                skill_3_level=s3,
            )

            self._char_table.set_lines(char_lines, "#B8B8B8")

        else:
            self._char_table.set_lines([ui_state["char_message"]], "#888888")

        if not ui_state["weapon_message"]:
            weapon_lines = build_weapon_attribute_lines(
                weapon_data,
                loadout.weapon_level,
                **loadout.weapon_skill_kwargs(),
            )

            self._weapon_table.set_lines(weapon_lines, "#4ECDC4")

        else:
            self._weapon_table.set_lines([ui_state["weapon_message"]], "#888888")

        if not ui_state["can_update_zone"]:
            self._zone_table.set_lines(["请选择有效角色和武器"], "#888888")

            return

        zone_lines = self._build_zone_lines(request)

        self._zone_table.set_lines(
            [],
            "#B8B8B8",
            zone_data=[ZoneDisplayLine("=== 乘区数据 ===", "#FF6B6B"), *zone_lines],
        )

    def _build_zone_lines(self, request: DisplayRequest) -> list[ZoneDisplayLine]:
        """从 DisplayRequest 构建乘区展示行。"""
        from .zone_display_builder import build_zone_lines

        return build_zone_lines(request)

    def _show_empty(self) -> None:
        self._char_table.set_lines(["请选择有效角色"], "#888888")

        self._weapon_table.set_lines(["请选择有效武器"], "#888888")

        self._zone_table.set_lines(["请选择有效角色和武器"], "#888888")
        """show empty。"""

    def refresh_from_demo(self) -> None:
        """用演示数据刷新三列（阶段 3 验证用）。"""

        self._char_table.set_lines(
            [
                "角色属性演示",
                "生命: 10000",
                "攻击: 2000",
                "防御: 800",
                "--- 技能段伤害类型 ---",
                "战技 第1段: 物理",
                "连携技 第1段: 物理",
                "战技 等级10 第1段: 300% · 物理",
            ],
            "#B8B8B8",
        )

        self._weapon_table.set_lines(
            [
                "武器属性演示",
                "基础攻击: 900",
                "暴击率: 24%",
                "暴击伤害: 60%",
                "特殊能力: 碎甲",
                "碎甲 等级6: 攻击+15%",
            ],
            "#4ECDC4",
        )

        self._zone_table.set_lines(
            [],
            "#B8B8B8",
            zone_data=[
                ZoneDisplayLine("=== 乘区数据 ===", "#FF6B6B"),
                ZoneDisplayLine("敌方防御减伤: 0.5000", "#4ECDC4"),
                ZoneDisplayLine("力量: 1800.0 (1500.0+300.0)", "#B8B8B8"),
                ZoneDisplayLine("敏捷: 1200.0", "#B8B8B8"),
                ZoneDisplayLine("能力值加成: 0.8500 (力量:1800.0*0.005+敏捷:1200.0*0.002)", "#FFD700"),
                ZoneDisplayLine("基础攻击力: 2900.0 (2000.0+900.0)", "#00D4AA"),
                ZoneDisplayLine("攻击加成攻击力: 1500.0 (2900.0×0.517)", "#9B59B6"),
                ZoneDisplayLine("中间攻击力: 3500.0 (1500.0+2000.0)", "#3498DB"),
                ZoneDisplayLine("最终攻击力: 6475.0 (3500.0×(1+0.8500))", "#E74C3C"),
            ],
        )
