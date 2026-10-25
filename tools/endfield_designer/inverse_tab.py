#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# SPDX-License-Identifier: AGPL-3.0
"""公式反推页签 — 从数值数据反向推导成长公式参数。"""

from __future__ import annotations

import re

from calc_framework.ui.i18n import tr
from PySide6.QtGui import QFont, QTextCursor
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from games.endfield.calc.damage.formula import calculate_growth_curve, calculate_skill_curve
from games.endfield.calc.damage.inverse import (
    fit_attribute_formula,
    fit_skill_formula,
    fit_skill_formula_no_special,
    remove_duplicates,
    validate_attribute_formula,
    validate_skill_formula,
)

_SECTION_STYLE = "color: #FF6B6B; padding: 4px 0;"

_LABEL_STYLE = "color: #CCCCCC;"

_HINT_STYLE = "color: #888888;"

_RESULT_STYLE = """

    QTextEdit { background-color: #1E1E1E; color: #D1D1D1;

                border: 1px solid #464646; border-radius: 4px;

                font-family: Consolas, monospace; font-size: 12px; }

"""

_INPUT_STYLE = """

    QTextEdit { background-color: #2B2B2B; color: #D1D1D1;

                border: 1px solid #464646; border-radius: 4px;

                font-family: Consolas, monospace; font-size: 12px; }

    QTextEdit:focus { border-color: #2B6CB6; }

"""

_BTN_STYLE = """

    QPushButton { background-color: transparent; color: #D1D1D1;

                  border: 1px solid #464646; border-radius: 6px;

                  padding: 6px 16px; }

    QPushButton:hover { border-color: #2B6CB6; color: white; }

"""

_BTN_PRIMARY_STYLE = """

    QPushButton { background-color: #2B6CB6; color: white;

                  border-radius: 6px; font-weight: bold;

                  padding: 6px 16px; }

    QPushButton:hover { background-color: #3182CE; }

"""

_COMBO_STYLE = """

    QComboBox { background-color: #2B2B2B; color: #D1D1D1;

                border: 1px solid #464646; border-radius: 4px;

                padding: 2px 8px; min-height: 28px; }

    QComboBox:hover { border-color: #2B6CB6; }

    QComboBox::drop-down { border-left: 1px solid #464646; width: 20px; }

    QComboBox QAbstractItemView {

        background-color: #2B2B2B; color: #D1D1D1;

        selection-background-color: #2B6CB6; border: 1px solid #464646; }

"""


