#!/usr/bin/env python3

# SPDX-License-Identifier: AGPL-3.0
"""公式反推页签 — 从数值数据反向推导成长公式参数。"""

from __future__ import annotations


import re


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

        header = QLabel("数值反推公式工具")

        header.setFont(self._big)

        header.setStyleSheet(_SECTION_STYLE)

        layout.addWidget(header)

        mode_row = QHBoxLayout()

        mode_row.addWidget(self._make_label("数据类型"))

        self._mode_combo = QComboBox()

        self._mode_combo.addItems(["属性数据（90级）", "技能倍率（9/12级）"])

        self._mode_combo.setStyleSheet(_COMBO_STYLE)

        self._mode_combo.currentTextChanged.connect(self._update_hint)

        mode_row.addWidget(self._mode_combo)

        mode_row.addStretch()

        layout.addLayout(mode_row)

        self._hint_label = self._make_label("")

        self._hint_label.setStyleSheet(_HINT_STYLE)

        layout.addWidget(self._hint_label)

        self._input_edit = QTextEdit()

        self._input_edit.setStyleSheet(_INPUT_STYLE)

        self._input_edit.setPlaceholderText("在此输入数值，空格或换行分隔…")

        self._input_edit.setMinimumHeight(120)

        layout.addWidget(self._input_edit, stretch=1)

        btn_row = QHBoxLayout()

        self._clear_btn = QPushButton("清除输入")

        self._clear_btn.setStyleSheet(_BTN_STYLE)

        self._clear_btn.clicked.connect(self._clear_input)

        btn_row.addWidget(self._clear_btn)

        self._sample_btn = QPushButton("示例数据")

        self._sample_btn.setStyleSheet(_BTN_STYLE)

        self._sample_btn.clicked.connect(self._load_sample)

        btn_row.addWidget(self._sample_btn)

        self._dedup_btn = QPushButton("去重处理")

        self._dedup_btn.setStyleSheet(_BTN_STYLE)

        self._dedup_btn.clicked.connect(self._handle_dedup)

        btn_row.addWidget(self._dedup_btn)

        btn_row2 = QHBoxLayout()

        self._calc_btn = QPushButton("开始反推")

        self._calc_btn.setStyleSheet(_BTN_PRIMARY_STYLE)

        self._calc_btn.clicked.connect(self._calculate)

        btn_row2.addWidget(self._calc_btn)

        self._validate_btn = QPushButton("验证公式")

        self._validate_btn.setStyleSheet(_BTN_STYLE)

        self._validate_btn.clicked.connect(self._validate)

        btn_row2.addWidget(self._validate_btn)

        self._curve_btn = QPushButton("生成曲线")

        self._curve_btn.setStyleSheet(_BTN_STYLE)

        self._curve_btn.clicked.connect(self._generate_curve)

        btn_row2.addWidget(self._curve_btn)

        layout.addLayout(btn_row)

        layout.addLayout(btn_row2)

        result_header = QLabel("计算结果")

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

    def _update_hint(self) -> None:
        """_update_hint 实现。"""
        mode = self._mode_combo.currentText()

        if "属性" in mode:
            self._hint_label.setText("提示：输入90个属性数据（空格或换行分隔），支持整数和小数/百分比格式")

        else:
            self._hint_label.setText("提示：输入9或12个技能倍率数据（空格或换行分隔），支持整数和小数/百分比格式")

    def _clear_input(self) -> None:
        """_clear_input 实现。"""
        self._input_edit.clear()

        self._result_edit.clear()

    def _load_sample(self) -> None:
        """_load_sample 实现。"""
        self._input_edit.clear()

        if "属性" in self._mode_combo.currentText():
            sample = "34 38 41 45 48 52 55 59 62 65 69 72 76 79 83 86 90 93 96 100"

        else:
            sample = "100 102 104 106 108 110 112 114 116 150 160 170"

        self._input_edit.setPlainText(sample)

    def _parse(self) -> list[float]:
        """_parse 实现。"""
        text = self._input_edit.toPlainText().strip()

        if not text:
            raise ValueError("请输入数据")

        tokens = re.split(r"[\s,，]+", text)

        tokens = [t.strip() for t in tokens if t.strip()]

        if not tokens:
            raise ValueError("未找到有效数据")

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

                self._show_result("已去重处理：94个数据 → 90个数据")

            else:
                self._show_result(f"当前数据长度 {len(data)}，只有94个数据需要去重")

        except Exception as exc:
            self._show_result(f"错误：{exc}")

    def _calculate(self) -> None:
        """_calculate 实现。"""
        try:
            data = self._parse()

            lines: list[str] = [
                f"输入数据长度: {len(data)}",
                f"数据类型: {'属性数据' if '属性' in self._mode_combo.currentText() else '技能倍率'}",
                "-" * 50,
            ]

            if "属性" in self._mode_combo.currentText():
                if len(data) == 94:
                    data = remove_duplicates(data)

                    lines.append("已自动去重: 94 → 90")

                if len(data) != 90:
                    raise ValueError(f"属性数据需要90个值，当前{len(data)}个")

                base, growth, divisor, offset = fit_attribute_formula(data)

                lines += [
                    "计算结果:",
                    f"  base    = {base}",
                    f"  growth  = {growth}",
                    f"  divisor = {divisor}",
                    f"  offset  = {offset}",
                    "",
                    "公式: base + floor((growth * (lv - 1) + offset) / divisor)",
                ]

            else:
                if len(data) == 12:
                    base, growth, divisor, offset, special = fit_skill_formula(data)

                elif len(data) == 9:
                    base, growth, divisor, offset, special = fit_skill_formula_no_special(data)

                else:
                    raise ValueError(f"技能数据需要9或12个值，当前{len(data)}个")

                lines += [
                    "计算结果:",
                    f"  base    = {base}",
                    f"  growth  = {growth}",
                    f"  divisor = {divisor}",
                    f"  offset  = {offset}",
                    f"  special = {special}",
                ]

            self._show_result("\n".join(lines))

        except Exception as exc:
            self._show_result(f"计算错误：{exc}")

    def _validate(self) -> None:
        """_validate 实现。"""
        try:
            data = self._parse()

            if "属性" in self._mode_combo.currentText():
                if len(data) == 94:
                    data = remove_duplicates(data)

                base, growth, divisor, offset = fit_attribute_formula(data)

                ok = validate_attribute_formula(base, growth, divisor, offset, data)

                lines = [
                    f"验证结果: {'✓ 公式正确' if ok else '✗ 公式不匹配'}",
                    f"参数: base={base}, growth={growth}, divisor={divisor}, offset={offset}",
                ]

            else:
                if len(data) == 12:
                    params = fit_skill_formula(data)

                else:
                    params = fit_skill_formula_no_special(data)

                base, growth, divisor, offset, special = params

                ok = validate_skill_formula(base, growth, divisor, offset, special, data)

                lines = [
                    f"验证结果: {'✓ 公式正确' if ok else '✗ 公式不匹配'}",
                    f"参数: base={base}, growth={growth}, divisor={divisor}, offset={offset}",
                    f"特殊值: {special}",
                ]

            self._show_result("\n".join(lines))

        except Exception as exc:
            self._show_result(f"验证错误：{exc}")

    def _generate_curve(self) -> None:
        """_generate_curve 实现。"""
        try:
            data = self._parse()

            if "属性" in self._mode_combo.currentText():
                if len(data) == 94:
                    data = remove_duplicates(data)

                base, growth, divisor, offset = fit_attribute_formula(data)

                curve = calculate_growth_curve(base, growth, divisor, offset)

                lines = [
                    "生成属性成长曲线（90级）:",
                    f"参数: base={base}, growth={growth}, divisor={divisor}, offset={offset}",
                    "-" * 50,
                ]

                for lv in (1, 20, 40, 60, 80, 90):
                    lines.append(f"等级{lv}: {curve[lv - 1]}")

                lines.append("")

                lines.append("完整曲线（前10级）:")

                lines.append(", ".join(map(str, curve[:10])) + " …")

            else:
                if len(data) == 12:
                    base, growth, divisor, offset, special = fit_skill_formula(data)

                else:
                    base, growth, divisor, offset, special = fit_skill_formula_no_special(data)

                curve = calculate_skill_curve(base, growth, divisor, offset, special)

                lines = [
                    f"生成技能倍率曲线（{len(curve)}级）:",
                    f"参数: base={base}, growth={growth}, divisor={divisor}, offset={offset}",
                    f"特殊值: {special}",
                    "-" * 50,
                    "完整曲线:",
                    ", ".join(map(str, curve)),
                ]

            self._show_result("\n".join(lines))

        except Exception as exc:
            self._show_result(f"生成错误：{exc}")
