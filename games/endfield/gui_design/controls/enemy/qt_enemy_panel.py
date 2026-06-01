#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""敌方参数面板 — 插件敌人下拉 + 防御/抗性/失衡参数微调。"""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from games.endfield.calc.damage.imbalance import ENEMY_TIERS
from games.endfield.data_loading.enemy_params import (
    DEFAULT_ATTACHED_EFFECT_MULTIPLIER,
    DEFAULT_COMBO_STACKS,
    DEFAULT_CORROSION_DURATION_SEC,
    DEFAULT_ENEMY_DEFENSE,
    DEFAULT_ENEMY_RESISTANCE,
    DEFAULT_ENEMY_TIER,
    DEFAULT_IGNORE_RESISTANCE,
    DEFAULT_IMBALANCE_EFFICIENCY_BONUS,
    DEFAULT_IMBALANCE_VULNERABILITY,
    DEFAULT_IS_UNBALANCED,
    list_plugin_enemy_choices,
    resolve_enemy_defense,
    resolve_enemy_resistance,
    resolve_enemy_tier,
    resolve_ignore_resistance,
    resolve_imbalance_vulnerability,
    resolve_is_unbalanced,
)

_LABEL_COLOR = "#CCCCCC"
_HINT_COLOR = "#888888"
_SECTION_COLOR = "#FF6B6B"

_SPINBOX_STYLE = """
    QDoubleSpinBox {
        background-color: #2B2B2B; color: #D1D1D1;
        border: 1px solid #464646; border-radius: 4px;
        padding: 2px 6px; min-height: 24px;
    }
    QDoubleSpinBox:focus { border-color: #2B6CB6; }
"""

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

_CHECKBOX_STYLE = """
    QCheckBox {
        color: #D1D1D1; spacing: 6px;
    }
    QCheckBox::indicator {
        width: 16px; height: 16px;
        border: 1px solid #464646; border-radius: 3px;
        background-color: #2B2B2B;
    }
    QCheckBox::indicator:checked {
        background-color: #2B6CB6; border-color: #2B6CB6;
    }
"""

_BTN_RESET_STYLE = """
    QPushButton {
        background-color: transparent; color: #D1D1D1;
        border: 1px solid #464646; border-radius: 4px;
        padding: 4px 12px; min-height: 24px;
    }
    QPushButton:hover { border-color: #2B6CB6; color: white; }
"""


class _Label(QLabel):
    def __init__(self, text: str, font: QFont) -> None:
        super().__init__(text)
        self.setFont(font)
        self.setStyleSheet(f"color: {_LABEL_COLOR};")


