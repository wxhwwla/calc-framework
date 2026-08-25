# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""数据录入页签 — 角色/武器表单式录入，无需写代码。"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from calc_framework.ui.i18n import tr
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

# path setup

_REPO = Path(__file__).resolve().parents[2]

_GAMES = _REPO / "games" / "endfield"

if str(_GAMES) not in sys.path:
    sys.path.insert(0, str(_GAMES))

if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))


from tools.endfield_scripts.add_character import add_character
from tools.endfield_scripts.add_weapon import add_weapon

_LABEL = "color: #CCCCCC;"

_BTN = """

    QPushButton { background-color: #2B6CB6; color: white;

                  border: none; border-radius: 6px; padding: 8px 24px;

                  font-size: 13px; font-weight: bold; }

    QPushButton:hover { background-color: #3182CE; }

"""

_BTN_RESET = """

    QPushButton { background-color: transparent; color: #D1D1D1;

                  border: 1px solid #464646; border-radius: 6px;

                  padding: 6px 16px; }

    QPushButton:hover { border-color: #E53E3E; color: #E53E3E; }

"""

_INPUT = """

    QLineEdit { background-color: #2B2B2B; color: #D1D1D1;

                border: 1px solid #464646; border-radius: 4px;

                padding: 4px 8px; min-height: 24px; }

    QLineEdit:focus { border-color: #2B6CB6; }

    QDoubleSpinBox, QSpinBox { background-color: #2B2B2B; color: #D1D1D1;

                border: 1px solid #464646; border-radius: 4px;

                padding: 2px 6px; min-height: 24px; }

    QDoubleSpinBox:focus, QSpinBox:focus { border-color: #2B6CB6; }

    QComboBox { background-color: #2B2B2B; color: #D1D1D1;

                border: 1px solid #464646; border-radius: 4px;

                padding: 2px 8px; min-height: 28px; }

    QComboBox:hover { border-color: #2B6CB6; }

    QComboBox QAbstractItemView {

                background-color: #2B2B2B; color: #D1D1D1;

                selection-background-color: #2B6CB6; }

    QCheckBox { color: #D1D1D1; }

    QGroupBox { color: #FF6B6B; font-weight: bold;

                border: 1px solid #464646; border-radius: 6px;

                margin-top: 12px; padding-top: 16px; }

    QGroupBox::title { subcontrol-origin: margin;

                left: 10px; padding: 0 6px; }

"""


class _FormulaGroup(QGroupBox):
    """公式参数组：base / growth / divisor / offset。"""

    def __init__(self, title: str, parent: QWidget | None = None):
        super().__init__(title, parent)

        self.setStyleSheet(_INPUT)

        layout = QFormLayout(self)

        self.base = QDoubleSpinBox()

        self.base.setRange(-99999, 99999)

        self.base.setDecimals(2)

        layout.addRow("Base:", self.base)

        self.growth = QDoubleSpinBox()

        self.growth.setRange(-99999, 99999)

        self.growth.setDecimals(2)

        layout.addRow("Growth:", self.growth)

        self.divisor = QSpinBox()

        self.divisor.setRange(1, 9999)

        self.divisor.setValue(1)

        layout.addRow("Divisor:", self.divisor)

        self.offset = QDoubleSpinBox()

        self.offset.setRange(-99999, 99999)

        self.offset.setDecimals(2)

        layout.addRow("Offset:", self.offset)

    def set_values(self, *, base=0, growth=0, divisor=1, offset=0):
        """set_values 实现。"""
        self.base.setValue(base)

        self.growth.setValue(growth)

        self.divisor.setValue(divisor)

        self.offset.setValue(offset)

    def values(self) -> dict[str, float | int]:
        """values 实现。"""
        return {
            "base": self.base.value(),
            "growth": self.growth.value(),
            "divisor": self.divisor.value(),
            "offset": self.offset.value(),
        }


