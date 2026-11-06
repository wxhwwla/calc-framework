# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""P2-07：``graph_editor.__main__`` 拆分后的结构与行为门禁。

菜单栏与工具栏按符号边界抽到独立模块后，入口文件继续负责窗口
装配与动作闭包；行数门禁防止 600+ 行入口回流。
"""

from __future__ import annotations

import importlib
from collections.abc import Callable
from pathlib import Path


def _line_count(module_name: str) -> int:
    module = importlib.import_module(module_name)
    module_file = module.__file__
    assert module_file is not None
    return len(Path(module_file).read_text(encoding="utf-8").splitlines())


def test_main_module_stays_within_target() -> None:
    assert _line_count("calc_framework.graph_editor.__main__") <= 400


def test_split_modules_stay_within_target() -> None:
    assert _line_count("calc_framework.graph_editor.app.menu") <= 400
    assert _line_count("calc_framework.graph_editor.app.toolbar") <= 400


def _recorder(calls: list[str], name: str) -> Callable[[], None]:
    return lambda: calls.append(name)


def test_build_menu_wires_file_actions(qapp) -> None:
    from PySide6.QtWidgets import QMainWindow

    from calc_framework.graph_editor.app.menu import MenuActions, build_menu

    calls: list[str] = []
    window = QMainWindow()
    build_menu(
        window,
        MenuActions(
            new_file=_recorder(calls, "new"),
            open_file=_recorder(calls, "open"),
            save_file=_recorder(calls, "save"),
            save_as_file=_recorder(calls, "save_as"),
            export_dag=_recorder(calls, "export"),
            show_help=_recorder(calls, "help"),
        ),
    )

    menu_actions = window.menuBar().actions()
    assert len(menu_actions) == 2

    file_menu = menu_actions[0].menu()
    assert file_menu is not None
    file_actions = file_menu.actions()
    assert len(file_actions) == 6
    file_actions[0].trigger()
    assert calls == ["new"]

    help_menu = menu_actions[1].menu()
    assert help_menu is not None
    help_actions = help_menu.actions()
    help_actions[0].trigger()
    assert calls[-1] == "help"


def test_build_toolbar_wires_buttons(qapp) -> None:
    from PySide6.QtWidgets import QMainWindow, QToolButton

    from calc_framework.graph_editor.app.toolbar import ToolbarActions, build_toolbar

    calls: list[str] = []
    window = QMainWindow()
    toolbar = build_toolbar(
        window,
        ToolbarActions(
            new_file=_recorder(calls, "new"),
            open_file=_recorder(calls, "open"),
            save_file=_recorder(calls, "save"),
            import_package=_recorder(calls, "import"),
            delete_selected=_recorder(calls, "delete"),
            fit_all=_recorder(calls, "fit"),
            reset_zoom=_recorder(calls, "reset"),
            run_evaluate=_recorder(calls, "evaluate"),
            export_dag=_recorder(calls, "export"),
            clear_canvas=_recorder(calls, "clear"),
        ),
    )

    # QToolBar 会自带一个用于溢出菜单的 qt_toolbar_ext_button
    buttons = [btn for btn in toolbar.findChildren(QToolButton) if btn.objectName() != "qt_toolbar_ext_button"]
    assert len(buttons) == 10
    buttons[0].click()
    assert calls == ["new"]
