# SPDX-License-Identifier: AGPL-3.0
"""明日方舟 Desktop GUI 伤害计算器。

基于 PySide6，直接调用本地 DAG 引擎 + skill_parser。
"""

from __future__ import annotations

import sys
from typing import Any

# 深色主题 QSS — 框架 ThemeManager 基础 + Arknights 特定覆盖
from calc_framework.ui.theme import ThemeManager as _ThemeManager
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QApplication,
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

from games.arknights.calc.dag_adapter.adapter import compute_snapshot_with_dag, get_parsed_skill_info
from games.arknights.calc.dag_adapter.loader import _parse_potential_atk
from games.arknights.calc.skill_parser import ParsedSkillInfo
from games.arknights.gui.arknights_compute_sheet import (
    create_arknights_compute_sheet,
    ensure_arknights_adapter,
    hide_sheet_eval_button,
    layout_for_damage_app,
    merge_atk_percent_bonus,
    populate_operator_context,
    read_compute_params_from_sheet,
)
from games.arknights.gui.operator_combo import configure_operator_combobox
from games.arknights.operator_catalog import (
    STAR_TIERS,
    build_operator_index,
    filter_operator_index,
    list_branches,
    list_professions,
    load_operators_map,
)
from utils.gui.donation import append_donation_help_menu_action, open_donation_dialog
from utils.gui.help_dialog import HelpDialog
from utils.gui.help_loader import load_multi_category

_BASE_DARK = _ThemeManager().stylesheet("dark")
DARK_QSS = (
    _BASE_DARK
    + """
QGroupBox {
    border: 1px solid #464646; border-radius: 8px; margin-top: 12px;
    padding-top: 16px; font-size: 13px; font-weight: bold; color: #E0E0E0;
}
QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 6px; }
QPushButton {
    background-color: #2B6CB6; color: white; border: none; border-radius: 6px;
    padding: 8px 24px; font-size: 14px; font-weight: bold; min-height: 20px;
}
QPushButton:hover { background-color: #3182CE; }
QPushButton:pressed { background-color: #1A4A8A; }
QPushButton:disabled { background-color: #4A4A4A; color: #888888; }
QSlider::groove:horizontal { height: 6px; background: #3C3C3C; border-radius: 3px; }
QSlider::handle:horizontal {
    background: #2B6CB6; width: 16px; height: 16px;
    margin: -5px 0; border-radius: 8px;
}
QSlider::sub-page:horizontal { background: #2B6CB6; border-radius: 3px; }
QTableWidget { border-radius: 4px; gridline-color: #333333; }
QTableWidget::item { padding: 4px 8px; }
QHeaderView::section { border: 1px solid #464646; padding: 4px; }
"""
)