class _CharSeedTab(QWidget):
    """角色录入表单。"""

    def __init__(self, big_font: QFont, small_font: QFont):
        super().__init__()

        self._big = big_font

        self._small = small_font

        self._build_ui()

    def _label(self, text: str) -> QLabel:
        """_label 实现。"""
        lbl = QLabel(text)

        lbl.setStyleSheet(_LABEL)

        return lbl

    def _build_ui(self) -> None:
        """_build_ui 实现。"""
        scroll = QScrollArea()

        scroll.setWidgetResizable(True)

        scroll.setStyleSheet("QScrollArea { border: none; }")

        inner = QWidget()

        layout = QVBoxLayout(inner)

        layout.setSpacing(8)

        header = QLabel(tr("desktop.designer.seedCharHeader"))

        header.setFont(self._big)

        header.setStyleSheet("color: #FF6B6B; padding: 4px 0;")

        layout.addWidget(header)

        form = QFormLayout()

        form.setSpacing(6)

        self._name = QLineEdit()

        self._name.setPlaceholderText(tr("desktop.designer.seedCharNamePh"))

        form.addRow(self._label(tr("desktop.designer.fieldName")), self._name)

        self._char_type = QComboBox()

        self._char_type.addItems(["近卫", "突击", "重装", "术师", "辅助", "先锋", "特种"])

        form.addRow(self._label(tr("desktop.designer.fieldType")), self._char_type)

        self._star = QSpinBox()

        self._star.setRange(3, 6)

        self._star.setValue(6)

        form.addRow(self._label(tr("desktop.designer.fieldStar")), self._star)

        self._weapon = QComboBox()

        self._weapon.addItems(["单手剑", "双手剑", "长柄武器", "手铳", "施术单元"])

        form.addRow(self._label(tr("desktop.designer.fieldWeapon")), self._weapon)

        self._primary = QComboBox()

        self._primary.addItems(["敏捷", "力量", "智识", "意志"])

        form.addRow(self._label(tr("desktop.designer.fieldPrimary")), self._primary)

        self._secondary = QComboBox()

        self._secondary.addItems(["敏捷", "力量", "智识", "意志"])

        form.addRow(self._label(tr("desktop.designer.fieldSecondary")), self._secondary)

        layout.addLayout(form)

        attr_group = QGroupBox(tr("desktop.designer.attrGrowthGroup"))

        attr_group.setStyleSheet(_INPUT)

        attr_form = QFormLayout(attr_group)

        self._strength = _FormulaGroup(tr("desktop.designer.attrStrength"))

        attr_form.addRow(self._strength)

        self._agility = _FormulaGroup(tr("desktop.designer.attrAgility"))

        attr_form.addRow(self._agility)

        self._intellect = _FormulaGroup(tr("desktop.designer.attrIntellect"))

        attr_form.addRow(self._intellect)

        self._will = _FormulaGroup(tr("desktop.designer.attrWill"))

        attr_form.addRow(self._will)

        self._base_atk = _FormulaGroup(tr("desktop.designer.attrBaseAtk"))

        attr_form.addRow(self._base_atk)

        layout.addWidget(attr_group)

        skill_group = QGroupBox(tr("desktop.designer.skillParamsGroup"))

        skill_group.setStyleSheet(_INPUT)

        skill_form = QFormLayout(skill_group)

        self._sk1 = QLineEdit()

        self._sk1.setPlaceholderText(
            '[{"base": 156, "growth": 78, "divisor": 5, "offset": 0, "special": [300,323,350]}]'
        )

        skill_form.addRow(self._label(tr("desktop.designer.skill1")), self._sk1)

        self._sk2 = QLineEdit()

        self._sk2.setPlaceholderText(tr("desktop.designer.skillSameFormatPh"))

        skill_form.addRow(self._label(tr("desktop.designer.skill2")), self._sk2)

        self._sk3 = QLineEdit()

        self._sk3.setPlaceholderText(tr("desktop.designer.skillSameFormatPh"))

        skill_form.addRow(self._label(tr("desktop.designer.skill3")), self._sk3)

        layout.addWidget(skill_group)

        btn_row = QHBoxLayout()

        self._save_btn = QPushButton(tr("desktop.designer.saveToFile"))

        self._save_btn.setStyleSheet(_BTN)

        self._save_btn.clicked.connect(self._save)

        btn_row.addWidget(self._save_btn)

        self._reset_btn = QPushButton(tr("desktop.designer.clearForm"))

        self._reset_btn.setStyleSheet(_BTN_RESET)

        self._reset_btn.clicked.connect(self._clear)

        btn_row.addWidget(self._reset_btn)

        btn_row.addStretch()

        layout.addLayout(btn_row)

        layout.addStretch()

        scroll.setWidget(inner)

        main_layout = QVBoxLayout(self)

        main_layout.addWidget(scroll)

    def _parse_skill_json(self, text: str) -> list:
        """_parse_skill_json 实现。"""
        text = text.strip()

        if not text:
            return []

        import json

        try:
            return json.loads(text)

        except json.JSONDecodeError:
            raise ValueError(tr("desktop.designer.skillJsonError", text=text))

    def _save(self) -> None:
        """_save 实现。"""
        name = self._name.text().strip()

        if not name:
            QMessageBox.warning(self, tr("desktop.designer.inputErrorTitle"), tr("desktop.designer.charNameRequired"))

            return

        try:
            char_type = self._char_type.currentText()

            star = self._star.value()

            weapon = self._weapon.currentText()

            primary = self._primary.currentText()

            secondary = self._secondary.currentText()

            strength = self._strength.values()

            agility = self._agility.values()

            intellect = self._intellect.values()

            will = self._will.values()

            base_atk = self._base_atk.values()

            sk1_raw = self._sk1.text().strip()

            sk2_raw = self._sk2.text().strip()

            sk3_raw = self._sk3.text().strip()

            sk1 = self._parse_skill_json(sk1_raw) if sk1_raw else []

            sk2 = self._parse_skill_json(sk2_raw) if sk2_raw else []

            sk3 = self._parse_skill_json(sk3_raw) if sk3_raw else []

            add_character(
                name=name,
                char_type=char_type,
                star=star,
                primary=primary,
                secondary=secondary,
                weapon=weapon,
                strength=strength,
                agility=agility,
                intellect=intellect,
                will=will,
                base_atk=base_atk,
                sk1=sk1,
                sk2=sk2,
                sk3=sk3,
            )

            QMessageBox.information(self, tr("common.success"), tr("desktop.designer.charSavedMsg", name=name))

            self._clear()

        except Exception as e:
            QMessageBox.critical(
                self, tr("desktop.designer.saveFailTitle"), tr("desktop.designer.errorWithDetail", error=e)
            )

    def _clear(self) -> None:
        """_clear 实现。"""
        self._name.clear()

        self._char_type.setCurrentIndex(0)

        self._star.setValue(6)

        self._weapon.setCurrentIndex(0)

        self._primary.setCurrentIndex(0)

        self._secondary.setCurrentIndex(1)

        for g in [self._strength, self._agility, self._intellect, self._will, self._base_atk]:
            g.set_values()

        self._sk1.clear()

        self._sk2.clear()

        self._sk3.clear()


