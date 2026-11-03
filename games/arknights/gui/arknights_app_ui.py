# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""ArknightsAppUIMixin — 明日方舟主窗口的菜单与界面构建。

从 ``ArknightsDamageApp.py`` 按符号边界拆出（P2-07 结构债清理）。
"""

from __future__ import annotations

from typing import cast

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
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
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from games.arknights.gui.arknights_compute_sheet import (
    create_arknights_compute_sheet,
    ensure_arknights_adapter,
    hide_sheet_eval_button,
    layout_for_damage_app,
)
from games.arknights.operator_catalog import STAR_TIERS, list_professions
from utils.gui.donation import append_donation_help_menu_action, open_donation_dialog
from utils.gui.help_dialog import HelpDialog
from utils.gui.help_loader import load_multi_category


class ArknightsAppUIMixin:
    """菜单、帮助、捐赠与左右分栏界面构建。"""

    def _open_help(self) -> None:
        """打开使用说明帮助对话框。"""
        sections = load_multi_category({"完整说明书": ["GUI ⑪：明日方舟计算器", "数据结构与文件格式"]})
        dlg = HelpDialog(
            build_tree=lambda: sections,
            parent=cast(QMainWindow, self),
            title="明日方舟计算器 — 使用说明",
        )
        dlg.exec()

    def _setup_menu(self) -> None:
        """构建应用菜单栏（帮助菜单）。"""
        host = cast(QMainWindow, self)
        mb = host.menuBar()
        help_menu = mb.addMenu("帮助(&H)")
        help_action = QAction("使用说明(&U)", host)
        help_action.setShortcut(QKeySequence("F1"))
        help_action.triggered.connect(self._open_help)
        help_menu.addAction(help_action)
        append_donation_help_menu_action(help_menu, host)

    def _open_donation(self) -> None:
        """打开捐赠对话框。"""
        open_donation_dialog(cast(QMainWindow, self))

    # ═══════════════════════════════════════════
    #  UI 构建
    # ═══════════════════════════════════════════

    def _setup_ui(self) -> None:
        """构建主界面布局（左右分栏）。"""
        cw = QWidget()
        cast(QMainWindow, self).setCentralWidget(cw)
        lo = QHBoxLayout(cw)
        lo.setContentsMargins(12, 12, 12, 12)
        lo.setSpacing(12)

        sp = QSplitter(Qt.Horizontal)
        lo.addWidget(sp)
        sp.addWidget(self._build_left())
        sp.addWidget(self._build_right())
        sp.setSizes([440, 920])

    # ── 左栏 ──

    def _build_left(self) -> QWidget:
        """构建左侧面板（筛选、干员选择、技能选择、干员详情）。"""
        w = QWidget()
        lo = QVBoxLayout(w)
        lo.setContentsMargins(0, 0, 0, 0)
        lo.setSpacing(8)

        # 筛选（星级 / 主职业 / 分支）
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

        # 干员选择
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

        # 技能选择
        g_sk = QGroupBox("技能")
        sl = QVBoxLayout(g_sk)
        self._skill_combo = QComboBox()
        self._skill_combo.addItems(["普攻", "技能1", "技能2", "技能3"])
        self._skill_combo.currentIndexChanged.connect(self._on_skill_changed)
        sl.addWidget(self._skill_combo)
        lo.addWidget(g_sk)

        # 技能信息
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

        # 干员详情
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self._detail_w = QWidget()
        self._detail_lo = QVBoxLayout(self._detail_w)
        self._detail_lo.setContentsMargins(0, 0, 0, 0)

        self._det_name = QLabel("")
        self._det_name.setStyleSheet("font-size: 18px; font-weight: bold; color: #E0E0E0;")
        self._detail_lo.addWidget(self._det_name)

        self._det_info = QLabel("")
        self._det_info.setStyleSheet("color: #888; font-size: 12px;")
        self._detail_lo.addWidget(self._det_info)

        self._det_trait = QLabel("")
        self._det_trait.setWordWrap(True)
        self._det_trait.setStyleSheet("color: #B0B0B0; font-style: italic; padding: 4px 0;")
        self._detail_lo.addWidget(self._det_trait)

        self._det_stat_tbl = QTableWidget()
        self._det_stat_tbl.setColumnCount(2)
        self._det_stat_tbl.setHorizontalHeaderLabels(["属性", "数值"])
        self._det_stat_tbl.horizontalHeader().setStretchLastSection(True)
        self._det_stat_tbl.setMaximumHeight(250)
        self._det_stat_tbl.verticalHeader().setVisible(False)
        self._detail_lo.addWidget(self._det_stat_tbl)

        self._det_trust = QLabel("")
        self._det_trust.setWordWrap(True)
        self._det_trust.setStyleSheet("color: #68D391; font-size: 12px;")
        self._detail_lo.addWidget(self._det_trust)

        self._det_potential = QLabel("")
        self._det_potential.setWordWrap(True)
        self._det_potential.setStyleSheet("color: #F6AD55; font-size: 12px;")
        self._detail_lo.addWidget(self._det_potential)

        self._det_talent = QLabel("")
        self._det_talent.setWordWrap(True)
        self._det_talent.setStyleSheet("color: #B794F4; font-size: 12px;")
        self._detail_lo.addWidget(self._det_talent)

        self._detail_lo.addStretch()
        scroll.setWidget(self._detail_w)
        lo.addWidget(scroll)

        return w

    # ── 右栏 ──

    def _build_right(self) -> QWidget:
        """构建右侧面板（技能参数、敌人参数、额外加成、结果展示）。"""
        w = QWidget()
        lo = QVBoxLayout(w)
        lo.setContentsMargins(0, 0, 0, 0)
        lo.setSpacing(8)

        scr = QScrollArea()
        scr.setWidgetResizable(True)
        sw = QWidget()
        sl = QVBoxLayout(sw)
        sl.setSpacing(10)

        # 技能参数
        g_sp = QGroupBox("技能参数")
        spg = QGridLayout(g_sp)
        spg.addWidget(QLabel("技能等级:"), 0, 0)
        self._lvl_slider = QSlider(Qt.Horizontal)
        self._lvl_slider.setRange(1, 10)
        self._lvl_slider.setValue(7)
        self._lvl_slider.setTickPosition(QSlider.TicksBelow)
        self._lvl_slider.setTickInterval(1)
        self._lvl_slider.valueChanged.connect(self._on_level_changed)
        spg.addWidget(self._lvl_slider, 0, 1)
        self._lvl_label = QLabel("Lv.7")
        self._lvl_label.setStyleSheet("color: #2B6CB6; font-weight: bold;")
        spg.addWidget(self._lvl_label, 0, 2)

        chip_row = QHBoxLayout()
        self._lvl_chip_btns: list[QPushButton] = []
        for lv in range(1, 11):
            chip_label = f"Lv.{lv}" if lv <= 7 else f"专{lv - 7}"
            chip = QPushButton(chip_label)
            chip.setCheckable(True)
            chip.setFixedHeight(26)
            chip.clicked.connect(lambda _checked=False, level=lv: self._set_skill_level(level))
            chip_row.addWidget(chip)
            self._lvl_chip_btns.append(chip)
        spg.addLayout(chip_row, 1, 0, 1, 3)
        self._sync_skill_level_chips(7)

        spg.addWidget(QLabel("连发数:"), 2, 0)
        self._hit_spin = QSpinBox()
        self._hit_spin.setRange(1, 99)
        self._hit_spin.setValue(1)
        spg.addWidget(self._hit_spin, 2, 1)

        spg.addWidget(QLabel("技能倍率:"), 3, 0)
        self._mult_input = QLineEdit("1.0")
        spg.addWidget(self._mult_input, 3, 1)
        self._mult_auto_label = QLabel("")
        self._mult_auto_label.setStyleSheet("color: #888; font-size: 11px;")
        spg.addWidget(self._mult_auto_label, 3, 2)

        self._cond_check = QCheckBox("仅攻击到一人时（激活条件倍率）")
        self._cond_check.setVisible(False)
        spg.addWidget(self._cond_check, 4, 0, 1, 3)

        self._total_mult_label = QLabel("总伤害倍率: 1.000x")
        self._total_mult_label.setStyleSheet("color: #2B6CB6; font-size: 12px; font-weight: bold;")
        spg.addWidget(self._total_mult_label, 5, 0, 1, 3)
        self._mult_input.textChanged.connect(self._update_total_mult_label)
        self._hit_spin.valueChanged.connect(self._update_total_mult_label)
        sl.addWidget(g_sp)

        pkg, full_layout = ensure_arknights_adapter()
        param_layout = layout_for_damage_app(full_layout)
        self._param_sheet = create_arknights_compute_sheet(pkg.dag_service, param_layout, parent=sw)
        hide_sheet_eval_button(self._param_sheet)
        sl.addWidget(self._param_sheet.widget)

        sl.addStretch()
        scr.setWidget(sw)
        lo.addWidget(scr)

        # 计算按钮
        self._calc_btn = QPushButton("开始计算")
        self._calc_btn.clicked.connect(self._on_compute)
        lo.addWidget(self._calc_btn)

        donation_btn = QPushButton("🤝 自愿捐赠")
        donation_btn.setStyleSheet(
            "QPushButton { background-color: transparent; color: #D1D1D1; "
            "border: 1px solid #464646; border-radius: 6px; padding: 6px 12px; }"
            "QPushButton:hover { border-color: #c0392b; color: #e74c3c; }"
        )
        donation_btn.clicked.connect(self._open_donation)
        lo.addWidget(donation_btn)

        # 结果标签
        self._result_label = QLabel("选择干员和技能，然后点击「开始计算」")
        self._result_label.setAlignment(Qt.AlignCenter)
        self._result_label.setStyleSheet("color: #888; font-size: 12px; padding: 8px;")
        lo.addWidget(self._result_label)

        # 结果卡片行
        card_row = QHBoxLayout()
        self._result_cards: dict[str, QLabel] = {}
        for label, key in [("最终攻击力", "atk"), ("物理伤害", "phys"), ("法术伤害", "magic"), ("真实伤害", "true")]:
            c = QFrame()
            c.setFrameShape(QFrame.StyledPanel)
            c.setStyleSheet(
                "QFrame { background-color: #222; border: 1px solid #464646; border-radius: 8px; padding: 8px; }"
            )
            cl = QVBoxLayout(c)
            cl.setContentsMargins(8, 4, 8, 4)
            cl.setSpacing(2)
            tl = QLabel(label)
            tl.setAlignment(Qt.AlignCenter)
            tl.setStyleSheet("color: #888; font-size: 11px; border: none;")
            cl.addWidget(tl)
            vl = QLabel("—")
            vl.setAlignment(Qt.AlignCenter)
            vl.setStyleSheet("font-size: 18px; font-weight: bold; border: none;")
            cl.addWidget(vl)
            card_row.addWidget(c)
            self._result_cards[key] = vl
        lo.addLayout(card_row)

        # 结果明细表（乘区 breakdown）
        self._result_table = QTableWidget()
        self._result_table.setColumnCount(2)
        self._result_table.setHorizontalHeaderLabels(["乘区/指标", "数值"])
        self._result_table.horizontalHeader().setStretchLastSection(True)
        self._result_table.setMaximumHeight(280)
        self._result_table.verticalHeader().setVisible(False)
        lo.addWidget(self._result_table)

        # 异常/元素伤害面板（类似终末地的异常矩阵）
        anom_box = QGroupBox("异常/元素伤害")
        anom_lo = QVBoxLayout(anom_box)
        self._anom_tbl = QTableWidget()
        self._anom_tbl.setColumnCount(3)
        self._anom_tbl.setHorizontalHeaderLabels(["伤害类型", "倍率", "额外伤害"])
        self._anom_tbl.horizontalHeader().setStretchLastSection(True)
        self._anom_tbl.setMaximumHeight(150)
        self._anom_tbl.verticalHeader().setVisible(False)
        # 填入预设行
        anom_data = [
            ("灼燃损伤", "1.0x", "0"),
            ("凋亡损伤", "1.0x", "0"),
        ]
        self._anom_tbl.setRowCount(len(anom_data))
        for i, (t, m, d) in enumerate(anom_data):
            self._anom_tbl.setItem(i, 0, QTableWidgetItem(t))
            self._anom_tbl.setItem(i, 1, QTableWidgetItem(m))
            self._anom_tbl.setItem(i, 2, QTableWidgetItem(d))
        anom_lo.addWidget(self._anom_tbl)
        lo.addWidget(anom_box)

        return w