class InverseTab(QWidget):
    """公式反推页签：输入数值数据，反推成长公式参数。"""

    def __init__(self, big_font: QFont, small_font: QFont) -> None:
        super().__init__()

        self._big = big_font

        self._small = small_font

        self._build_ui()

    def _build_ui(self) -> None:
        """_build_ui 实现。"""
        layout = QVBoxLayout(self)

        layout.setContentsMargins(12, 12, 12, 12)

        layout.setSpacing(8)

        header = QLabel(tr("desktop.designer.inverseToolTitle"))

        header.setFont(self._big)

        header.setStyleSheet(_SECTION_STYLE)

        layout.addWidget(header)

        mode_row = QHBoxLayout()

        mode_row.addWidget(self._make_label(tr("desktop.designer.dataKindLabel")))

        self._mode_combo = QComboBox()

        self._mode_combo.addItem(tr("desktop.designer.inverseModeAttr"), "attr")
        self._mode_combo.addItem(tr("desktop.designer.inverseModeSkill"), "skill")

        self._mode_combo.setStyleSheet(_COMBO_STYLE)

        self._mode_combo.currentIndexChanged.connect(self._update_hint)

        mode_row.addWidget(self._mode_combo)

        mode_row.addStretch()

        layout.addLayout(mode_row)

        self._hint_label = self._make_label("")

        self._hint_label.setStyleSheet(_HINT_STYLE)

        layout.addWidget(self._hint_label)

        self._input_edit = QTextEdit()

        self._input_edit.setStyleSheet(_INPUT_STYLE)

        self._input_edit.setPlaceholderText(tr("desktop.designer.inverseInputPlaceholder"))

        self._input_edit.setMinimumHeight(120)

        layout.addWidget(self._input_edit, stretch=1)

        btn_row = QHBoxLayout()

        self._clear_btn = QPushButton(tr("desktop.designer.clearInput"))

        self._clear_btn.setStyleSheet(_BTN_STYLE)

        self._clear_btn.clicked.connect(self._clear_input)

        btn_row.addWidget(self._clear_btn)

        self._sample_btn = QPushButton(tr("desktop.designer.sampleData"))

        self._sample_btn.setStyleSheet(_BTN_STYLE)

        self._sample_btn.clicked.connect(self._load_sample)

        btn_row.addWidget(self._sample_btn)

        self._dedup_btn = QPushButton(tr("desktop.designer.dedupe"))

        self._dedup_btn.setStyleSheet(_BTN_STYLE)

        self._dedup_btn.clicked.connect(self._handle_dedup)

        btn_row.addWidget(self._dedup_btn)

        btn_row2 = QHBoxLayout()

        self._calc_btn = QPushButton(tr("desktop.designer.inverseStart"))

        self._calc_btn.setStyleSheet(_BTN_PRIMARY_STYLE)

        self._calc_btn.clicked.connect(self._calculate)

        btn_row2.addWidget(self._calc_btn)

        self._validate_btn = QPushButton(tr("desktop.designer.validateFormula"))

        self._validate_btn.setStyleSheet(_BTN_STYLE)

        self._validate_btn.clicked.connect(self._validate)

        btn_row2.addWidget(self._validate_btn)

        self._curve_btn = QPushButton(tr("desktop.designer.generateCurve"))

        self._curve_btn.setStyleSheet(_BTN_STYLE)

        self._curve_btn.clicked.connect(self._generate_curve)

        btn_row2.addWidget(self._curve_btn)

        layout.addLayout(btn_row)

        layout.addLayout(btn_row2)

        result_header = QLabel(tr("desktop.designer.calcResult"))

        result_header.setStyleSheet(_SECTION_STYLE)

        layout.addWidget(result_header)

        self._result_edit = QTextEdit()

        self._result_edit.setStyleSheet(_RESULT_STYLE)

        self._result_edit.setReadOnly(True)

        self._result_edit.setMinimumHeight(180)

        layout.addWidget(self._result_edit, stretch=2)

        self._update_hint()

    def _make_label(self, text: str) -> QLabel:
        """_make_label 实现。"""
        lbl = QLabel(text)

        lbl.setFont(self._small)

        lbl.setStyleSheet(_LABEL_STYLE)

        return lbl

    def _is_attr_mode(self) -> bool:
        """当前是否为属性反推模式。"""
        return self._mode_combo.currentData() == "attr"

    def _update_hint(self) -> None:
        """_update_hint 实现。"""
        if self._is_attr_mode():
            self._hint_label.setText(tr("desktop.designer.inverseHintAttr"))

        else:
            self._hint_label.setText(tr("desktop.designer.inverseHintSkill"))

    def _clear_input(self) -> None:
        """_clear_input 实现。"""
        self._input_edit.clear()

        self._result_edit.clear()

    def _load_sample(self) -> None:
        """_load_sample 实现。"""
        self._input_edit.clear()

        if self._is_attr_mode():
            sample = "34 38 41 45 48 52 55 59 62 65 69 72 76 79 83 86 90 93 96 100"

        else:
            sample = "100 102 104 106 108 110 112 114 116 150 160 170"

        self._input_edit.setPlainText(sample)

    def _parse(self) -> list[float]:
        """_parse 实现。"""
        text = self._input_edit.toPlainText().strip()

        if not text:
            raise ValueError(tr("desktop.designer.needInputData"))

        tokens = re.split(r"[\s,，]+", text)

        tokens = [t.strip() for t in tokens if t.strip()]

        if not tokens:
            raise ValueError(tr("desktop.designer.noValidData"))

        result: list[float] = []

        for token in tokens:
            if token.endswith("%"):
                result.append(float(token[:-1]))

            else:
                result.append(float(token))

        return result

    def _show_result(self, text: str) -> None:
        """_show_result 实现。"""
        self._result_edit.setPlainText(text)

        cursor = self._result_edit.textCursor()

        cursor.movePosition(QTextCursor.MoveOperation.Start)

        self._result_edit.setTextCursor(cursor)

    def _handle_dedup(self) -> None:
        """_handle_dedup 实现。"""
        try:
            data = self._parse()

            if len(data) == 94:
                clean = remove_duplicates(data)

                self._input_edit.setPlainText(" ".join(map(str, clean)))

                self._show_result(tr("desktop.designer.dedupDone94to90"))

            else:
                self._show_result(tr("desktop.designer.dedupOnly94", n=len(data)))

        except Exception as exc:
            self._show_result(tr("desktop.designer.errorPrefix", error=exc))

    def _calculate(self) -> None:
        """_calculate 实现。"""
        try:
            data = self._parse()

            data_kind = (
                tr("desktop.designer.dataKindAttr") if self._is_attr_mode() else tr("desktop.designer.dataKindSkill")
            )
            lines: list[str] = [
                tr("desktop.designer.inputLen", n=len(data)),
                tr("desktop.designer.dataKindLine", kind=data_kind),
                "-" * 50,
            ]

            if self._is_attr_mode():
                if len(data) == 94:
                    data = remove_duplicates(data)

                    lines.append(tr("desktop.designer.autoDedup94to90"))

                if len(data) != 90:
                    raise ValueError(tr("desktop.designer.attrNeed90", n=len(data)))

                base, growth, divisor, offset = fit_attribute_formula(data)

                lines += [
                    tr("desktop.designer.calcResultColon"),
                    f"  base    = {base}",
                    f"  growth  = {growth}",
                    f"  divisor = {divisor}",
                    f"  offset  = {offset}",
                    "",
                    tr("desktop.designer.attrFormula"),
                ]

            else:
                if len(data) == 12:
                    base, growth, divisor, offset, special = fit_skill_formula(data)

                elif len(data) == 9:
                    base, growth, divisor, offset, special = fit_skill_formula_no_special(data)

                else:
                    raise ValueError(tr("desktop.designer.skillNeed9or12", n=len(data)))

                lines += [
                    tr("desktop.designer.calcResultColon"),
                    f"  base    = {base}",
                    f"  growth  = {growth}",
                    f"  divisor = {divisor}",
                    f"  offset  = {offset}",
                    f"  special = {special}",
                ]

            self._show_result("\n".join(lines))

        except Exception as exc:
            self._show_result(tr("desktop.designer.calcErrorPrefix", error=exc))

    def _validate(self) -> None:
        """_validate 实现。"""
        try:
            data = self._parse()

            if self._is_attr_mode():
                if len(data) == 94:
                    data = remove_duplicates(data)

                base, growth, divisor, offset = fit_attribute_formula(data)

                ok = validate_attribute_formula(base, growth, divisor, offset, data)

                ok_text = tr("desktop.designer.formulaOk") if ok else tr("desktop.designer.formulaMismatch")
                lines = [
                    tr("desktop.designer.validateResultLine", result=ok_text),
                    tr(
                        "desktop.designer.paramsLine",
                        base=base,
                        growth=growth,
                        divisor=divisor,
                        offset=offset,
                    ),
                ]

            else:
                params = fit_skill_formula(data) if len(data) == 12 else fit_skill_formula_no_special(data)

                base, growth, divisor, offset, special = params

                ok = validate_skill_formula(base, growth, divisor, offset, special, data)

                ok_text = tr("desktop.designer.formulaOk") if ok else tr("desktop.designer.formulaMismatch")
                lines = [
                    tr("desktop.designer.validateResultLine", result=ok_text),
                    tr(
                        "desktop.designer.paramsLine",
                        base=base,
                        growth=growth,
                        divisor=divisor,
                        offset=offset,
                    ),
                    tr("desktop.designer.specialLine", special=special),
                ]

            self._show_result("\n".join(lines))

        except Exception as exc:
            self._show_result(tr("desktop.designer.validateErrorPrefix", error=exc))

    def _generate_curve(self) -> None:
        """_generate_curve 实现。"""
        try:
            data = self._parse()

            if self._is_attr_mode():
                if len(data) == 94:
                    data = remove_duplicates(data)

                base, growth, divisor, offset = fit_attribute_formula(data)

                curve = calculate_growth_curve(base, growth, divisor, offset)

                lines = [
                    tr("desktop.designer.genAttrCurveHeader"),
                    tr(
                        "desktop.designer.paramsLine",
                        base=base,
                        growth=growth,
                        divisor=divisor,
                        offset=offset,
                    ),
                    "-" * 50,
                ]

                for lv in (1, 20, 40, 60, 80, 90):
                    lines.append(tr("desktop.designer.levelValue", level=lv, value=curve[lv - 1]))

                lines.append("")

                lines.append(tr("desktop.designer.fullCurveFirst10"))

                lines.append(", ".join(map(str, curve[:10])) + " …")

            else:
                if len(data) == 12:
                    base, growth, divisor, offset, special = fit_skill_formula(data)

                else:
                    base, growth, divisor, offset, special = fit_skill_formula_no_special(data)

                curve = calculate_skill_curve(base, growth, divisor, offset, special)

                lines = [
                    tr("desktop.designer.genSkillCurveHeader", n=len(curve)),
                    tr(
                        "desktop.designer.paramsLine",
                        base=base,
                        growth=growth,
                        divisor=divisor,
                        offset=offset,
                    ),
                    tr("desktop.designer.specialLine", special=special),
                    "-" * 50,
                    tr("desktop.designer.fullCurve"),
                    ", ".join(map(str, curve)),
                ]

            self._show_result("\n".join(lines))

        except Exception as exc:
            self._show_result(tr("desktop.designer.genErrorPrefix", error=exc))
