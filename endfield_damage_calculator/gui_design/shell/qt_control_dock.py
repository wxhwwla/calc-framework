#!/usr/bin/env python3
"""
高级页控制栏（PySide6 版）。

与 CTk 版 ``app_control_dock.py`` 平行。
三列布局：操作/乘区展示 | 全量搜索 | 多技能次数。
包含固定配装槽、异常矩阵、搜索参数、增强工具按钮。
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from gui_design.search_ui.search_settings import (
    build_worker_option_labels,
    format_parallel_workers_help,
    get_cpu_parallel_info,
    resolve_parallel_workers,
)
from gui_design.shared.calc_mode_labels import CALC_MODE_LABELS, DEFAULT_CALC_MODE_LABEL

# 固定配装槽位配置：(catalog_key, 界面标签)
_FIXED_SLOT_SPECS: list[tuple[str, str]] = [
    ("chest", "护甲"),
    ("gloves", "护手"),
    ("accessory_a", "配件A"),
    ("accessory_b", "配件B"),
]
_FIXED_SLOT_NONE_LABEL = "（不固定）"

# 物理异常类型列表（5 等级）
_PHYSICAL_ABNORMAL_TYPES = ["侵蚀", "灼烧", "冻伤", "战栗"]
_PHYSICAL_ABNORMAL_LEVELS = ["L1", "L2", "L3", "L4", "L5"]

# 法术异常类型列表（4 等级）
_SPELL_ABNORMAL_TYPES = ["侵蚀(法术)", "灼烧(法术)"]
_SPELL_ABNORMAL_LEVELS = ["L1", "L2", "L3", "L4"]

_PHYSICAL_ABNORMAL_KEYS = ["erosion", "burn", "frostbite", "trembling"]
_SPELL_ABNORMAL_KEYS = ["erosion_spell", "burn_spell"]

_PRIMARY_BTN_HEIGHT = 40
_SECONDARY_BTN_HEIGHT = 32
_SECTION_COLOR = "#FF6B6B"
_LABEL_COLOR = "#CCCCCC"
_HINT_COLOR = "#888888"

_COMBO_STYLE = """
    QComboBox {
        background-color: #2B2B2B; color: #D1D1D1;
        border: 1px solid #464646; border-radius: 4px;
        padding: 2px 6px; min-height: 28px;
    }
    QComboBox:hover { border-color: #2B6CB6; }
    QComboBox::drop-down { border-left: 1px solid #464646; width: 20px; }
    QComboBox QAbstractItemView {
        background-color: #2B2B2B; color: #D1D1D1;
        selection-background-color: #2B6CB6; border: 1px solid #464646;
    }
"""

_ENTRY_STYLE = """
    QLineEdit {
        background-color: #2B2B2B; color: #D1D1D1;
        border: 1px solid #464646; border-radius: 4px;
        padding: 2px 6px; min-height: 24px;
    }
    QLineEdit:focus { border-color: #2B6CB6; }
"""

_BTN_SECONDARY_STYLE = """
    QPushButton {
        background-color: transparent; color: #D1D1D1;
        border: 1px solid #464646; border-radius: 6px;
    }
    QPushButton:hover { border-color: #2B6CB6; color: white; }
"""

_BTN_PRIMARY_STYLE = """
    QPushButton {
        background-color: #2B6CB6; color: white;
        border-radius: 6px; font-weight: bold;
    }
    QPushButton:hover { background-color: #3182CE; }
    QPushButton:pressed { background-color: #2C5282; }
"""


class _SectionHeader(QLabel):
    def __init__(self, text: str, font: QFont) -> None:
        super().__init__(text)
        self.setFont(font)
        self.setStyleSheet(f"color: {_SECTION_COLOR}; padding: 4px 0;")


class _HintLabel(QLabel):
    def __init__(self, text: str, font: QFont) -> None:
        super().__init__(text)
        self.setFont(font)
        self.setStyleSheet(f"color: {_HINT_COLOR};")
        self.setWordWrap(True)


class _SmallLabel(QLabel):
    def __init__(self, text: str, font: QFont) -> None:
        super().__init__(text)
        self.setFont(font)
        self.setStyleSheet(f"color: {_LABEL_COLOR};")


class _ComboRow(QWidget):
    """标签 + QComboBox 水平行。"""

    def __init__(self, label: str, items: list[str], current: str, font: QFont) -> None:
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.label = _SmallLabel(label, font)
        layout.addWidget(self.label)
        self.combo = QComboBox()
        self.combo.addItems(items)
        self.combo.setCurrentText(current)
        self.combo.setStyleSheet(_COMBO_STYLE)
        layout.addWidget(self.combo, stretch=1)

    def current(self) -> str:
        return self.combo.currentText()


# ═══════════════════════════════════════════════════════
#  QtControlDock
# ═══════════════════════════════════════════════════════


class QtControlDock(QWidget):
    """高级页三列控制栏。

    包含操作按钮（确认/返回/许可）、计算模式选择、全量搜索参数、
    固定配装槽、多技能次数段行、物理/法术异常矩阵、暴击微调。
    """

    calc_mode_changed = Signal(str)
    confirm_requested = Signal()
    loadout_pending = Signal()

    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        big_font: QFont | None = None,
        small_font: QFont | None = None,
        on_back_to_main: Callable[[], None] | None = None,
        on_confirm: Callable[[], None] | None = None,
        on_attribution: Callable[[], None] | None = None,
        on_donation: Callable[[], None] | None = None,
        on_open_help: Callable[[], None] | None = None,
    ) -> None:
        super().__init__(parent)
        self._big = big_font or QFont()
        self._small = small_font or QFont()
        self._on_back_to_main = on_back_to_main
        self._on_confirm = on_confirm
        self._on_attribution = on_attribution
        self._on_donation = on_donation
        self._on_open_help = on_open_help

        # 暴露给外部的控件引用
        self.back_to_main_btn: QPushButton
        self.confirm_btn: QPushButton
        self.attribution_btn: QPushButton
        self.donation_btn: QPushButton
        self.help_btn: QPushButton
        self.calc_mode_menu: QComboBox
        self.single_skill_scope_combo: QComboBox
        self.equipment_scope_combo: QComboBox
        self.fixed_loadout_slots: list[QComboBox] = []
        self.use_manual_skill_counts_cb: QCheckBox
        self.damage_component_combo: QComboBox
        self.use_expected_crit_cb: QCheckBox
        self.include_conditional_crit_cb: QCheckBox
        self.extra_crit_rate_edit: QLineEdit
        self.extra_crit_damage_edit: QLineEdit

        self._build_ui()

    def _make_btn(self, text: str, height: int, *, primary: bool = False, style: str | None = None) -> QPushButton:
        """创建一个统一样式的 QPushButton。"""
        btn = QPushButton(text)
        btn.setMinimumHeight(height)
        btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        btn.setStyleSheet(style or (_BTN_PRIMARY_STYLE if primary else _BTN_SECONDARY_STYLE))
        return btn

    def _build_ui(self) -> None:
        """构建三列布局。"""
        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(6)

        outer.addWidget(self._build_col_actions(), stretch=1)
        outer.addWidget(self._build_col_search(), stretch=2)
        outer.addWidget(self._build_col_multi(), stretch=3)

    # ── 列 1：操作 / 乘区展示 ──────────────────────

    def _build_col_actions(self) -> QWidget:
        """构建第一列：操作按钮、计算模式、更多设置。"""
        col = QWidget()
        col.setMinimumWidth(200)
        lay = QVBoxLayout(col)
        lay.setContentsMargins(4, 4, 4, 4)
        lay.setSpacing(4)

        lay.addWidget(_SectionHeader("操作", self._big))

        self.back_to_main_btn = self._make_btn("返回计算页", _SECONDARY_BTN_HEIGHT)
        if self._on_back_to_main:
            self.back_to_main_btn.clicked.connect(self._on_back_to_main)
        lay.addWidget(self.back_to_main_btn)

        self.confirm_btn = self._make_btn("确认选择", _PRIMARY_BTN_HEIGHT, primary=True)
        if self._on_confirm:
            self.confirm_btn.clicked.connect(self._on_confirm)
        lay.addWidget(self.confirm_btn)

        self.attribution_btn = self._make_btn("数据来源与许可", _SECONDARY_BTN_HEIGHT)
        if self._on_attribution:
            self.attribution_btn.clicked.connect(self._on_attribution)
        lay.addWidget(self.attribution_btn)

        self.donation_btn = self._make_btn("🤝 自愿捐赠", _SECONDARY_BTN_HEIGHT)
        if self._on_donation:
            self.donation_btn.clicked.connect(self._on_donation)
        lay.addWidget(self.donation_btn)

        self.help_btn = self._make_btn("📖 使用说明", _SECONDARY_BTN_HEIGHT)
        if self._on_open_help:
            self.help_btn.clicked.connect(self._on_open_help)
        lay.addWidget(self.help_btn)

        lay.addSpacing(8)
        lay.addWidget(_SectionHeader("乘区展示", self._big))
        lay.addWidget(_SmallLabel("计算模式", self._small))

        self.calc_mode_menu = QComboBox()
        self.calc_mode_menu.addItems(list(CALC_MODE_LABELS))
        self.calc_mode_menu.setCurrentText(DEFAULT_CALC_MODE_LABEL)
        self.calc_mode_menu.currentTextChanged.connect(self._on_calc_mode_changed)
        self.calc_mode_menu.setStyleSheet(_COMBO_STYLE)
        lay.addWidget(self.calc_mode_menu)

        # 增强操作区域
        lay.addSpacing(8)
        lay.addWidget(_SectionHeader("工具与分享", self._big))

        self._more_settings_btn = self._make_btn("更多设置 (展开)", _SECONDARY_BTN_HEIGHT)
        self._more_settings_btn.clicked.connect(self._toggle_more_settings)
        lay.addWidget(self._more_settings_btn)

        self._more_settings_body = QWidget()
        self._more_settings_body.setVisible(False)
        ms_lay = QVBoxLayout(self._more_settings_body)
        ms_lay.setContentsMargins(0, 0, 0, 0)
        ms_lay.setSpacing(4)

        self._enemy_combo = QComboBox()
        self._enemy_combo.setStyleSheet(_COMBO_STYLE)
        ms_lay.addWidget(_SmallLabel("插件敌人", self._small))
        ms_lay.addWidget(self._enemy_combo)

        def _make_tool_btn(text: str) -> QPushButton:
            b = self._make_btn(text, _SECONDARY_BTN_HEIGHT)
            ms_lay.addWidget(b)
            return b

        self._export_btn = _make_tool_btn("导出配装 (.json)")
        self._import_btn = _make_tool_btn("导入配装 (.json)")
        self._compare_btn = _make_tool_btn("多方案对比")
        self._dashboard_btn = _make_tool_btn("伤害仪表盘")
        self._history_btn = _make_tool_btn("计算历史")
        self._export_log_btn = _make_tool_btn("导出操作日志")

        ms_lay.addStretch()
        lay.addWidget(self._more_settings_body)
        lay.addStretch()
        return col

    def _toggle_more_settings(self) -> None:
        """展开/折叠「更多设置」面板。"""
        visible = not self._more_settings_body.isVisible()
        self._more_settings_body.setVisible(visible)
        self._more_settings_btn.setText("更多设置 (折叠)" if visible else "更多设置 (展开)")

    def _on_calc_mode_changed(self, text: str) -> None:
        """计算模式下拉变更：发射 calc_mode_changed 信号。"""
        self.calc_mode_changed.emit(text)

    def current_calc_mode(self) -> str:
        """获取当前计算模式显示标签。"""
        return self.calc_mode_menu.currentText()

    # ── 列 2：全量搜索 ─────────────────────────────

    def _build_col_search(self) -> QWidget:
        """构建第二列：武器/装备范围、固定配装、搜索按钮、预估/状态。"""
        col = QWidget()
        col.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; }")

        body = QWidget()
        lay = QVBoxLayout(body)
        lay.setContentsMargins(4, 4, 4, 4)
        lay.setSpacing(4)

        lay.addWidget(_SectionHeader("全量遍历", self._big))

        self.single_skill_scope_combo = QComboBox()
        self.single_skill_scope_combo.addItems(["当前武器", "同类型同星级", "同类型全部"])
        self.single_skill_scope_combo.setStyleSheet(_COMBO_STYLE)
        lay.addWidget(_SmallLabel("武器候选范围", self._small))
        self.single_skill_scope_combo.currentTextChanged.connect(lambda _: self._mark_pending())
        lay.addWidget(self.single_skill_scope_combo)

        self.equipment_scope_combo = QComboBox()
        self.equipment_scope_combo.addItems(["全部装备", "仅套装装备", "仅散件装备"])
        self.equipment_scope_combo.setStyleSheet(_COMBO_STYLE)
        lay.addWidget(_SmallLabel("装备范围", self._small))
        self.equipment_scope_combo.currentTextChanged.connect(lambda _: self._mark_pending())
        lay.addWidget(self.equipment_scope_combo)

        # 固定配装（四槽装备名称下拉）
        lay.addWidget(_SmallLabel("固定配装（0–4 件）", self._small))
        slots_grid = QHBoxLayout()
        slots_grid.setSpacing(4)
        self.fixed_loadout_slots.clear()
        for slot_key, slot_label in _FIXED_SLOT_SPECS:
            row = QVBoxLayout()
            row.setSpacing(2)
            slot_lbl = QLabel(slot_label)
            slot_lbl.setStyleSheet(f"color: {_HINT_COLOR};")
            slot_lbl.setFont(self._small)
            cb = QComboBox()
            cb.addItem(_FIXED_SLOT_NONE_LABEL)
            cb.setStyleSheet(_COMBO_STYLE)
            cb.currentTextChanged.connect(lambda _: self._mark_pending())
            row.addWidget(slot_lbl)
            row.addWidget(cb)
            slots_grid.addLayout(row)
            self.fixed_loadout_slots.append(cb)
        lay.addLayout(slots_grid)

        lay.addWidget(_HintLabel("选择装备名称固定该槽位，选「（不固定）」则遍历。", self._small))

        # 搜索按钮
        self.mvp_search_btn = self._make_btn("MVP 搜索", _SECONDARY_BTN_HEIGHT, primary=True, style=_BTN_PRIMARY_STYLE)
        lay.addWidget(self.mvp_search_btn)

        self.full_search_btn = self._make_btn(
            "全量遍历搜索", _SECONDARY_BTN_HEIGHT, primary=True, style=_BTN_PRIMARY_STYLE
        )
        lay.addWidget(self.full_search_btn)

        self.search_cancel_btn = self._make_btn("取消搜索", _SECONDARY_BTN_HEIGHT)
        self.search_cancel_btn.setEnabled(False)
        lay.addWidget(self.search_cancel_btn)

        # 并行线程 + TopN
        param_row = QHBoxLayout()
        self.search_workers_combo = QComboBox()
        self.search_workers_combo.addItems(build_worker_option_labels())
        self.search_workers_combo.setStyleSheet(_COMBO_STYLE)
        param_row.addWidget(_SmallLabel("并行线程", self._small))
        param_row.addWidget(self.search_workers_combo, stretch=1)
        param_row.addSpacing(8)
        self.search_top_n_combo = QComboBox()
        self.search_top_n_combo.addItems(["3", "5", "10", "20", "50"])
        self.search_top_n_combo.setCurrentText("10")
        self.search_top_n_combo.setStyleSheet(_COMBO_STYLE)
        param_row.addWidget(_SmallLabel("Top 条数", self._small))
        param_row.addWidget(self.search_top_n_combo, stretch=1)
        lay.addLayout(param_row)

        self.search_workers_hint_label = _HintLabel("", self._small)
        self.search_workers_hint_label.setVisible(True)
        lay.addWidget(self.search_workers_hint_label)

        self._update_workers_hint()
        self.search_workers_combo.currentTextChanged.connect(lambda _: self._update_workers_hint())

        # 搜索预估 & 状态
        self.search_estimate_label = _HintLabel("预计组合数：—", self._small)
        self.search_estimate_label.setVisible(True)
        lay.addWidget(self.search_estimate_label)

        self.mvp_status_label = _HintLabel("搜索状态：未开始", self._small)
        self.mvp_status_label.setVisible(True)
        lay.addWidget(self.mvp_status_label)

        lay.addStretch()
        scroll.setWidget(body)

        outer = QVBoxLayout(col)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)
        return col

    # ── 列 3：多技能次数 ───────────────────────────

    def _build_col_multi(self) -> QWidget:
        """构建第三列：多技能次数段行、手动 Buff、异常矩阵、暴击微调。"""
        col = QWidget()
        col.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; }")

        body = QWidget()
        lay = QVBoxLayout(body)
        lay.setContentsMargins(4, 4, 4, 4)
        lay.setSpacing(4)

        lay.addWidget(_SectionHeader("多技能次数", self._big))

        self.use_manual_skill_counts_cb = QCheckBox("使用手动次数")
        self.use_manual_skill_counts_cb.setFont(self._small)
        self.use_manual_skill_counts_cb.setStyleSheet("color: #D1D1D1;")
        self.use_manual_skill_counts_cb.toggled.connect(lambda: self._mark_pending())
        lay.addWidget(self.use_manual_skill_counts_cb)

        self._segment_rows_container = QWidget()
        self._segment_rows_lay = QVBoxLayout(self._segment_rows_container)
        self._segment_rows_lay.setContentsMargins(0, 0, 0, 0)
        self._segment_rows_lay.setSpacing(2)
        self._segment_rows_lay.addWidget(_SmallLabel("技能段数", self._small))
        self._segment_count_edits_dict: dict[str, QLineEdit] = {}
        self._build_segment_rows_fallback()
        lay.addWidget(self._segment_rows_container)

        self._manual_buff_btn = self._make_btn(
            "场外 Buff 微调",
            _SECONDARY_BTN_HEIGHT,
            style="""
            QPushButton {
                background-color: #2d6a4f; color: white;
                border-radius: 6px;
            }
            QPushButton:hover { background-color: #40916c; }
        """,
        )
        lay.addWidget(self._manual_buff_btn)

        # 物理异常
        lay.addWidget(_SectionHeader("物理异常", self._big))
        lay.addWidget(_HintLabel("按异常类型与等级填入触发次数。", self._small))

        self.damage_component_combo = QComboBox()
        self.damage_component_combo.addItems(["仅技能", "仅异常", "技能+异常"])
        self.damage_component_combo.setStyleSheet(_COMBO_STYLE)
        cc_row = QHBoxLayout()
        cc_row.addWidget(_SmallLabel("伤害口径", self._small))
        cc_row.addWidget(self.damage_component_combo)
        lay.addLayout(cc_row)

        self.use_expected_crit_cb = QCheckBox("期望伤害模式")
        self.use_expected_crit_cb.setFont(self._small)
        self.use_expected_crit_cb.setStyleSheet("color: #D1D1D1;")
        lay.addWidget(self.use_expected_crit_cb)

        self.include_conditional_crit_cb = QCheckBox("装备条件暴击")
        self.include_conditional_crit_cb.setFont(self._small)
        self.include_conditional_crit_cb.setStyleSheet("color: #D1D1D1;")
        lay.addWidget(self.include_conditional_crit_cb)

        # 额外暴击率/暴伤
        crit_row = QHBoxLayout()
        self.extra_crit_rate_edit = QLineEdit("0")
        self.extra_crit_rate_edit.setStyleSheet(_ENTRY_STYLE)
        self.extra_crit_rate_edit.setFixedWidth(72)
        self.extra_crit_damage_edit = QLineEdit("0")
        self.extra_crit_damage_edit.setStyleSheet(_ENTRY_STYLE)
        self.extra_crit_damage_edit.setFixedWidth(72)
        crit_row.addWidget(_SmallLabel("额外暴击率%", self._small))
        crit_row.addWidget(self.extra_crit_rate_edit)
        crit_row.addSpacing(8)
        crit_row.addWidget(_SmallLabel("额外暴伤%", self._small))
        crit_row.addWidget(self.extra_crit_damage_edit)
        lay.addLayout(crit_row)

        # 物理异常矩阵
        self._physical_abnormal_widget, self._physical_abnormal_edits = _build_abnormal_matrix(
            self._small,
            _PHYSICAL_ABNORMAL_TYPES,
            _PHYSICAL_ABNORMAL_LEVELS,
        )
        lay.addWidget(self._physical_abnormal_widget)

        # 法术异常
        lay.addWidget(_SectionHeader("法术异常", self._big))
        self._spell_abnormal_widget, self._spell_abnormal_edits = _build_abnormal_matrix(
            self._small,
            _SPELL_ABNORMAL_TYPES,
            _SPELL_ABNORMAL_LEVELS,
        )
        lay.addWidget(self._spell_abnormal_widget)

        clear_btn = self._make_btn("清空全部异常次数", _SECONDARY_BTN_HEIGHT)
        clear_btn.clicked.connect(self._clear_abnormal_counts)
        lay.addWidget(clear_btn)

        lay.addStretch()
        scroll.setWidget(body)

        outer = QVBoxLayout(col)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)
        return col

    def _mark_pending(self) -> None:
        """标记配装待确认（发射 loadout_pending 信号）。"""
        self.loadout_pending.emit()

    # ── 段级次数动态行 ──────────────────────────

    def _build_segment_rows_fallback(self) -> None:
        """初始占位：3 个基础段次数输入。"""
        skill_labels = ["战技", "连携技", "终结技"]
        self._segment_count_edits_dict.clear()
        for i in range(3):
            row = QHBoxLayout()
            lbl = QLabel(f"{skill_labels[i]} 次数:")
            lbl.setStyleSheet(f"color: {_LABEL_COLOR};")
            lbl.setFont(self._small)
            edit = QLineEdit("0")
            edit.setStyleSheet(_ENTRY_STYLE)
            edit.setFixedWidth(60)
            edit.textChanged.connect(self._mark_pending)
            row.addWidget(lbl)
            row.addWidget(edit)
            row.addStretch()
            w = QWidget()
            w.setLayout(row)
            self._segment_rows_lay.addWidget(w)
            self._segment_count_edits_dict[skill_labels[i]] = edit

    def rebuild_segment_rows(self, char_data: dict | None, s1: int, s2: int, s3: int) -> None:
        """按角色技能段规格重建段级次数输入行。"""
        from calculation.skills.segments import list_segment_count_specs

        # 清空容器
        while self._segment_rows_lay.count():
            item = self._segment_rows_lay.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()

        self._segment_rows_lay.addWidget(_SmallLabel("技能段数", self._small))
        self._segment_count_edits_dict.clear()

        if not char_data:
            self._build_segment_rows_fallback()
            return

        specs = list_segment_count_specs(char_data, skill_1_level=s1, skill_2_level=s2, skill_3_level=s3)
        if not specs:
            self._build_segment_rows_fallback()
            return

        for spec in specs:
            key = str(spec["key"])
            label_text = str(spec["label"])
            row = QHBoxLayout()
            lbl = QLabel(label_text)
            lbl.setStyleSheet(f"color: {_LABEL_COLOR};")
            lbl.setFont(self._small)
            edit = QLineEdit("0")
            edit.setStyleSheet(_ENTRY_STYLE)
            edit.setFixedWidth(60)
            edit.textChanged.connect(self._mark_pending)
            row.addWidget(lbl, stretch=1)
            row.addWidget(edit)
            w = QWidget()
            w.setLayout(row)
            self._segment_rows_lay.addWidget(w)
            self._segment_count_edits_dict[key] = edit

    # ── 搜索参数读取 ──────────────────────────

    def _update_workers_hint(self) -> None:
        """刷新并行线程提示文字（基于 CPU 核心数）。"""
        info = get_cpu_parallel_info()
        workers = resolve_parallel_workers(self.search_workers_combo.currentText())
        self.search_workers_hint_label.setText(format_parallel_workers_help(info, selected_workers=workers))

    def read_workers_choice(self) -> str:
        """读取并行线程选择标签。"""
        return self.search_workers_combo.currentText()

    def read_top_n_choice(self) -> str:
        """读取 Top N 条数选择标签。"""
        return self.search_top_n_combo.currentText()

    # ── 控制值读取 ──────────────────────────────

    def populate_fixed_loadout_slots(
        self,
        catalog: dict[str, list[dict[str, Any]]],
    ) -> None:
        """从装备 catalog 填充四槽装备名称下拉。"""
        from data.equipment_filters import equipment_names_from_rows

        for i, (slot_key, _) in enumerate(_FIXED_SLOT_SPECS):
            cb = self.fixed_loadout_slots[i]
            current = cb.currentText()

            catalog_key = "accessories" if slot_key in ("accessory_a", "accessory_b") else slot_key
            rows = list(catalog.get(catalog_key) or [])
            names = equipment_names_from_rows(rows)

            cb.blockSignals(True)
            cb.clear()
            cb.addItem(_FIXED_SLOT_NONE_LABEL)
            for name in names:
                cb.addItem(name)
            cb.setCurrentText(current if current in names else _FIXED_SLOT_NONE_LABEL)
            cb.blockSignals(False)

    def read_fixed_loadout_selection(
        self,
        catalog: dict[str, list[dict[str, Any]]],
    ) -> Any:
        """从四槽下拉读取 FixedLoadoutSelection。"""
        from calculation.loadout.slot_search import FixedLoadoutSelection

        def _pick(i: int, catalog_key: str):
            name = self.fixed_loadout_slots[i].currentText()
            if name == _FIXED_SLOT_NONE_LABEL:
                return None
            for row in catalog.get(catalog_key) or []:
                if str(row.get("名称") or "") == name:
                    return row
            return None

        return FixedLoadoutSelection(
            chest=_pick(0, "chest"),
            gloves=_pick(1, "gloves"),
            accessory_a=_pick(2, "accessories"),
            accessory_b=_pick(3, "accessories"),
        )

    def read_skill_counts(self) -> dict[str, int]:
        """读取段级手动次数（仅正值）。"""
        result: dict[str, int] = {}
        edits = getattr(self, "_segment_count_edits_dict", None)
        if edits:
            for key, edit in edits.items():
                try:
                    val = max(0, int(edit.text() or "0"))
                except ValueError:
                    val = 0
                if val > 0:
                    result[key] = val
        return result

    def read_physical_abnormal_counts(self) -> dict[str, int]:
        """按级别累加各等级次数，返回 {异常键: 总次数}。"""
        return _read_abnormal_edits(
            self._physical_abnormal_edits,
            _PHYSICAL_ABNORMAL_KEYS,
        )

    def read_spell_abnormal_counts(self) -> dict[str, int]:
        """读取法术异常次数（按类型累加）。"""
        return _read_abnormal_edits(
            self._spell_abnormal_edits,
            _SPELL_ABNORMAL_KEYS,
        )

    def read_damage_component_mode(self) -> str:
        """读取伤害口径模式（skill_only / abnormal_only / skill_and_abnormal）。"""
        mapping = {"仅技能": "skill_only", "仅异常": "abnormal_only", "技能+异常": "skill_and_abnormal"}
        return mapping.get(self.damage_component_combo.currentText(), "skill_and_abnormal")

    def read_extra_crit_rate(self) -> float:
        """读取额外暴击率百分比。"""
        try:
            return float(self.extra_crit_rate_edit.text() or "0")
        except ValueError:
            return 0.0

    def read_extra_crit_damage(self) -> float:
        """读取额外暴击伤害百分比。"""
        try:
            return float(self.extra_crit_damage_edit.text() or "0")
        except ValueError:
            return 0.0

    def _clear_abnormal_counts(self) -> None:
        """清空所有异常次数输入（物理+法术）。"""
        for edits in self._physical_abnormal_edits.values():
            for e in edits:
                e.setText("0")
        for edits in self._spell_abnormal_edits.values():
            for e in edits:
                e.setText("0")
        self._mark_pending()


def _read_abnormal_edits(
    edits_by_row: dict[str, list[QLineEdit]],
    keys: list[str],
) -> dict[str, int]:
    result: dict[str, int] = {}
    for i, (row_name, edits) in enumerate(edits_by_row.items()):
        total = 0
        for e in edits:
            try:
                val = int(e.text() or "0")
            except ValueError:
                val = 0
            total += max(0, val)
        if i < len(keys):
            result[keys[i]] = total
    return result


def _build_abnormal_matrix(
    small_font: QFont,
    rows: list[str],
    cols: list[str],
) -> tuple[QWidget, dict[str, list[QLineEdit]]]:
    """构建异常矩阵输入网格，返回 (widget, edits_by_row)。"""
    w = QWidget()
    grid = QGridLayout(w)
    grid.setSpacing(2)
    grid.setContentsMargins(0, 0, 0, 0)

    edits_by_row: dict[str, list[QLineEdit]] = {}

    # 列标题
    for j, c in enumerate(cols, start=1):
        lbl = QLabel(c)
        lbl.setFont(small_font)
        lbl.setStyleSheet(f"color: {_LABEL_COLOR};")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        grid.addWidget(lbl, 0, j)

    # 行标题 + 输入框
    for i, row_name in enumerate(rows, start=1):
        lbl = QLabel(row_name)
        lbl.setFont(small_font)
        lbl.setStyleSheet(f"color: {_LABEL_COLOR};")
        grid.addWidget(lbl, i, 0)
        row_edits: list[QLineEdit] = []
        for j in range(len(cols)):
            edit = QLineEdit("0")
            edit.setStyleSheet(_ENTRY_STYLE)
            edit.setFixedWidth(44)
            edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
            grid.addWidget(edit, i, j + 1)
            row_edits.append(edit)
        edits_by_row[row_name] = row_edits

    return w, edits_by_row
