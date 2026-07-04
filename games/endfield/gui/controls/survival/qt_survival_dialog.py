#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""处决/治疗估算对话框。"""

from __future__ import annotations

from typing import Any

from calc_framework.ui.i18n import tr
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QMessageBox,
    QVBoxLayout,
)

# 计算逻辑已提取到 survival_estimator.py（无 PySide6 依赖）
from .survival_estimator import (
    estimate_burn,
    estimate_execute,
    estimate_healing,
    estimate_imbalance,
    estimate_resources,
)

_DASH = "—"


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
        imbalance_efficiency_bonus: float = 0.0,
        enemy_max_hp: float | None = None,
        weapon_skill_kwargs: dict[str, Any] | None = None,
        big_font: QFont | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(tr("desktop.endfield.survivalEstimate"))
        self.setMinimumWidth(420)
        font = big_font or QFont()

        layout = QVBoxLayout(self)

        exec_box = QGroupBox(tr("desktop.endfield.survivalExecGroup"))
        exec_form = QFormLayout(exec_box)
        self._exec_result = QLabel(_DASH)
        self._exec_result.setFont(font)
        self._exec_sp = QLabel(_DASH)
        exec_form.addRow(tr("desktop.endfield.survivalExecDamage"), self._exec_result)
        exec_form.addRow(tr("desktop.endfield.survivalExecSpRestore"), self._exec_sp)
        layout.addWidget(exec_box)

        imb_box = QGroupBox(tr("desktop.endfield.survivalImbGroup"))
        imb_form = QFormLayout(imb_box)
        self._imb_cap = QLabel(_DASH)
        self._imb_duration = QLabel(_DASH)
        self._imb_nodes = QLabel(_DASH)
        imb_form.addRow(tr("desktop.endfield.survivalImbCap"), self._imb_cap)
        imb_form.addRow(tr("desktop.endfield.survivalImbDuration"), self._imb_duration)
        imb_form.addRow(tr("desktop.endfield.survivalImbNodes"), self._imb_nodes)
        self._imb_gain_base = QDoubleSpinBox()
        self._imb_gain_base.setRange(0.0, 999.0)
        self._imb_gain_base.setValue(10.0)
        self._imb_gain_eff = QDoubleSpinBox()
        self._imb_gain_eff.setRange(0.0, 2.0)
        self._imb_gain_eff.setDecimals(2)
        self._imb_gain_eff.setValue(0.0)
        self._imb_gain_result = QLabel(_DASH)
        self._fast_break_mult = QLabel(_DASH)
        imb_form.addRow(tr("desktop.endfield.survivalImbGainBase"), self._imb_gain_base)
        imb_form.addRow(tr("desktop.endfield.survivalImbEffBonus"), self._imb_gain_eff)
        imb_form.addRow(tr("desktop.endfield.survivalImbGainResult"), self._imb_gain_result)
        imb_form.addRow(tr("desktop.endfield.survivalFastBreakMult"), self._fast_break_mult)
        layout.addWidget(imb_box)

        burn_box = QGroupBox(tr("desktop.endfield.survivalBurnGroup"))
        burn_form = QFormLayout(burn_box)
        self._enemy_max_hp = QDoubleSpinBox()
        self._enemy_max_hp.setRange(0.0, 999999.0)
        self._enemy_max_hp.setValue(6605.0)
        self._hot_resist = QDoubleSpinBox()
        self._hot_resist.setRange(-100.0, 100.0)
        self._hot_resist.setDecimals(1)
        self._hot_resist.setSuffix("%")
        self._burn_tick = QLabel(_DASH)
        burn_form.addRow(tr("desktop.endfield.survivalEnemyMaxHp"), self._enemy_max_hp)
        burn_form.addRow(tr("desktop.endfield.survivalHotResist"), self._hot_resist)
        burn_form.addRow(tr("desktop.endfield.survivalBurnTick"), self._burn_tick)
        layout.addWidget(burn_box)

        res_box = QGroupBox(tr("desktop.endfield.survivalResourceGroup"))
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
        self._sp_result = QLabel(_DASH)
        self._ult_result = QLabel(_DASH)
        res_form.addRow(tr("desktop.endfield.survivalSpStart"), self._sp_start)
        res_form.addRow(tr("desktop.endfield.survivalSpRegenSec"), self._sp_seconds)
        res_form.addRow(tr("desktop.endfield.survivalSpAfter"), self._sp_result)
        res_form.addRow(tr("desktop.endfield.survivalUltStart"), self._ult_start)
        res_form.addRow(tr("desktop.endfield.survivalUltAfter"), self._ult_result)
        layout.addWidget(res_box)

        steal_box = QGroupBox(tr("desktop.endfield.survivalStealGroup"))
        steal_form = QFormLayout(steal_box)
        self._steal_rate = QDoubleSpinBox()
        self._steal_rate.setRange(0.0, 1.0)
        self._steal_rate.setDecimals(3)
        self._steal_rate.setSingleStep(0.01)
        self._steal_rate.setValue(0.10)
        self._steal_result = QLabel(_DASH)
        steal_form.addRow(tr("desktop.endfield.survivalStealRate"), self._steal_rate)
        steal_form.addRow(tr("desktop.endfield.survivalStealHeal"), self._steal_result)
        layout.addWidget(steal_box)

        heal_box = QGroupBox(tr("desktop.endfield.survivalHealGroup"))
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
        self._heal_result = QLabel(_DASH)
        self._heal_result.setFont(font)
        heal_form.addRow(tr("desktop.endfield.survivalHealBase"), self._base_heal)
        heal_form.addRow(tr("desktop.endfield.survivalHealPerWill"), self._stat_per)
        heal_form.addRow(tr("desktop.endfield.survivalWill"), self._will)
        heal_form.addRow(tr("desktop.endfield.survivalHealEff"), self._heal_eff)
        heal_form.addRow(tr("desktop.endfield.survivalIndepHeal"), self._indep_heal)
        heal_form.addRow(tr("desktop.endfield.survivalHealAmount"), self._heal_result)
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
            self._imb_gain_base,
            self._imb_gain_eff,
            self._enemy_max_hp,
            self._hot_resist,
        ):
            spin.valueChanged.connect(self._refresh_all)
        layout.addWidget(QLabel(tr("desktop.endfield.survivalFooterHint"), self))

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
        self._imbalance_efficiency_bonus = float(imbalance_efficiency_bonus)
        if enemy_max_hp is not None and float(enemy_max_hp) > 0:
            self._enemy_max_hp.setValue(float(enemy_max_hp))
        self._imb_gain_eff.setValue(float(imbalance_efficiency_bonus))
        self._weapon_skill_kwargs = dict(weapon_skill_kwargs or {})
        self._last_execute_damage = 0.0
        self._refresh_all()

    def _refresh_all(self) -> None:
        self._refresh_imbalance_info()
        self._refresh_burn()
        self._refresh_execute()
        self._refresh_resources()
        self._refresh_healing()

    def _refresh_resources(self) -> None:
        res = estimate_resources(
            sp_start=float(self._sp_start.value()),
            sp_seconds=float(self._sp_seconds.value()),
            ult_start=float(self._ult_start.value()),
            execute_damage=self._last_execute_damage,
            life_steal_rate=float(self._steal_rate.value()),
        )
        self._sp_result.setText(
            tr(
                "desktop.endfield.survivalSpResultFmt",
                sp=f"{res.sp_after:,.1f}",
                rate=f"{res.sp_rate:g}",
            )
        )
        self._ult_result.setText(
            tr(
                "desktop.endfield.survivalUltResultFmt",
                ult=f"{res.ult_after:,.1f}",
                charge=f"{res.ult_charge:g}",
                dodge=f"{res.dodge_gain:g}",
            )
        )
        self._steal_result.setText(f"{res.life_steal_heal:,.1f}")

    def _refresh_imbalance_info(self) -> None:
        imb = estimate_imbalance(
            enemy_tier=self._enemy_tier,
            gain_base=float(self._imb_gain_base.value()),
            gain_efficiency=float(self._imb_gain_eff.value()),
        )
        self._imb_cap.setText(f"{imb.cap:g}")
        self._imb_duration.setText(f"{imb.duration:g}")
        node_text = tr(
            "desktop.endfield.survivalImbNode1Fmt",
            values=", ".join(f"{v:g}" for v in imb.nodes_1),
        )
        if len(imb.nodes_2) > 1:
            node_text += "；" + tr(
                "desktop.endfield.survivalImbNode2Fmt",
                values=", ".join(f"{v:g}" for v in imb.nodes_2),
            )
        self._imb_nodes.setText(node_text)
        self._imb_gain_result.setText(
            tr(
                "desktop.endfield.survivalImbGainFmt",
                gain=f"{imb.gain:g}",
                cap=f"{imb.cap:g}",
                pct=f"{imb.gain_pct:.1f}",
            )
        )
        self._fast_break_mult.setText(tr("desktop.endfield.survivalFastBreakFmt", mult=f"{imb.fast_break_mult:g}"))

    def _refresh_burn(self) -> None:
        hp = float(self._enemy_max_hp.value())
        if hp <= 0:
            self._burn_tick.setText(_DASH)
            return
        tick = estimate_burn(hp, hot_resistance_percent=float(self._hot_resist.value()))
        self._burn_tick.setText(f"{tick:,.1f}")

    def _refresh_execute(self) -> None:
        result = estimate_execute(
            char_data=self._char_data,
            weapon_data=self._weapon_data,
            char_level=self._char_level,
            weapon_level=self._weapon_level,
            trust_level=self._trust_level,
            enemy_tier=self._enemy_tier,
            weapon_skill_kwargs=self._weapon_skill_kwargs,
        )
        self._last_execute_damage = result.damage
        self._exec_result.setText(
            tr(
                "desktop.endfield.survivalExecResultFmt",
                dmg=f"{result.damage:,.1f}",
                mult=f"{result.multiplier:.2f}",
            )
        )
        self._exec_sp.setText(str(result.sp_restore))
        self._refresh_resources()

    def _refresh_healing(self) -> None:
        result = estimate_healing(
            base_heal=float(self._base_heal.value()),
            stat_per_point=float(self._stat_per.value()),
            will=float(self._will.value()),
            char_data=self._char_data,
            char_level=self._char_level,
            heal_efficiency=float(self._heal_eff.value()),
            independent_heal_bonus=float(self._indep_heal.value()),
        )
        self._heal_result.setText(f"{result.heal_amount:,.1f}")


def open_survival_estimate_dialog(
    parent,
    *,
    char_data: dict[str, Any] | None,
    weapon_data: dict[str, Any] | None,
    char_level: int,
    weapon_level: int,
    trust_level: int,
    enemy_tier: str,
    imbalance_efficiency_bonus: float = 0.0,
    enemy_max_hp: float | None = None,
    weapon_skill_kwargs: dict[str, Any] | None = None,
    big_font: QFont | None = None,
) -> None:
    if not char_data or not weapon_data:
        QMessageBox.warning(
            parent,
            tr("desktop.endfield.survivalEstimate"),
            tr("desktop.endfield.survivalNeedCharWeapon"),
        )
        return
    dialog = QtSurvivalEstimateDialog(
        parent,
        char_data=char_data,
        weapon_data=weapon_data,
        char_level=char_level,
        weapon_level=weapon_level,
        trust_level=trust_level,
        enemy_tier=enemy_tier,
        imbalance_efficiency_bonus=imbalance_efficiency_bonus,
        enemy_max_hp=enemy_max_hp,
        weapon_skill_kwargs=weapon_skill_kwargs,
        big_font=big_font,
    )
    dialog.exec()
