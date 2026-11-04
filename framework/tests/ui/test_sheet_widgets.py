# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""_ResponsiveGroupBox — 响应式重排回归测试。

回归：旧实现每次 ``resizeEvent`` 都无条件清空并重建网格。重建会改变
布局尺寸提示并再次触发 resize，事件循环被持续占用；加载列数较多的
查看器时窗口长时间无响应（表现为卡死）。
"""

from __future__ import annotations

import sys
from typing import Any, cast

import pytest
from PySide6.QtWidgets import QApplication, QLabel, QWidget

from calc_framework.ui.controls import ControlSpec
from calc_framework.ui.sheet_widgets import (
    _AVG_ITEM_WIDTH,
    _MIN_CONTROL_WIDTH,
    _ResponsiveGroupBox,
    make_spinbox,
)


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


def _make_box(item_count: int = 4) -> _ResponsiveGroupBox:
    """构造只含标签的响应式分组（widget 传 None，spec 不参与重排）。"""
    items: list[tuple[str, QLabel, QWidget | None, Any]] = [
        (f"user.v{index}", QLabel(f"标签{index}"), None, None) for index in range(item_count)
    ]
    return _ResponsiveGroupBox("输入参数", items)  # type: ignore[arg-type]


def _set_width(box: _ResponsiveGroupBox, width: int) -> None:
    box.width = lambda: width  # type: ignore[method-assign]


def _count_take_at(box: _ResponsiveGroupBox) -> dict[str, int]:
    calls = {"count": 0}
    original = box._grid.takeAt  # noqa: SLF001

    def counting_take(*args: Any, **kwargs: Any) -> Any:
        calls["count"] += 1
        return original(*args, **kwargs)

    box._grid.takeAt = counting_take  # type: ignore[method-assign]  # noqa: SLF001
    return calls


def test_first_layout_builds_grid(qapp) -> None:
    box = _make_box()
    _set_width(box, _AVG_ITEM_WIDTH * 2 + 40)

    box._on_resized()

    assert box._grid.count() == 4  # noqa: SLF001


def test_same_width_does_not_rebuild(qapp) -> None:
    """同样列数的 resize 不应清空/重建网格（卡死根因）。"""
    box = _make_box()
    _set_width(box, _AVG_ITEM_WIDTH * 2 + 40)
    box._on_resized()

    calls = _count_take_at(box)
    box._on_resized()

    assert calls["count"] == 0


def test_reentrant_resize_is_guarded(qapp) -> None:
    """重排过程中被同步触发的 resize 应立即返回，不能嵌套重建。"""
    box = _make_box()
    _set_width(box, _AVG_ITEM_WIDTH * 2 + 40)
    original_add = box._grid.addWidget  # noqa: SLF001
    nested = {"done": False}

    def add_and_reenter(*args: Any, **kwargs: Any) -> Any:
        result = original_add(*args, **kwargs)
        if not nested["done"]:
            nested["done"] = True
            box._on_resized()
        return result

    box._grid.addWidget = add_and_reenter  # type: ignore[method-assign]  # noqa: SLF001
    calls = _count_take_at(box)

    box._on_resized()

    assert nested["done"] is True
    assert calls["count"] == 0  # 嵌套调用被 guard 拦截，未清空网格
    assert box._grid.count() == 4  # noqa: SLF001


def test_input_labels_wrap_to_available_width(qapp) -> None:
    """标签必须允许换行，否则长描述会把整列撑到可视区之外。"""
    box = _make_box()

    labels = [label for _path, label, _widget, _spec in box._items]  # noqa: SLF001
    assert labels
    assert all(label.wordWrap() for label in labels)


def test_spinbox_keeps_compact_minimum_width(qapp) -> None:
    """大上限值（2^31-1）不应把输入框的最小宽度撑到 180px。"""
    spec = ControlSpec(label="数量", widget="spinbox", default=1, step=1)

    box = make_spinbox(spec)

    assert box.minimumWidth() == _MIN_CONTROL_WIDTH
    assert _MIN_CONTROL_WIDTH <= 120


def test_width_change_to_new_column_count_rebuilds(qapp) -> None:
    box = _make_box()
    _set_width(box, _AVG_ITEM_WIDTH * 2 + 40)
    box._on_resized()

    # 两个 item 列：第 2 个标签在第 0 行第 2 列
    pos = cast("tuple[int, int, int, int]", box._grid.getItemPosition(1))  # noqa: SLF001
    assert pos[:2] == (0, 2)

    _set_width(box, _AVG_ITEM_WIDTH + 40)
    box._on_resized()

    # 收窄为一个 item 列：第 2 个标签换到第 1 行第 0 列
    pos = cast("tuple[int, int, int, int]", box._grid.getItemPosition(1))  # noqa: SLF001
    assert pos[:2] == (1, 0)