class QtEnemyPanel(QWidget):
    """敌方参数面板。

    插件敌人下拉 + 防御/抗性/无视抗性/失衡易伤/失衡状态微调。
    切换插件敌人时自动填入对应参数，用户可手动覆盖。

    信号：
        enemy_params_changed: 任一参数变更时发射 dict
    """

    enemy_params_changed = Signal(dict)

    def __init__(self, font: QFont, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._font = font
        self._id_by_label: dict[str, str] = {}

        self._build_ui()
        self._connect_signals()
        self._populate_enemy_combo()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # -- 插件敌人下拉 --
        layout.addWidget(_Label("插件敌人", self._font))
        self._enemy_combo = QComboBox()
        self._enemy_combo.setStyleSheet(_COMBO_STYLE)
        layout.addWidget(self._enemy_combo)

        # -- 防御力 --
        layout.addWidget(_Label("防御力", self._font))
        self._defense_spin = QDoubleSpinBox()
        self._defense_spin.setStyleSheet(_SPINBOX_STYLE)
        self._defense_spin.setRange(0, 99999)
        self._defense_spin.setDecimals(0)
        self._defense_spin.setValue(DEFAULT_ENEMY_DEFENSE)
        layout.addWidget(self._defense_spin)

        # -- 抗性 % --
        layout.addWidget(_Label("抗性 (%)", self._font))
        self._resistance_spin = QDoubleSpinBox()
        self._resistance_spin.setStyleSheet(_SPINBOX_STYLE)
        self._resistance_spin.setRange(-100, 100)
        self._resistance_spin.setDecimals(1)
        self._resistance_spin.setSuffix("%")
        self._resistance_spin.setValue(DEFAULT_ENEMY_RESISTANCE)
        layout.addWidget(self._resistance_spin)

        # -- 无视抗性 % --
        layout.addWidget(_Label("无视抗性 (%)", self._font))
        self._ignore_resistance_spin = QDoubleSpinBox()
        self._ignore_resistance_spin.setStyleSheet(_SPINBOX_STYLE)
        self._ignore_resistance_spin.setRange(-100, 100)
        self._ignore_resistance_spin.setDecimals(1)
        self._ignore_resistance_spin.setSuffix("%")
        self._ignore_resistance_spin.setValue(DEFAULT_IGNORE_RESISTANCE)
        layout.addWidget(self._ignore_resistance_spin)

        # -- 失衡易伤系数 --
        layout.addWidget(_Label("失衡易伤系数", self._font))
        self._imbalance_spin = QDoubleSpinBox()
        self._imbalance_spin.setStyleSheet(_SPINBOX_STYLE)
        self._imbalance_spin.setRange(0.1, 10.0)
        self._imbalance_spin.setDecimals(2)
        self._imbalance_spin.setSingleStep(0.05)
        self._imbalance_spin.setValue(DEFAULT_IMBALANCE_VULNERABILITY)
        layout.addWidget(self._imbalance_spin)

        # -- 失衡状态 --
        self._unbalanced_cb = QCheckBox("失衡状态（启用失衡易伤乘区）")
        self._unbalanced_cb.setFont(self._font)
        self._unbalanced_cb.setStyleSheet(_CHECKBOX_STYLE)
        self._unbalanced_cb.setChecked(DEFAULT_IS_UNBALANCED)
        layout.addWidget(self._unbalanced_cb)

        layout.addWidget(_Label("敌人等阶", self._font))
        self._tier_combo = QComboBox()
        self._tier_combo.setStyleSheet(_COMBO_STYLE)
        self._tier_combo.addItems(list(ENEMY_TIERS))
        layout.addWidget(self._tier_combo)

        layout.addWidget(_Label("连击层数 (0=不用层数表)", self._font))
        self._combo_spin = QSpinBox()
        self._combo_spin.setRange(0, 4)
        self._combo_spin.setValue(DEFAULT_COMBO_STACKS)
        layout.addWidget(self._combo_spin)

        layout.addWidget(_Label("附带效果倍率 (潜能等)", self._font))
        self._attached_mult_spin = QDoubleSpinBox()
        self._attached_mult_spin.setStyleSheet(_SPINBOX_STYLE)
        self._attached_mult_spin.setRange(0.1, 3.0)
        self._attached_mult_spin.setDecimals(2)
        self._attached_mult_spin.setSingleStep(0.05)
        self._attached_mult_spin.setValue(DEFAULT_ATTACHED_EFFECT_MULTIPLIER)
        layout.addWidget(self._attached_mult_spin)

        layout.addWidget(_Label("腐蚀计时 (秒)", self._font))
        self._corrosion_spin = QDoubleSpinBox()
        self._corrosion_spin.setStyleSheet(_SPINBOX_STYLE)
        self._corrosion_spin.setRange(0.0, 15.0)
        self._corrosion_spin.setDecimals(1)
        self._corrosion_spin.setValue(DEFAULT_CORROSION_DURATION_SEC)
        layout.addWidget(self._corrosion_spin)

        layout.addWidget(_Label("失衡效率加成", self._font))
        self._imbalance_eff_spin = QDoubleSpinBox()
        self._imbalance_eff_spin.setStyleSheet(_SPINBOX_STYLE)
        self._imbalance_eff_spin.setRange(0.0, 1.0)
        self._imbalance_eff_spin.setDecimals(2)
        self._imbalance_eff_spin.setSingleStep(0.05)
        self._imbalance_eff_spin.setValue(DEFAULT_IMBALANCE_EFFICIENCY_BONUS)
        layout.addWidget(self._imbalance_eff_spin)

        # -- 重置按钮 --
        reset_row = QHBoxLayout()
        reset_row.setContentsMargins(0, 4, 0, 0)
        self._reset_btn = QPushButton("恢复默认")
        self._reset_btn.setFont(self._font)
        self._reset_btn.setStyleSheet(_BTN_RESET_STYLE)
        reset_row.addStretch()
        reset_row.addWidget(self._reset_btn)
        layout.addLayout(reset_row)

    def _connect_signals(self) -> None:
        self._enemy_combo.currentTextChanged.connect(self._on_enemy_combo_changed)
        self._defense_spin.valueChanged.connect(self._emit_params)
        self._resistance_spin.valueChanged.connect(self._emit_params)
        self._ignore_resistance_spin.valueChanged.connect(self._emit_params)
        self._imbalance_spin.valueChanged.connect(self._emit_params)
        self._unbalanced_cb.toggled.connect(self._emit_params)
        self._tier_combo.currentTextChanged.connect(self._emit_params)
        self._combo_spin.valueChanged.connect(self._emit_params)
        self._attached_mult_spin.valueChanged.connect(self._emit_params)
        self._corrosion_spin.valueChanged.connect(self._emit_params)
        self._imbalance_eff_spin.valueChanged.connect(self._emit_params)
        self._reset_btn.clicked.connect(self._reset_to_default)

    def _populate_enemy_combo(self) -> None:
        choices = list_plugin_enemy_choices()
        labels: list[str] = []
        for label, eid in choices:
            labels.append(label)
            self._id_by_label[label] = eid
        self._enemy_combo.clear()
        self._enemy_combo.addItems(labels)

    def _on_enemy_combo_changed(self, text: str) -> None:
        eid = self._id_by_label.get(text, "")
        self._defense_spin.setValue(resolve_enemy_defense(eid))
        self._resistance_spin.setValue(resolve_enemy_resistance(eid))
        self._ignore_resistance_spin.setValue(resolve_ignore_resistance(eid))
        self._imbalance_spin.setValue(resolve_imbalance_vulnerability(eid))
        self._unbalanced_cb.setChecked(resolve_is_unbalanced(eid))
        tier = resolve_enemy_tier(eid)
        idx = self._tier_combo.findText(tier)
        if idx >= 0:
            self._tier_combo.setCurrentIndex(idx)
        self._emit_params()

    def _emit_params(self) -> None:
        self.enemy_params_changed.emit(self.get_params())

    def _reset_to_default(self) -> None:
        self._defense_spin.setValue(DEFAULT_ENEMY_DEFENSE)
        self._resistance_spin.setValue(DEFAULT_ENEMY_RESISTANCE)
        self._ignore_resistance_spin.setValue(DEFAULT_IGNORE_RESISTANCE)
        self._imbalance_spin.setValue(DEFAULT_IMBALANCE_VULNERABILITY)
        self._unbalanced_cb.setChecked(DEFAULT_IS_UNBALANCED)
        self._tier_combo.setCurrentText(DEFAULT_ENEMY_TIER)
        self._combo_spin.setValue(DEFAULT_COMBO_STACKS)
        self._attached_mult_spin.setValue(DEFAULT_ATTACHED_EFFECT_MULTIPLIER)
        self._corrosion_spin.setValue(DEFAULT_CORROSION_DURATION_SEC)
        self._imbalance_eff_spin.setValue(DEFAULT_IMBALANCE_EFFICIENCY_BONUS)

    def get_params(self) -> dict[str, Any]:
        return {
            "enemy_defense": float(self._defense_spin.value()),
            "enemy_resistance": float(self._resistance_spin.value()),
            "ignore_resistance": float(self._ignore_resistance_spin.value()),
            "imbalance_vulnerability_coeff": float(self._imbalance_spin.value()),
            "is_unbalanced": bool(self._unbalanced_cb.isChecked()),
            "enemy_tier": str(self._tier_combo.currentText()),
            "combo_stacks": int(self._combo_spin.value()),
            "attached_effect_multiplier": float(self._attached_mult_spin.value()),
            "corrosion_duration_seconds": float(self._corrosion_spin.value()),
            "imbalance_efficiency_bonus": float(self._imbalance_eff_spin.value()),
        }

    def set_params(self, params: dict[str, Any]) -> None:
        if "enemy_defense" in params:
            self._defense_spin.setValue(float(params["enemy_defense"]))
        if "enemy_resistance" in params:
            self._resistance_spin.setValue(float(params["enemy_resistance"]))
        if "ignore_resistance" in params:
            self._ignore_resistance_spin.setValue(float(params["ignore_resistance"]))
        if "imbalance_vulnerability_coeff" in params:
            self._imbalance_spin.setValue(float(params["imbalance_vulnerability_coeff"]))
        if "is_unbalanced" in params:
            self._unbalanced_cb.setChecked(bool(params["is_unbalanced"]))
        if "enemy_tier" in params:
            idx = self._tier_combo.findText(str(params["enemy_tier"]))
            if idx >= 0:
                self._tier_combo.setCurrentIndex(idx)
        if "combo_stacks" in params:
            self._combo_spin.setValue(max(0, min(4, int(params["combo_stacks"]))))
        if "attached_effect_multiplier" in params:
            self._attached_mult_spin.setValue(float(params["attached_effect_multiplier"]))
        if "corrosion_duration_seconds" in params:
            self._corrosion_spin.setValue(float(params["corrosion_duration_seconds"]))
        if "imbalance_efficiency_bonus" in params:
            self._imbalance_eff_spin.setValue(float(params["imbalance_efficiency_bonus"]))

    def current_enemy_id(self) -> str:
        return self._id_by_label.get(self._enemy_combo.currentText(), "")

    def set_enemy_combo_index(self, index: int) -> None:
        if 0 <= index < self._enemy_combo.count():
            self._enemy_combo.setCurrentIndex(index)
