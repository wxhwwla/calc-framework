# SPDX-License-Identifier: AGPL-3.0
"""高级页控制栏：搜索列与多技能列构建器（BuilderMixin）。"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from games.endfield.calc.manual_buff.abnormal_matrix import (
    ABNORMAL_MATRIX_HINT,
    matrix_column_labels,
    physical_abnormal_matrix_specs,
    spell_abnormal_matrix_specs,
)
from games.endfield.gui.controls.search.search_settings import (
    build_worker_option_labels,
)
from games.endfield.gui.shell.qt_control_dock_widgets import (
    HintLabel,
    SectionHeader,
    SmallLabel,
    build_manual_abnormal_matrix,
)

_FIXED_SLOT_SPECS: list[tuple[str, str]] = [
    ("chest", "护甲"),
    ("gloves", "护手"),
    ("accessory_a", "配件A"),
    ("accessory_b", "配件B"),
]
_FIXED_SLOT_NONE_LABEL = "（不固定）"
_SECTION_COLOR = "#FF6B6B"
_LABEL_COLOR = "#CCCCCC"
_HINT_COLOR = "#888888"
_SECONDARY_BTN_HEIGHT = 32
_PRIMARY_BTN_HEIGHT = 40
_COMBO_STYLE = """
    QComboBox { background-color: #2B2B2B; color: #D1D1D1;
                border: 1px solid #464646; border-radius: 4px;
                padding: 2px 6px; min-height: 28px; }
    QComboBox:hover { border-color: #2B6CB6; }
    QComboBox::drop-down { border-left: 1px solid #464646; width: 20px; }
    QComboBox QAbstractItemView { background-color: #2B2B2B; color: #D1D1D1;
        selection-background-color: #2B6CB6; border: 1px solid #464646; }
"""
_ENTRY_STYLE = """
    QLineEdit { background-color: #2B2B2B; color: #D1D1D1;
                border: 1px solid #464646; border-radius: 4px;
                padding: 2px 6px; min-height: 24px; }
    QLineEdit:focus { border-color: #2B6CB6; }
"""
_BTN_PRIMARY_STYLE = """
    QPushButton { background-color: #2B6CB6; color: white;
                  border-radius: 6px; font-weight: bold; }
    QPushButton:hover { background-color: #3182CE; }
    QPushButton:pressed { background-color: #2C5282; }
"""

_BTN_SECONDARY_STYLE = """
    QPushButton {
        background-color: transparent; color: #D1D1D1;
        border: 1px solid #464646; border-radius: 6px;
    }
    QPushButton:hover { border-color: #2B6CB6; color: white; }
"""


class BuilderMixin:
    def _build_col_search(self) -> QWidget:
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
        lay.addWidget(SectionHeader("全量遍历", self._big))

        self.single_skill_scope_combo = QComboBox()
        self.single_skill_scope_combo.addItems(["当前武器", "同类型同星级", "同类型全部"])
        self.single_skill_scope_combo.setStyleSheet(_COMBO_STYLE)
        lay.addWidget(SmallLabel("武器候选范围", self._small))
        self.single_skill_scope_combo.currentTextChanged.connect(lambda _: self._mark_pending())
        lay.addWidget(self.single_skill_scope_combo)

        self.equipment_scope_combo = QComboBox()
        self.equipment_scope_combo.addItems(["全部装备", "仅套装装备", "仅散件装备"])
        self.equipment_scope_combo.setStyleSheet(_COMBO_STYLE)
        lay.addWidget(SmallLabel("装备范围", self._small))
        self.equipment_scope_combo.currentTextChanged.connect(lambda _: self._mark_pending())
        lay.addWidget(self.equipment_scope_combo)

        lay.addWidget(SmallLabel("固定配装（0-4 件）", self._small))
        slots_grid = QHBoxLayout()
        slots_grid.setSpacing(4)
        self.fixed_loadout_slots.clear()
        for _slot_key, slot_label in _FIXED_SLOT_SPECS:
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
        lay.addWidget(HintLabel("选择装备名称固定该槽位，选「（不固定）」则遍历。", self._small))

        self.mvp_search_btn = self._make_btn("最优搜索", _SECONDARY_BTN_HEIGHT, primary=True, style=_BTN_PRIMARY_STYLE)
        lay.addWidget(self.mvp_search_btn)
        self.full_search_btn = self._make_btn(
            "全量遍历搜索",
            _SECONDARY_BTN_HEIGHT,
            primary=True,
            style=_BTN_PRIMARY_STYLE,
        )
        lay.addWidget(self.full_search_btn)
        self.search_cancel_btn = self._make_btn("取消搜索", _SECONDARY_BTN_HEIGHT)
        self.search_cancel_btn.setEnabled(False)
        lay.addWidget(self.search_cancel_btn)

        param_row = QHBoxLayout()
        self.search_workers_combo = QComboBox()
        self.search_workers_combo.addItems(build_worker_option_labels())
        self.search_workers_combo.setStyleSheet(_COMBO_STYLE)
        param_row.addWidget(SmallLabel("并行线程", self._small))
        param_row.addWidget(self.search_workers_combo, stretch=1)
        param_row.addSpacing(8)
        self.search_top_n_combo = QComboBox()
        self.search_top_n_combo.addItems(["3", "5", "10", "20", "50"])
        self.search_top_n_combo.setCurrentText("10")
        self.search_top_n_combo.setStyleSheet(_COMBO_STYLE)
        param_row.addWidget(SmallLabel("前列条数", self._small))
        param_row.addWidget(self.search_top_n_combo, stretch=1)
        lay.addLayout(param_row)

        self.search_workers_hint_label = HintLabel("", self._small)
        self.search_workers_hint_label.setVisible(True)
        lay.addWidget(self.search_workers_hint_label)
        self._update_workers_hint()
        self.search_workers_combo.currentTextChanged.connect(lambda _: self._update_workers_hint())

        self.search_estimate_label = HintLabel("预计组合数：—", self._small)
        self.search_estimate_label.setVisible(True)
        lay.addWidget(self.search_estimate_label)
        self.mvp_status_label = HintLabel("搜索状态：未开始", self._small)
        self.mvp_status_label.setVisible(True)
        lay.addWidget(self.mvp_status_label)

        lay.addStretch()
        scroll.setWidget(body)
        outer = QVBoxLayout(col)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)
        return col
        """build col search。"""

    def _build_col_multi(self) -> QWidget:
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
        lay.addWidget(SectionHeader("多技能次数", self._big))

        self.use_manual_skill_counts_cb = QCheckBox("使用手动次数")
        self.use_manual_skill_counts_cb.setFont(self._small)
        self.use_manual_skill_counts_cb.setStyleSheet("color: #D1D1D1;")
        self.use_manual_skill_counts_cb.toggled.connect(lambda: self._mark_pending())
        lay.addWidget(self.use_manual_skill_counts_cb)

        self._segment_rows_container = QWidget()
        self._segment_rows_lay = QVBoxLayout(self._segment_rows_container)
        self._segment_rows_lay.setContentsMargins(0, 0, 0, 0)
        self._segment_rows_lay.setSpacing(2)
        self._segment_rows_lay.addWidget(SmallLabel("技能段数", self._small))
        self._segment_count_edits_dict: dict[str, QLineEdit] = {}
        self._build_segment_rows_fallback()
        lay.addWidget(self._segment_rows_container)

        self._survival_btn = self._make_btn(
            "处决/治疗估算",
            _SECONDARY_BTN_HEIGHT,
            style="""
            QPushButton { background-color: #5a4a78; color: white; border-radius: 6px; }
            QPushButton:hover { background-color: #6b5b8a; }
        """,
        )
        lay.addWidget(self._survival_btn)

        self._manual_buff_btn = self._make_btn(
            "额外加成微调",
            _SECONDARY_BTN_HEIGHT,
            style="""
            QPushButton { background-color: #2d6a4f; color: white; border-radius: 6px; }
            QPushButton:hover { background-color: #40916c; }
        """,
        )
        lay.addWidget(self._manual_buff_btn)

        lay.addWidget(SectionHeader("物理异常", self._big))
        lay.addWidget(HintLabel(ABNORMAL_MATRIX_HINT, self._small))
        self.damage_component_combo = QComboBox()
        self.damage_component_combo.addItems(["仅技能", "仅异常", "技能+异常"])
        self.damage_component_combo.setStyleSheet(_COMBO_STYLE)
        cc_row = QHBoxLayout()
        cc_row.addWidget(SmallLabel("伤害口径", self._small))
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

        crit_row = QHBoxLayout()
        self.extra_crit_rate_edit = QLineEdit("0")
        self.extra_crit_rate_edit.setStyleSheet(_ENTRY_STYLE)
        self.extra_crit_rate_edit.setFixedWidth(72)
        self.extra_crit_damage_edit = QLineEdit("0")
        self.extra_crit_damage_edit.setStyleSheet(_ENTRY_STYLE)
        self.extra_crit_damage_edit.setFixedWidth(72)
        crit_row.addWidget(SmallLabel("额外暴击率%", self._small))
        crit_row.addWidget(self.extra_crit_rate_edit)
        crit_row.addSpacing(8)
        crit_row.addWidget(SmallLabel("额外暴伤%", self._small))
        crit_row.addWidget(self.extra_crit_damage_edit)
        lay.addLayout(crit_row)

        self._physical_abnormal_specs = physical_abnormal_matrix_specs()
        self._spell_abnormal_specs = spell_abnormal_matrix_specs()
        _abnormal_cols = list(matrix_column_labels())
        self._physical_abnormal_widget, self._physical_abnormal_edits = build_manual_abnormal_matrix(
            self._small,
            self._physical_abnormal_specs,
            column_labels=tuple(_abnormal_cols),
        )
        lay.addWidget(self._physical_abnormal_widget)

        lay.addWidget(SectionHeader("法术异常", self._big))
        self._spell_abnormal_widget, self._spell_abnormal_edits = build_manual_abnormal_matrix(
            self._small,
            self._spell_abnormal_specs,
            column_labels=tuple(_abnormal_cols),
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
        """build col multi。"""

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
        from games.endfield.calc.skills.segments import list_segment_count_specs

        # 清空容器
        while self._segment_rows_lay.count():
            item = self._segment_rows_lay.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()

        self._segment_rows_lay.addWidget(SmallLabel("技能段数", self._small))
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

    """BuilderMixin。"""

    # ── 搜索参数读取 ──────────────────────────