class _WeaponSeedTab(QWidget):
    """武器录入表单。"""

    def __init__(self, big_font: QFont, small_font: QFont):
        super().__init__()

        self._big = big_font

        self._small = small_font

        self._build_ui()

    def _label(self, text: str) -> QLabel:
        """_label 实现。"""
        lbl = QLabel(text)

        lbl.setStyleSheet(_LABEL)

        return lbl

    def _build_ui(self) -> None:
        """_build_ui 实现。"""
        scroll = QScrollArea()

        scroll.setWidgetResizable(True)

        scroll.setStyleSheet("QScrollArea { border: none; }")

        inner = QWidget()

        layout = QVBoxLayout(inner)

        layout.setSpacing(8)

        header = QLabel(tr("desktop.designer.seedWeaponHeader"))

        header.setFont(self._big)

        header.setStyleSheet("color: #FF6B6B; padding: 4px 0;")

        layout.addWidget(header)

        form = QFormLayout()

        form.setSpacing(6)

        self._name = QLineEdit()

        self._name.setPlaceholderText(tr("desktop.designer.seedWeaponNamePh"))

        form.addRow(self._label(tr("desktop.designer.fieldName")), self._name)

        self._weapon_type = QComboBox()

        self._weapon_type.addItems(["单手剑", "双手剑", "长柄武器", "手铳", "施术单元"])

        form.addRow(self._label(tr("desktop.designer.fieldType")), self._weapon_type)

        self._star = QSpinBox()

        self._star.setRange(3, 6)

        self._star.setValue(6)

        form.addRow(self._label(tr("desktop.designer.fieldStar")), self._star)

        layout.addLayout(form)

        atk_group = QGroupBox(tr("desktop.designer.baseAtkGrowthGroup"))

        atk_group.setStyleSheet(_INPUT)

        atk_form = QFormLayout(atk_group)

        self._base_atk = _FormulaGroup(tr("desktop.designer.attrBaseAtk"))

        atk_form.addRow(self._base_atk)

        layout.addWidget(atk_group)

        bonus_group = QGroupBox(tr("desktop.designer.bonusAttrsGroup"))

        bonus_group.setStyleSheet(_INPUT)

        bonus_form = QFormLayout(bonus_group)

        self._bonus_attrs = QLineEdit()

        self._bonus_attrs.setPlaceholderText(
            '{"攻击力+": {"base": 5, "growth": 4, "divisor": 1, "offset": 0, "special": [39]}}'
        )

        bonus_form.addRow(self._label(tr("desktop.designer.attrList")), self._bonus_attrs)

        layout.addWidget(bonus_group)

        special_group = QGroupBox(tr("desktop.designer.specialAbilityGroup"))

        special_group.setStyleSheet(_INPUT)

        special_form = QFormLayout(special_group)

        self._special_enabled = QCheckBox(tr("desktop.designer.enableSpecial"))

        special_form.addRow(self._special_enabled)

        self._special_name = QLineEdit()

        self._special_name.setPlaceholderText(tr("desktop.designer.specialNamePh"))

        special_form.addRow(self._label(tr("desktop.designer.abilityName")), self._special_name)

        self._special_formula = _FormulaGroup(tr("desktop.designer.formulaParams"))

        special_form.addRow(self._special_formula)

        self._special_curve = QLineEdit()

        self._special_curve.setPlaceholderText(tr("desktop.designer.curveOptionalPh"))

        special_form.addRow(self._label(tr("desktop.designer.curveOptional")), self._special_curve)

        layout.addWidget(special_group)

        btn_row = QHBoxLayout()

        self._save_btn = QPushButton(tr("desktop.designer.saveToFile"))

        self._save_btn.setStyleSheet(_BTN)

        self._save_btn.clicked.connect(self._save)

        btn_row.addWidget(self._save_btn)

        self._reset_btn = QPushButton(tr("desktop.designer.clearForm"))

        self._reset_btn.setStyleSheet(_BTN_RESET)

        self._reset_btn.clicked.connect(self._clear)

        btn_row.addWidget(self._reset_btn)

        btn_row.addStretch()

        layout.addLayout(btn_row)

        layout.addStretch()

        scroll.setWidget(inner)

        main_layout = QVBoxLayout(self)

        main_layout.addWidget(scroll)

    def _parse_json(self, text: str) -> Any:
        """_parse_json 实现。"""
        text = text.strip()

        if not text:
            return None

        import json

        return json.loads(text)

    def _save(self) -> None:
        """_save 实现。"""
        name = self._name.text().strip()

        if not name:
            QMessageBox.warning(self, tr("desktop.designer.inputErrorTitle"), tr("desktop.designer.weaponNameRequired"))

            return

        try:
            weapon_type = self._weapon_type.currentText()

            star = self._star.value()

            base_atk = self._base_atk.values()

            bonus_raw = self._bonus_attrs.text().strip()

            bonus_attrs = self._parse_json(bonus_raw) if bonus_raw else None

            special_ability = None

            if self._special_enabled.isChecked():
                sname = self._special_name.text().strip()

                curve_raw = self._special_curve.text().strip()

                if curve_raw:
                    curve = self._parse_json(curve_raw)

                    special_ability = {"enabled": True, "name": sname, "curve": curve}

                else:
                    sv = self._special_formula.values()

                    special_ability = {"enabled": True, "name": sname, **sv}

            add_weapon(
                name=name,
                weapon_type=weapon_type,
                star=star,
                base_atk=base_atk,
                bonus_attrs=bonus_attrs,
                special_ability=special_ability,
            )

            QMessageBox.information(self, tr("common.success"), tr("desktop.designer.weaponSavedMsg", name=name))

            self._clear()

        except Exception as e:
            QMessageBox.critical(
                self, tr("desktop.designer.saveFailTitle"), tr("desktop.designer.errorWithDetail", error=e)
            )

    def _clear(self) -> None:
        """_clear 实现。"""
        self._name.clear()

        self._weapon_type.setCurrentIndex(0)

        self._star.setValue(6)

        self._base_atk.set_values()

        self._bonus_attrs.clear()

        self._special_enabled.setChecked(False)

        self._special_name.clear()

        self._special_formula.set_values()

        self._special_curve.clear()


class SeedTab(QWidget):
    """数据录入页签 — 角色和武器录入（含子页签）。"""

    def __init__(self, big_font: QFont, small_font: QFont):
        super().__init__()

        layout = QVBoxLayout(self)

        layout.setContentsMargins(0, 0, 0, 0)

        self._tabs = QTabWidget()

        self._tabs.addTab(_CharSeedTab(big_font, small_font), tr("desktop.designer.seedCharTab"))

        self._tabs.addTab(_WeaponSeedTab(big_font, small_font), tr("desktop.designer.seedWeaponTab"))

        layout.addWidget(self._tabs)
