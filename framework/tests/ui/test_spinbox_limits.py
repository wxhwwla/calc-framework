# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""数值输入框默认上限回归测试。

回归：QSpinBox/QDoubleSpinBox 自带 99/99.99 的默认最大值。DAG 变量未声明
``max`` 时，旧实现不覆盖该默认值，导致「无上限」的输入（伤害加成、护甲、
编组数量等）被静默截断。
"""

from __future__ import annotations

import sys

import pytest
from PySide6.QtWidgets import QApplication, QDoubleSpinBox, QSpinBox

from calc_framework.ui.controls import ControlSpec, infer_control
from calc_framework.ui.sheet_widgets import make_spinbox


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


def test_double_spinbox_without_max_is_not_capped(qapp) -> None:
    box = make_spinbox(ControlSpec(label="伤害加成", widget="spinbox", default=0.0, step=0.01))

    assert isinstance(box, QDoubleSpinBox)
    assert box.maximum() > 1_000_000


def test_int_spinbox_without_max_is_not_capped(qapp) -> None:
    box = make_spinbox(ControlSpec(label="编组数量", widget="spinbox", default=1, step=1))

    assert isinstance(box, QSpinBox)
    assert box.maximum() > 1_000_000


def test_ui_control_suffix_and_step_are_inferred() -> None:
    spec = infer_control(
        "user_input.damage_bonus",
        {
            "type": "float",
            "source": "user_input",
            "ui_control": {"suffix": "%", "step": 1},
        },
    )

    assert spec.suffix == "%"
    assert spec.step == 1


def test_spinbox_suffix_is_applied(qapp) -> None:
    box = make_spinbox(ControlSpec(label="伤害加成", widget="spinbox", default=0.0, step=1, suffix="%"))

    assert box.suffix() == "%"


def test_explicit_max_is_honored(qapp) -> None:
    box = make_spinbox(
        ControlSpec(
            label="飞行时间加成",
            widget="spinbox",
            default=0.0,
            max_val=1.0,
            step=0.01,
        )
    )

    assert box.maximum() == pytest.approx(1.0)
