# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""CalculatorShell / CalculatorPage — 三计算器共享布局骨架。"""

from __future__ import annotations

import sys

import pytest
from PySide6.QtWidgets import QApplication, QLabel


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


def _page() -> object:
    from calc_framework.ui.calculator_shell import CalculatorPage

    page = CalculatorPage(
        top_left_title="角色选择",
        top_right_title="武器选择",
        bottom_left_title="角色属性",
        bottom_right_title="武器属性",
    )
    for key, text in (
        ("top_left", "左上"),
        ("top_right", "右上"),
        ("bottom_left", "左下"),
        ("bottom_right", "右下"),
    ):
        page.zone(key).add_widget(QLabel(text))
    return page


class TestCalculatorPage:
    def test_exposes_four_zones_with_titles(self, qapp) -> None:
        page = _page()

        assert page.zone("top_left").title() == "角色选择"
        assert page.zone("top_right").title() == "武器选择"
        assert page.zone("bottom_left").title() == "角色属性"
        assert page.zone("bottom_right").title() == "武器属性"
        assert [widget.text() for widget in page.zone("top_left").findChildren(QLabel)] == ["左上"]

    def test_zone_can_be_hidden(self, qapp) -> None:
        page = _page()

        page.set_zone_visible("bottom_right", False)

        assert page.zone("bottom_right").isHidden() is True

    def test_unknown_zone_raises(self, qapp) -> None:
        page = _page()

        with pytest.raises(KeyError):
            page.zone("center")


class TestCalculatorShell:
    def _shell(self):
        from calc_framework.ui.calculator_shell import CalculatorShell

        return CalculatorShell()

    def test_toolbar_collects_non_calc_actions(self, qapp) -> None:
        shell = self._shell()
        calls: list[str] = []

        shell.add_tool_action("帮助", lambda: calls.append("help"))
        shell.add_tool_action("捐赠", lambda: calls.append("donate"))

        texts = [action.text() for action in shell.toolbar.actions() if action.text()]
        assert texts == ["帮助", "捐赠"]

    def test_pages_are_switched_from_bottom_tabs(self, qapp) -> None:
        shell = self._shell()
        page_one = _page()
        page_two = _page()

        shell.add_page("计算", page_one)
        shell.add_page("乘区明细", page_two)

        assert shell.page_count == 2
        assert shell.current_page == 0
        assert shell.tab_texts() == ["计算", "乘区明细"]

        shell.set_current_page(1)

        assert shell.current_page == 1
        assert shell.page_stack.currentWidget() is page_two

    def test_confirm_button_emits_signal(self, qapp) -> None:
        shell = self._shell()
        emitted: list[bool] = []
        shell.confirmed.connect(lambda: emitted.append(True))

        shell.confirm_button.click()

        assert emitted == [True]

    def test_pending_and_confirmed_states_change_button_text(self, qapp) -> None:
        shell = self._shell()

        shell.set_pending("待确认")
        assert shell.confirm_button.text() == "待确认"

        shell.set_confirmed("已确认")
        assert shell.confirm_button.text() == "已确认"

    def test_status_text_is_visible(self, qapp) -> None:
        shell = self._shell()

        shell.set_status("有未确认的更改")

        assert shell.status_text() == "有未确认的更改"
