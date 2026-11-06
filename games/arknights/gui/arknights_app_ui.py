# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""ArknightsAppUIMixin — 明日方舟主窗口的统一 Shell 布局。

采用共享 ``CalculatorShell``：

- 顶部工具条：使用说明、自愿捐赠等与计算无关的入口。
- 计算页 2×2：干员选择 | 技能选择 / 干员基础数据 | 技能加成数据。
- 乘区明细页 2×2：敌人参数 | 额外加成 / 乘区明细 | 最终伤害。
- 底部固定确认按钮与页签；选择/输入变更只标记待确认。
"""

from __future__ import annotations

from typing import cast

from calc_framework.ui.calculator_shell import CalculatorPage, CalculatorShell
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QSlider,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from games.arknights.gui.arknights_compute_sheet import (
    create_arknights_compute_sheet,
    ensure_arknights_adapter,
    layout_for_damage_app,
)
from games.arknights.operator_catalog import STAR_TIERS, list_professions
from utils.gui.donation import open_donation_dialog
from utils.gui.help_dialog import HelpDialog
from utils.gui.help_loader import load_multi_category


def _scrollable(widget: QWidget) -> QScrollArea:
    """把内容包进滚动区，避免固定 2×2 区域被长面板撑破。"""
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QFrame.Shape.NoFrame)
    scroll.setWidget(widget)
    return scroll


def _new_kv_table(headers: list[str]) -> QTableWidget:
    """创建只读的两列表格。"""
    table = QTableWidget()
    table.setColumnCount(len(headers))
    table.setHorizontalHeaderLabels(headers)
    table.horizontalHeader().setStretchLastSection(True)
    table.verticalHeader().setVisible(False)
    table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    return table


class ArknightsAppUIMixin:
    """菜单入口、共享外壳与 2×2 页面构建。"""

    # ── 帮助 / 捐赠 ────────────────────────────

    def _open_help(self) -> None:
        """打开使用说明帮助对话框。"""
        sections = load_multi_category({"完整说明书": ["GUI ⑪：明日方舟计算器", "数据结构与文件格式"]})
        dlg = HelpDialog(
            build_tree=lambda: sections,
            parent=cast(QMainWindow, self),
            title="明日方舟计算器 — 使用说明",
        )
        dlg.exec()

    def _open_donation(self) -> None:
        """打开捐赠对话框。"""
        open_donation_dialog(cast(QMainWindow, self))

    # ── 共享外壳 ──────────────────────────────

    def _init_shell(self) -> None:
        """创建顶部工具条 + 页面栈 + 底部确认/页签。"""
        self._shell = CalculatorShell(cast(QWidget, self))
        cast(QMainWindow, self).setCentralWidget(self._shell)
        self.status_label = self._shell.status_label
        self._shell.confirmed.connect(self._on_compute)
        self._shell.set_status("就绪")
        self._build_toolbar()

    def _build_toolbar(self) -> None:
        """把所有与计算无关的入口收进顶部工具条。"""
        self._shell.add_tool_action("使用说明", self._open_help, shortcut="F1")
        self._shell.add_tool_action("自愿捐赠", self._open_donation)

    def _setup_ui(self) -> None:
        """构建共享外壳与两个 2×2 页面。"""
        self._init_shell()
        self._build_calc_page()
        self._build_breakdown_page()
        self._on_op_selected(self._op_combo.currentText())

    def _build_calc_page(self) -> None:
        """计算页：干员选择 | 技能选择 / 干员基础 | 技能加成。"""
        self._bonus_table = _new_kv_table(["加成项", "数值"])

        page = CalculatorPage(
            top_left_title="干员选择",
            top_right_title="技能选择",
            bottom_left_title="干员基础数据",
            bottom_right_title="技能加成数据",
        )
        page.zone("top_left").add_widget(_scrollable(self._build_left()))
        page.zone("top_right").add_widget(_scrollable(self._build_right()))
        page.zone("bottom_left").add_widget(_scrollable(self._build_detail_panel()))
        page.zone("bottom_right").add_widget(self._bonus_table)

        self._calc_page = page
        self._shell.add_page("计算", page)

    def _build_breakdown_page(self) -> None:
        """乘区明细页：敌人参数 | 额外加成 / 乘区明细 | 最终伤害。"""
        pkg, full_layout = ensure_arknights_adapter()
        param_layout = layout_for_damage_app(full_layout)
        self._param_sheet = create_arknights_compute_sheet(
            pkg.dag_service,
            param_layout,
            parent=cast(QWidget, self),
        )
        sections = {sec.id: sec for sec in param_layout.sections}

        enemy_widget = self._param_sheet.build_section_widget(sections["enemy"])
        assert enemy_widget is not None
        self._enemy_section_widget = enemy_widget

        extra_widget = QWidget()
        extra_layout = QVBoxLayout(extra_widget)
        extra_layout.setContentsMargins(0, 0, 0, 0)
        extra_layout.setSpacing(6)
        pct_widget = self._param_sheet.build_section_widget(sections["extra_pct_bonus"])
        bonus_widget = self._param_sheet.build_section_widget(sections["extra_bonuses"])
        assert pct_widget is not None and bonus_widget is not None
        extra_layout.addWidget(pct_widget)
        extra_layout.addWidget(bonus_widget)
        extra_layout.addStretch()
        self._extra_bonus_widget = extra_widget

        self._result_table = _new_kv_table(["乘区/指标", "数值"])

        page = CalculatorPage(
            top_left_title="敌人参数",
            top_right_title="额外加成",
            bottom_left_title="乘区明细",
            bottom_right_title="最终伤害",
        )
        page.zone("top_left").add_widget(_scrollable(self._enemy_section_widget))
        page.zone("top_right").add_widget(_scrollable(self._extra_bonus_widget))
        page.zone("bottom_left").add_widget(self._result_table)
        page.zone("bottom_right").add_widget(_scrollable(self._build_result_panel()))

        self._breakdown_page = page
        self._shell.add_page("乘区明细", page)

        self._param_sheet.value_changed.connect(self._on_sheet_value_changed)

    # ── 计算页：左上（干员选择） ────────────────

    def _build_left(self) -> QWidget:
        """构建左上角：筛选、干员选择与基本信息。"""
        w = QWidget()
        lo = QVBoxLayout(w)
        lo.setContentsMargins(0, 0, 0, 0)
        lo.setSpacing(8)

        g_filter = QGroupBox("筛选")
        fl = QVBoxLayout(g_filter)
        stars_row = QHBoxLayout()
        self._star_checks: dict[int, QCheckBox] = {}
        for star in STAR_TIERS:
            cb = QCheckBox(f"{star}★")
            cb.setChecked(True)
            cb.toggled.connect(self._on_filter_changed)
            self._star_checks[star] = cb
            stars_row.addWidget(cb)
        fl.addLayout(stars_row)

        prof_row = QHBoxLayout()
        prof_row.addWidget(QLabel("主职业"))
        self._prof_combo = QComboBox()
        self._prof_combo.addItem("全部", "")
        for p in list_professions(self._operator_index):
            self._prof_combo.addItem(p, p)
        self._prof_combo.currentIndexChanged.connect(self._on_profession_changed)
        prof_row.addWidget(self._prof_combo, 1)
        fl.addLayout(prof_row)

        branch_row = QHBoxLayout()
        branch_row.addWidget(QLabel("分支"))
        self._branch_combo = QComboBox()
        self._branch_combo.addItem("全部", "")
        self._branch_combo.currentIndexChanged.connect(self._on_filter_changed)
        branch_row.addWidget(self._branch_combo, 1)
        fl.addLayout(branch_row)
        lo.addWidget(g_filter)

        g_op = QGroupBox("干员")
        gl = QVBoxLayout(g_op)
        self._op_combo = QComboBox()
        self._op_combo.setEditable(True)
        self._op_combo.setPlaceholderText("搜索干员...")
        self._op_combo.currentTextChanged.connect(self._on_op_selected)
        gl.addWidget(self._op_combo)

        total = len(self._operator_index)
        self._op_count_label = QLabel(f"显示 {total} / {total} 个干员")
        self._op_count_label.setStyleSheet("color: #666; font-size: 11px;")
        gl.addWidget(self._op_count_label)
        lo.addWidget(g_op)
        self._refresh_branch_combo()
        self._refresh_operator_combo()

        g_info = QGroupBox("基本信息")
        il = QVBoxLayout(g_info)
        self._det_name = QLabel("")
        self._det_name.setStyleSheet("font-size: 18px; font-weight: bold; color: #E0E0E0;")
        il.addWidget(self._det_name)
        self._det_info = QLabel("")
        self._det_info.setStyleSheet("color: #888; font-size: 12px;")
        il.addWidget(self._det_info)
        self._det_trait = QLabel("")
        self._det_trait.setWordWrap(True)
        self._det_trait.setStyleSheet("color: #B0B0B0; font-style: italic; padding: 4px 0;")
        il.addWidget(self._det_trait)
        lo.addWidget(g_info)
        lo.addStretch()
        return w

    # ── 计算页：右上（技能选择） ────────────────

    def _build_right(self) -> QWidget:
        """构建右上角：技能、技能等级与技能参数。"""
        w = QWidget()
        lo = QVBoxLayout(w)
        lo.setContentsMargins(0, 0, 0, 0)
        lo.setSpacing(8)

        g_sk = QGroupBox("技能")
        sl = QVBoxLayout(g_sk)
        self._skill_combo = QComboBox()
        self._skill_combo.addItems(["普攻", "技能1", "技能2", "技能3"])
        self._skill_combo.currentIndexChanged.connect(self._on_skill_changed)
        sl.addWidget(self._skill_combo)

        level_row = QHBoxLayout()
        level_row.addWidget(QLabel("技能等级:"))
        self._lvl_slider = QSlider(Qt.Orientation.Horizontal)
        self._lvl_slider.setRange(1, 10)
        self._lvl_slider.setValue(7)
        self._lvl_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self._lvl_slider.setTickInterval(1)
        self._lvl_slider.valueChanged.connect(self._on_level_changed)
        level_row.addWidget(self._lvl_slider, 1)
        self._lvl_label = QLabel("Lv.7")
        self._lvl_label.setStyleSheet("color: #2B6CB6; font-weight: bold;")
        level_row.addWidget(self._lvl_label)
        sl.addLayout(level_row)

        chip_row = QGridLayout()
        chip_row.setHorizontalSpacing(4)
        chip_row.setVerticalSpacing(4)
        self._lvl_chip_btns: list[QPushButton] = []
        for lv in range(1, 11):
            chip_label = f"Lv.{lv}" if lv <= 7 else f"专{lv - 7}"
            chip = QPushButton(chip_label)
            chip.setCheckable(True)
            chip.setFixedHeight(24)
            # 全局按钮样式有 8×24 内边距，单行 10 个等级按钮会撑出横向滚动条；
            # 这里压缩内边距并排成 5×2。
            chip.setStyleSheet(
                "QPushButton { padding: 1px 6px; min-height: 18px; font-size: 11px; font-weight: normal; }"
            )
            chip.clicked.connect(lambda _checked=False, level=lv: self._set_skill_level(level))
            chip_row.addWidget(chip, (lv - 1) // 5, (lv - 1) % 5)
            self._lvl_chip_btns.append(chip)
        sl.addLayout(chip_row)
        self._sync_skill_level_chips(7)
        lo.addWidget(g_sk)

        g_param = QGroupBox("技能参数")
        pg = QGridLayout(g_param)
        pg.addWidget(QLabel("连发数:"), 0, 0)
        self._hit_spin = QSpinBox()
        self._hit_spin.setRange(1, 99)
        self._hit_spin.setValue(1)
        pg.addWidget(self._hit_spin, 0, 1)
        pg.addWidget(QLabel("技能倍率:"), 1, 0)
        self._mult_input = QLineEdit("1.0")
        pg.addWidget(self._mult_input, 1, 1)
        self._mult_auto_label = QLabel("")
        self._mult_auto_label.setStyleSheet("color: #888; font-size: 11px;")
        pg.addWidget(self._mult_auto_label, 1, 2)
        self._cond_check = QCheckBox("仅攻击到一人时（激活条件倍率）")
        self._cond_check.setVisible(False)
        pg.addWidget(self._cond_check, 2, 0, 1, 3)
        self._total_mult_label = QLabel("总伤害倍率: 1.000x")
        self._total_mult_label.setStyleSheet("color: #2B6CB6; font-size: 12px; font-weight: bold;")
        pg.addWidget(self._total_mult_label, 3, 0, 1, 3)
        self._mult_input.textChanged.connect(self._update_total_mult_label)
        self._hit_spin.valueChanged.connect(self._update_total_mult_label)
        lo.addWidget(g_param)

        self._skill_info_box = QGroupBox("技能信息")
        sil = QVBoxLayout(self._skill_info_box)
        self._skill_name_label = QLabel("")
        self._skill_name_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #2B6CB6;")
        sil.addWidget(self._skill_name_label)
        self._skill_meta_label = QLabel("")
        self._skill_meta_label.setStyleSheet("color: #888; font-size: 12px;")
        sil.addWidget(self._skill_meta_label)
        self._skill_desc_label = QLabel("")
        self._skill_desc_label.setWordWrap(True)
        self._skill_desc_label.setStyleSheet("color: #B0B0B0; font-size: 11px; padding: 4px 0;")
        sil.addWidget(self._skill_desc_label)
        self._skill_heal_label = QLabel("")
        self._skill_heal_label.setStyleSheet("color: #68D391; font-weight: bold; font-size: 12px;")
        sil.addWidget(self._skill_heal_label)
        self._skill_info_box.hide()
        lo.addWidget(self._skill_info_box)
        lo.addStretch()
        return w

    # ── 计算页：左下（干员基础数据） ────────────

    def _build_detail_panel(self) -> QWidget:
        """构建左下角：干员属性、信赖、潜能与天赋。"""
        w = QWidget()
        lo = QVBoxLayout(w)
        lo.setContentsMargins(0, 0, 0, 0)
        lo.setSpacing(6)

        self._det_stat_tbl = QTableWidget()
        self._det_stat_tbl.setColumnCount(2)
        self._det_stat_tbl.setHorizontalHeaderLabels(["属性", "数值"])
        self._det_stat_tbl.horizontalHeader().setStretchLastSection(True)
        self._det_stat_tbl.verticalHeader().setVisible(False)
        self._det_stat_tbl.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        lo.addWidget(self._det_stat_tbl)

        self._det_trust = QLabel("")
        self._det_trust.setWordWrap(True)
        self._det_trust.setStyleSheet("color: #68D391; font-size: 12px;")
        lo.addWidget(self._det_trust)

        self._det_potential = QLabel("")
        self._det_potential.setWordWrap(True)
        self._det_potential.setStyleSheet("color: #F6AD55; font-size: 12px;")
        lo.addWidget(self._det_potential)

        self._det_talent = QLabel("")
        self._det_talent.setWordWrap(True)
        self._det_talent.setStyleSheet("color: #B794F4; font-size: 12px;")
        lo.addWidget(self._det_talent)
        lo.addStretch()
        return w

    # ── 乘区明细页：右下（最终伤害） ────────────

    def _build_result_panel(self) -> QWidget:
        """构建右下角：结果标题、四张结果卡片与异常伤害表。"""
        w = QWidget()
        lo = QVBoxLayout(w)
        lo.setContentsMargins(0, 0, 0, 0)
        lo.setSpacing(8)

        self._result_label = QLabel("选择干员和技能，然后点击「确认计算」")
        self._result_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._result_label.setWordWrap(True)
        self._result_label.setStyleSheet("color: #888; font-size: 12px; padding: 8px;")
        lo.addWidget(self._result_label)

        card_row = QHBoxLayout()
        self._result_cards: dict[str, QLabel] = {}
        for label, key in [("最终攻击力", "atk"), ("物理伤害", "phys"), ("法术伤害", "magic"), ("真实伤害", "true")]:
            card = QFrame()
            card.setFrameShape(QFrame.Shape.StyledPanel)
            card.setStyleSheet(
                "QFrame { background-color: #222; border: 1px solid #464646; border-radius: 8px; padding: 8px; }"
            )
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(8, 4, 8, 4)
            card_layout.setSpacing(2)
            title = QLabel(label)
            title.setAlignment(Qt.AlignmentFlag.AlignCenter)
            title.setStyleSheet("color: #888; font-size: 11px; border: none;")
            card_layout.addWidget(title)
            value = QLabel("—")
            value.setAlignment(Qt.AlignmentFlag.AlignCenter)
            value.setStyleSheet("font-size: 18px; font-weight: bold; border: none;")
            card_layout.addWidget(value)
            card_row.addWidget(card)
            self._result_cards[key] = value
        lo.addLayout(card_row)

        anom_box = QGroupBox("异常/元素伤害")
        anom_lo = QVBoxLayout(anom_box)
        self._anom_tbl = QTableWidget()
        self._anom_tbl.setColumnCount(3)
        self._anom_tbl.setHorizontalHeaderLabels(["伤害类型", "倍率", "额外伤害"])
        self._anom_tbl.horizontalHeader().setStretchLastSection(True)
        self._anom_tbl.verticalHeader().setVisible(False)
        self._anom_tbl.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        anom_data = [
            ("灼燃损伤", "1.0x", "0"),
            ("凋亡损伤", "1.0x", "0"),
        ]
        self._anom_tbl.setRowCount(len(anom_data))
        for i, (damage_type, multiplier, extra) in enumerate(anom_data):
            self._anom_tbl.setItem(i, 0, QTableWidgetItem(damage_type))
            self._anom_tbl.setItem(i, 1, QTableWidgetItem(multiplier))
            self._anom_tbl.setItem(i, 2, QTableWidgetItem(extra))
        anom_lo.addWidget(self._anom_tbl)
        lo.addWidget(anom_box)
        lo.addStretch()
        return w

    # ── 确认状态 ──────────────────────────────

    def _on_sheet_value_changed(self, _path: str, _value: object) -> None:
        """ComputeSheet 输入变化时只标记待确认。"""
        self._mark_pending()

    def _mark_pending(self) -> None:
        """选择/输入变更后：底部确认按钮显示待更新。"""
        if hasattr(self, "_shell"):
            self._shell.set_pending("确认选择（待更新）")
            self._shell.set_status("待确认")

    def _set_confirm_ui_computing(self) -> None:
        """计算进行中。"""
        self._shell.set_confirm_enabled(False)
        self._shell.set_confirm_text("计算中…")
        self._shell.set_status("计算中…")

    def _set_confirm_ui_confirmed(self) -> None:
        """确认完成。"""
        self._shell.set_confirmed("已确认")
        self._shell.set_status("已确认")

    def _set_confirm_ui_failed(self, message: str) -> None:
        """计算失败：恢复确认按钮并显示原因。"""
        self._shell.set_confirmed("确认计算")
        self._shell.set_status(message)


__all__ = ["ArknightsAppUIMixin"]
