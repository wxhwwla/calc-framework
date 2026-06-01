#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""处决/治疗估算对话框。"""

from __future__ import annotations

from typing import Any

from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QVBoxLayout,
)

from games.endfield.calc.character_stats import total_max_hp
from games.endfield.calc.damage.combat_resources import (
    DODGE_SP_GAIN,
    SP_NATURAL_REGEN_PER_SEC,
    ULTIMATE_CHARGE_PER_100_SP,
    estimate_ultimate_after_actions,
    sp_after_natural_regen,
)
from games.endfield.calc.damage.special_damage import life_steal_heal
from games.endfield.calc.damage.engine import DamageContext
from games.endfield.calc.damage.execute import calculate_execute_damage, execute_sp_restore
from games.endfield.calc.damage.healing import HealingContext, calculate_healing, received_heal_efficiency_from_will
from games.endfield.calc.damage.imbalance import (
    imbalance_cap_for_tier,
    imbalance_duration_for_tier,
    imbalance_node_thresholds,
)
from games.endfield.calc.multiplicative_zones.final_attack_zone import calculate_final_attack_with_details


class QtSurvivalEstimateDialog(QDialog):
    """基于当前配装估算处决伤害与治疗量。"""

    def __init__(
        self,
        parent,
        *,
        char_data: dict[str, Any],
        weapon_data: dict[str, Any],
        char_level: int,
        weapon_level: int,
        trust_level: int,
        enemy_tier: str,
        weapon_skill_kwargs: dict[str, Any] | None = None,
        big_font: QFont | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("处决 / 治疗估算")
        self.setMinimumWidth(420)
        font = big_font or QFont()

        layout = QVBoxLayout(self)

        exec_box = QGroupBox("处决（普攻 × 失衡易伤 × 等阶系数）")
        exec_form = QFormLayout(exec_box)
        self._exec_result = QLabel("—")
        self._exec_result.setFont(font)
        self._exec_sp = QLabel("—")
        exec_form.addRow("预估处决伤害", self._exec_result)
        exec_form.addRow("恢复技力", self._exec_sp)
        layout.addWidget(exec_box)

        imb_box = QGroupBox("失衡参考（按敌人等阶）")
        imb_form = QFormLayout(imb_box)
        self._imb_cap = QLabel("—")
        self._imb_duration = QLabel("—")
        self._imb_nodes = QLabel("—")
        imb_form.addRow("失衡上限", self._imb_cap)
        imb_form.addRow("失衡持续 (s)", self._imb_duration)
        imb_form.addRow("节点阈值", self._imb_nodes)
        layout.addWidget(imb_box)

        res_box = QGroupBox("技力 / 终结技（NGA 节选估算）")
        res_form = QFormLayout(res_box)
        self._sp_seconds = QDoubleSpinBox()
        self._sp_seconds.setRange(0.0, 60.0)
        self._sp_seconds.setValue(5.0)
        self._sp_start = QDoubleSpinBox()
        self._sp_start.setRange(0.0, 100.0)
        self._sp_start.setValue(0.0)
        self._ult_start = QDoubleSpinBox()
        self._ult_start.setRange(0.0, 100.0)
        self._ult_start.setValue(0.0)
        self._sp_result = QLabel("—")
        self._ult_result = QLabel("—")
        res_form.addRow("起始技力", self._sp_start)
        res_form.addRow("自然回能时长 (s)", self._sp_seconds)
        res_form.addRow("回能后技力", self._sp_result)
        res_form.addRow("起始终结充能", self._ult_start)
        res_form.addRow("终结充能（含闪避1次）", self._ult_result)
        layout.addWidget(res_box)

        steal_box = QGroupBox("生命汲取")
        steal_form = QFormLayout(steal_box)
        self._steal_rate = QDoubleSpinBox()
        self._steal_rate.setRange(0.0, 1.0)
        self._steal_rate.setDecimals(3)
        self._steal_rate.setSingleStep(0.01)
        self._steal_rate.setValue(0.10)
        self._steal_result = QLabel("—")
        steal_form.addRow("汲取率", self._steal_rate)
        steal_form.addRow("预估回复", self._steal_result)
        layout.addWidget(steal_box)

        heal_box = QGroupBox("治疗（三乘区）")
        heal_form = QFormLayout(heal_box)
        self._base_heal = QDoubleSpinBox()
        self._base_heal.setRange(0.0, 99999.0)
        self._base_heal.setValue(201.6)
        self._stat_per = QDoubleSpinBox()
        self._stat_per.setRange(0.0, 10.0)
        self._stat_per.setDecimals(3)
        self._stat_per.setValue(0.47)
        self._will = QDoubleSpinBox()
        self._will.setRange(0.0, 9999.0)
        self._will.setValue(400.0)
        self._heal_eff = QDoubleSpinBox()
        self._heal_eff.setRange(0.0, 2.0)
        self._heal_eff.setDecimals(3)
        self._heal_eff.setValue(0.20)
        self._indep_heal = QDoubleSpinBox()
        self._indep_heal.setRange(0.0, 2.0)
        self._indep_heal.setDecimals(3)
        self._indep_heal.setValue(0.30)
        self._heal_result = QLabel("—")
        self._heal_result.setFont(font)
        heal_form.addRow("治疗基础值", self._base_heal)
        heal_form.addRow("每点意志+", self._stat_per)
        heal_form.addRow("意志", self._will)
        heal_form.addRow("治疗效率", self._heal_eff)
        heal_form.addRow("独立治疗加成", self._indep_heal)
        heal_form.addRow("治疗量", self._heal_result)
        layout.addWidget(heal_box)

        for spin in (
            self._base_heal,
            self._stat_per,
            self._will,
            self._heal_eff,
            self._indep_heal,
            self._sp_seconds,
            self._sp_start,
            self._ult_start,
            self._steal_rate,
        ):
            spin.valueChanged.connect(self._refresh_all)
        layout.addWidget(
            QLabel("处决按当前角色/武器面板；治疗/技力参数可手动调整。", self)
        )

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)

        self._char_data = char_data
        self._weapon_data = weapon_data
        self._char_level = char_level
        self._weapon_level = weapon_level
        self._trust_level = trust_level
        self._enemy_tier = enemy_tier
        self._weapon_skill_kwargs = dict(weapon_skill_kwargs or {})
        self._last_execute_damage = 0.0
        self._refresh_all()

    def _refresh_all(self) -> None:
        self._refresh_imbalance_info()
        self._refresh_execute()
        self._refresh_resources()
        self._refresh_healing()

    def _refresh_resources(self) -> None:
        sp = sp_after_natural_regen(float(self._sp_start.value()), float(self._sp_seconds.value()))
        sp_gain = max(0.0, sp - float(self._sp_start.value()))
        ult = estimate_ultimate_after_actions(
            float(self._ult_start.value()),
            sp_gains=(sp_gain, DODGE_SP_GAIN),
        )
        self._sp_result.setText(f"{sp:,.1f}（{SP_NATURAL_REGEN_PER_SEC:g}/s）")
        self._ult_result.setText(
            f"{ult:,.1f}（{ULTIMATE_CHARGE_PER_100_SP:g}/100 技力 + 闪避 {DODGE_SP_GAIN:g}）"
        )
        heal = life_steal_heal(self._last_execute_damage, life_steal_rate=float(self._steal_rate.value()))
        self._steal_result.setText(f"{heal:,.1f}")

    def _refresh_imbalance_info(self) -> None:
        cap = imbalance_cap_for_tier(self._enemy_tier)
        duration = imbalance_duration_for_tier(self._enemy_tier)
        nodes_1 = imbalance_node_thresholds(cap, 1)
        nodes_2 = imbalance_node_thresholds(cap, 2)
        self._imb_cap.setText(f"{cap:g}")
        self._imb_duration.setText(f"{duration:g}")
        node_text = f"1 节点: {', '.join(f'{v:g}' for v in nodes_1)}"
        if len(nodes_2) > 1:
            node_text += f"；2 节点: {', '.join(f'{v:g}' for v in nodes_2)}"
        self._imb_nodes.setText(node_text)

    def _refresh_execute(self) -> None:
        details = calculate_final_attack_with_details(
            self._char_data,
            self._weapon_data,
            level=self._char_level,
            weapon_level=self._weapon_level,
            trust_level=self._trust_level,
            **self._weapon_skill_kwargs,
        )
        ctx = DamageContext(
            final_attack=float(details["final_attack"]),
            skill_multiplier=1.0,
            damage_type="物理",
            skill_type="普通攻击",
            is_unbalanced=True,
        )
        dmg, mult = calculate_execute_damage(
            context=ctx,
            normal_attack_multiplier=1.0,
            enemy_tier=self._enemy_tier,
        )
        sp = execute_sp_restore(self._enemy_tier)
        self._last_execute_damage = float(dmg)
        self._exec_result.setText(f"{dmg:,.1f}（承伤×{mult:.2f}）")
        self._exec_sp.setText(str(sp))
        self._refresh_resources()

    def _refresh_healing(self) -> None:
        will = float(self._will.value())
        strength = float(self._char_data.get("力量", [0.0])[min(self._char_level - 1, 89)])
        hp = total_max_hp(strength, level=self._char_level)
        out = calculate_healing(
            HealingContext(
                base_heal_flat=float(self._base_heal.value()),
                stat_per_point=float(self._stat_per.value()),
                stat_value=will,
                max_hp=hp,
                heal_efficiency=float(self._heal_eff.value()),
                received_heal_efficiency=received_heal_efficiency_from_will(will),
                independent_heal_bonus=float(self._indep_heal.value()),
            )
        )
        self._heal_result.setText(f"{out['治疗量']:,.1f}")


def open_survival_estimate_dialog(
    parent,
    *,
    char_data: dict[str, Any] | None,
    weapon_data: dict[str, Any] | None,
    char_level: int,
    weapon_level: int,
    trust_level: int,
    enemy_tier: str,
    weapon_skill_kwargs: dict[str, Any] | None = None,
    big_font: QFont | None = None,
) -> None:
    if not char_data or not weapon_data:
        from PySide6.QtWidgets import QMessageBox

        QMessageBox.warning(parent, "处决/治疗估算", "请先选择角色与武器。")
        return
    dialog = QtSurvivalEstimateDialog(
        parent,
        char_data=char_data,
        weapon_data=weapon_data,
        char_level=char_level,
        weapon_level=weapon_level,
        trust_level=trust_level,
        enemy_tier=enemy_tier,
        weapon_skill_kwargs=weapon_skill_kwargs,
        big_font=big_font,
    )
    dialog.exec()