class ArknightsDamageApp(QMainWindow):
    """明日方舟桌面伤害计算器 — 完整版（与 Web 页面对齐）。"""

    def __init__(self, *, embedded: bool = False) -> None:
        self._embedded = embedded
        existing = QApplication.instance()
        if existing is None:
            self._qapp: QApplication = QApplication(sys.argv)  # type: ignore[name-defined]
            self._owns_qapp = True
        else:
            self._qapp = existing
            self._owns_qapp = False
        if self._owns_qapp:
            self._qapp.setStyle("Fusion")
            self._qapp.setStyleSheet(DARK_QSS)

        super().__init__()
        self.setWindowTitle("明日方舟 伤害计算器")
        self.setMinimumSize(1200, 720)
        self.resize(1366, 768)

        self._operators_map = load_operators_map()
        self._operator_index = build_operator_index(self._operators_map)
        self._current_operator: dict[str, Any] | None = None
        self._skill_count: int = 0

        self._setup_menu()
        self._setup_ui()

    # ── 菜单 ──

    def _open_help(self) -> None:
        """打开使用说明帮助对话框。"""
        sections = load_multi_category({"完整说明书": ["GUI ⑪：明日方舟计算器", "数据结构与文件格式"]})
        dlg = HelpDialog(build_tree=lambda: sections, parent=self, title="明日方舟计算器 — 使用说明")
        dlg.exec()

    def _setup_menu(self) -> None:
        """构建应用菜单栏（帮助菜单）。"""
        mb = self.menuBar()
        help_menu = mb.addMenu("帮助(&H)")
        help_action = QAction("使用说明(&U)", self)
        help_action.setShortcut(QKeySequence("F1"))
        help_action.triggered.connect(self._open_help)
        help_menu.addAction(help_action)
        append_donation_help_menu_action(help_menu, self)

    def _open_donation(self) -> None:
        """打开捐赠对话框。"""
        open_donation_dialog(self)

    # ═══════════════════════════════════════════
    #  UI 构建
    # ═══════════════════════════════════════════

    def _setup_ui(self) -> None:
        """构建主界面布局（左右分栏）。"""
        cw = QWidget()
        self.setCentralWidget(cw)
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

    # ═══════════════════════════════════════════
    #  信号处理
    # ═══════════════════════════════════════════

    def _update_total_mult_label(self) -> None:
        """更新总伤害倍率展示（与 Web 一致：技能倍率 × 连发数）。"""
        try:
            mult = float(self._mult_input.text() or "1.0")
        except ValueError:
            mult = 1.0
        hits = self._hit_spin.value()
        self._total_mult_label.setText(f"总伤害倍率: {mult * hits:.3f}x")

    def _set_skill_level(self, level: int) -> None:
        """技能等级快捷按钮 → 滑块。"""
        self._lvl_slider.setValue(level)

    def _sync_skill_level_chips(self, level: int) -> None:
        """同步技能等级快捷按钮选中态。"""
        for idx, chip in enumerate(self._lvl_chip_btns, start=1):
            chip.blockSignals(True)
            chip.setChecked(idx == level)
            chip.blockSignals(False)

    def _sync_param_sheet(self) -> None:
        """干员/技能变化时同步 ComputeSheet 信赖与潜能。"""
        if not self._current_operator:
            return
        level = self._lvl_slider.value()
        si = self._skill_combo.currentIndex() - 1
        info = get_parsed_skill_info(self._current_operator, level, si)
        populate_operator_context(
            self._param_sheet,
            self._current_operator,
            skill_multiplier=info.effective_multiplier,
            skill_level=level,
        )

    def _active_stars(self) -> set[int]:
        """获取当前勾选的所有星级。"""
        return {s for s, cb in self._star_checks.items() if cb.isChecked()}

    def _refresh_branch_combo(self) -> None:
        """根据当前职业刷新分支下拉选项。"""
        profession = self._prof_combo.currentData() or ""
        self._branch_combo.blockSignals(True)
        current = self._branch_combo.currentData() or ""
        self._branch_combo.clear()
        self._branch_combo.addItem("全部", "")
        for b in list_branches(self._operator_index, profession):
            self._branch_combo.addItem(b, b)
        idx = self._branch_combo.findData(current)
        if idx >= 0:
            self._branch_combo.setCurrentIndex(idx)
        self._branch_combo.blockSignals(False)

    def _refresh_operator_combo(self) -> None:
        """根据当前筛选条件刷新干员下拉列表。"""
        filtered = filter_operator_index(
            self._operator_index,
            active_stars=self._active_stars(),
            profession=self._prof_combo.currentData() or "",
            branch=self._branch_combo.currentData() or "",
        )
        names = [op["名称"] for op in filtered]
        current = self._op_combo.currentText()
        configure_operator_combobox(self._op_combo, names, preserve=current)
        total = len(self._operator_index)
        self._op_count_label.setText(f"显示 {len(names)} / {total} 个干员")

    def _on_profession_changed(self) -> None:
        """职业选择变化时刷新分支和干员列表。"""
        self._refresh_branch_combo()
        self._on_filter_changed()

    def _on_filter_changed(self) -> None:
        """筛选条件变化时刷新干员列表。"""
        self._refresh_operator_combo()

    def _on_op_selected(self, name: str) -> None:
        """选中干员时更新详情和技能信息。"""
        if not name or name not in self._operators_map:
            return
        self._current_operator = self._operators_map[name]
        self._skill_count = len(self._current_operator.get("技能", []))
        # 更新技能下拉
        self._skill_combo.blockSignals(True)
        self._skill_combo.clear()
        self._skill_combo.addItem("普攻")
        for i in range(min(self._skill_count, 3)):
            self._skill_combo.addItem(f"技能{i + 1}")
        for i in range(self._skill_count, 3):
            self._skill_combo.addItem(f"技能{i + 1}（无数据）")
        self._skill_combo.blockSignals(False)
        self._update_detail()
        self._on_skill_changed(1)  # default to skill 1

    def _on_skill_changed(self, idx: int) -> None:
        """技能选择变化时更新技能信息。"""
        if not self._current_operator:
            return
        si = idx - 1  # 0=普攻(-1), 1=技能1(0), 2=技能2(1), 3=技能3(2)
        level = self._lvl_slider.value()
        info = get_parsed_skill_info(self._current_operator, level, si)
        self._apply_skill_info(info)

    def _on_level_changed(self, value: int) -> None:
        """技能等级滑块变化时更新标签和技能信息。"""
        label = f"Lv.{value}" if value <= 7 else f"专精{value - 7}"
        self._lvl_label.setText(label)
        self._sync_skill_level_chips(value)
        self._on_skill_changed(self._skill_combo.currentIndex())

    def _apply_skill_info(self, info: ParsedSkillInfo) -> None:
        """将技能解析信息应用到 UI 控件。"""
        # 技能信息
        self._skill_info_box.show()
        self._skill_name_label.setText(info.name)
        self._skill_meta_label.setText(f"SP={info.sp_cost}  初始={info.init_sp}  持续={info.duration}秒")
        self._skill_desc_label.setText(info.description[:200] if info.description else "无描述")

        self._cond_check.setChecked(False)

        # 治疗标记
        if info.is_healing:
            self._skill_heal_label.setText("⚕ 治疗技能 — 结果数值为治疗量")
            self._cond_check.setVisible(False)
        else:
            self._skill_heal_label.setText("")
            self._cond_check.setVisible(info.has_conditional)
            if info.has_conditional:
                self._cond_check.setText(f"仅攻击到一人时（倍率 {info.conditional_mult:.2f}x）")

        # 自动倍率
        eff_mult = info.effective_multiplier
        auto_text = f"自动检测: {eff_mult:.2f}x"
        if info.atk_buff_hint > 0:
            auto_text += f"（含 ATK+{info.atk_buff_hint * 100:.0f}% 加成）"
        self._mult_auto_label.setText(auto_text)
        self._mult_input.setText(f"{eff_mult:.2f}")

        # 连发数
        self._hit_spin.setValue(info.hit_count)
        self._update_total_mult_label()
        self._sync_param_sheet()

    def _update_detail(self) -> None:
        """更新右侧干员详情面板（名称/属性/信赖/天赋）。"""
        op = self._current_operator
        if not op:
            return
        name = op.get("名称", "?")
        star = op.get("星级", 0)
        cls = op.get("职业", "")
        branch = op.get("分支", "")
        trait = op.get("特性", "")
        self._det_name.setText(f"{name}  {'★' * star}")
        self._det_info.setText(f"{cls} · {branch}")
        self._det_trait.setText(trait)

        base = op.get("基础属性", {})
        labels = {
            "生命": "生命上限",
            "攻击": "攻击力",
            "防御": "防御力",
            "法术抗性": "法术抗性",
            "部署费用": "部署费用",
            "再部署": "再部署时间",
            "阻挡数": "阻挡数",
            "攻击间隔": "攻击间隔",
        }
        self._det_stat_tbl.setRowCount(len(base))
        for i, (k, v) in enumerate(base.items()):
            self._det_stat_tbl.setItem(i, 0, QTableWidgetItem(labels.get(k, k)))  # type: ignore[arg-type]
            self._det_stat_tbl.setItem(i, 1, QTableWidgetItem(f"{v:.1f}" if isinstance(v, float) else str(v)))
        self._det_stat_tbl.resizeColumnsToContents()

        trust = op.get("信赖加成", {})
        if trust and any(v != 0 for v in trust.values()):
            parts = "  ".join(f"{labels.get(k, k)} {'+' if v >= 0 else ''}{v}" for k, v in trust.items() if v != 0)
            self._det_trust.setText(f"信赖加成（200%）：{parts}")
            self._det_trust.show()
        else:
            self._det_trust.hide()

        potentials = op.get("潜能", [])
        pot_atk = _parse_potential_atk(potentials) if isinstance(potentials, list) else 0.0
        if pot_atk > 0:
            self._det_potential.setText(f"潜能攻击（满潜合计）：+{pot_atk:.0f}")
            self._det_potential.show()
        else:
            self._det_potential.hide()

        talents = op.get("天赋", [])
        if talents:
            lines = [f"{t.get('name', '')}（{t.get('unlock', '')}）：{t.get('description', '')}" for t in talents]
            self._det_talent.setText("天赋：\n" + "\n".join(lines))
            self._det_talent.show()
        else:
            self._det_talent.hide()

    # ═══════════════════════════════════════════
    #  计算
    # ═══════════════════════════════════════════

    def _on_compute(self) -> None:
        """执行伤害计算并更新所有结果展示面板。"""
        if not self._current_operator:
            self._result_label.setText("请先选择一个干员")
            return

        try:
            level = self._lvl_slider.value()
            si = self._skill_combo.currentIndex() - 1
            skill_info = get_parsed_skill_info(self._current_operator, level, si)

            # 技能倍率：手动输入优先
            try:
                skill_mult = float(self._mult_input.text() or "1.0")
            except ValueError:
                skill_mult = skill_info.effective_multiplier

            # 条件触发
            if self._cond_check.isChecked() and skill_info.has_conditional:
                skill_mult = skill_info.conditional_mult

            hit_count = self._hit_spin.value()

            sheet_params = read_compute_params_from_sheet(self._param_sheet)
            enemy_def = sheet_params["enemy_def"]
            enemy_res = sheet_params["enemy_res"]
            def_pen = sheet_params["def_penetration"]
            res_pen = sheet_params["res_penetration"]
            atk_bonus = merge_atk_percent_bonus(
                sheet_params["atk_percent_bonus"],
                skill_info.atk_buff_hint,
            )
            dmg_bonus = sheet_params["dmg_bonus"]

            result = compute_snapshot_with_dag(
                operator=self._current_operator,
                skill_level=level,
                skill_multiplier=skill_mult,
                enemy_def=enemy_def,
                enemy_res=enemy_res,
                atk_percent_bonus=atk_bonus,
                dmg_bonus=dmg_bonus,
                def_penetration=def_pen,
                res_penetration=res_pen,
                trust_atk_override=sheet_params["trust_atk"],
                pot_atk_override=sheet_params["pot_atk"],
            )

            outputs = result.outputs
            final_atk = outputs.get("最终攻击力", 0)
            phys = outputs.get("物理伤害", 0)
            magic = outputs.get("法术伤害", 0)
            true_dmg = outputs.get("真伤伤害", 0)

            # 更新结果卡片
            self._result_cards["atk"].setText(f"{final_atk:.1f}")
            self._result_cards["phys"].setText(f"{phys:.1f}")
            self._result_cards["phys"].setStyleSheet(
                "font-size: 18px; font-weight: bold; color: #DAA520; border: none;"
            )
            self._result_cards["magic"].setText(f"{magic:.1f}")
            self._result_cards["magic"].setStyleSheet(
                "font-size: 18px; font-weight: bold; color: #2B6CB6; border: none;"
            )
            self._result_cards["true"].setText(f"{true_dmg:.1f}")
            self._result_cards["true"].setStyleSheet(
                "font-size: 18px; font-weight: bold; color: #68D391; border: none;"
            )

            # 乘区明细表
            op = self._current_operator
            base_atk = float(op.get("基础属性", {}).get("攻击", 0))
            trust_atk = sheet_params["trust_atk"]
            pot_atk = sheet_params["pot_atk"]
            zone_rows = [
                ("基础攻击力", f"{base_atk:.1f}"),
                ("信赖加成", f"+{trust_atk:.1f}" if trust_atk > 0 else "0"),
                ("潜能攻击", f"+{pot_atk:.1f}" if pot_atk > 0 else "0"),
                (f"ATK%加成（{atk_bonus:.0f}%）", f"+{base_atk * atk_bonus / 100:.1f}"),
                ("最终攻击力", f"{final_atk:.1f}"),
                ("技能倍率", f"x{skill_mult:.2f}"),
                ("连发数", f"x{hit_count}"),
                ("总伤害倍率", f"x{skill_mult * hit_count:.2f}"),
                ("", ""),
                ("防御力", f"{enemy_def:.0f}"),
                ("法术抗性", f"{enemy_res:.0f}%"),
                ("", ""),
                (
                    "物理伤害（单发）",
                    f"{phys:.1f}" if hit_count <= 1 else f"{(phys / hit_count if hit_count else 0):.1f}",
                ),
                # "法术伤害（单发）" 类似
            ]
            if hit_count > 1:
                zone_rows.append(("物理伤害（合计）", f"{phys * hit_count:.1f}"))
                zone_rows.append(("法术伤害（合计）", f"{magic * hit_count:.1f}"))
                zone_rows.append(("真伤伤害（合计）", f"{true_dmg * hit_count:.1f}"))

            self._result_table.setRowCount(len(zone_rows))
            for i, (k, v) in enumerate(zone_rows):
                self._result_table.setItem(i, 0, QTableWidgetItem(k))
                self._result_table.setItem(i, 1, QTableWidgetItem(v))
            self._result_table.resizeColumnsToContents()

            op_name = op.get("名称", "")
            label = f"计算结果 — {op_name}"
            label += f"（{skill_info.name}，总伤害倍率 {skill_mult * hit_count:.2f}x）"
            if skill_info.is_healing:
                label += " ⚕ 治疗技能"
            self._result_label.setText(label)
            self._result_label.setStyleSheet("color: #68D391; font-size: 14px; font-weight: bold; padding: 8px;")

        except Exception as e:
            self._result_label.setText(f"计算错误: {e}")
            self._result_label.setStyleSheet("color: #FC8181; font-size: 12px; padding: 8px;")
            import traceback

            traceback.print_exc()

    def run(self) -> None:
        """显示主窗口；独立启动时进入事件循环。"""
        self.showMaximized()
        if self._owns_qapp:
            sys.exit(self._qapp.exec())

    def show_embedded(self) -> None:
        """由 launcher 同进程拉起时仅显示窗口。"""
        self.showMaximized()


def main() -> None:
    """启动明日方舟桌面伤害计算器（独立入口）。"""
    from pathlib import Path as _Path

    _REPO_ROOT = _Path(__file__).resolve().parents[2].parent
    _FW_SRC = _REPO_ROOT / "framework" / "src"
    if str(_FW_SRC) not in sys.path:
        sys.path.insert(0, str(_FW_SRC))
    if str(_REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(_REPO_ROOT))

    window = ArknightsDamageApp()
    window.run()


if __name__ == "__main__":
    main()
