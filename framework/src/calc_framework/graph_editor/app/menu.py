# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""图编辑器主窗口 — 菜单栏构建。

入口 ``__main__.py`` 只负责装配窗口与动作闭包；本模块把
文件/帮助菜单的声明式构建拆出来，便于单独验证。
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import QMainWindow, QMenu

from calc_framework.ui.i18n import tr


@dataclass(frozen=True)
class MenuActions:
    """文件菜单与帮助菜单的回调集合。"""

    new_file: Callable[[], None]
    open_file: Callable[[], None]
    save_file: Callable[[], None]
    save_as_file: Callable[[], None]
    export_dag: Callable[[], None]
    show_help: Callable[[], None]


def _add_action(
    menu: QMenu,
    window: QMainWindow,
    text: str,
    shortcut: QKeySequence | QKeySequence.StandardKey | str,
    callback: Callable[[], None],
) -> None:
    action = QAction(text, window)
    action.setShortcut(shortcut)
    action.triggered.connect(callback)
    menu.addAction(action)


def build_menu(window: QMainWindow, actions: MenuActions) -> None:
    """构建文件/帮助菜单并挂到主窗口。

    参数:
        window: 主窗口，作为 QAction 的父对象。
        actions: 菜单项回调集合。
    """
    menubar = window.menuBar()
    file_menu = menubar.addMenu(tr("common.file"))

    _add_action(file_menu, window, tr("desktop.graphEditor.new"), QKeySequence.StandardKey.New, actions.new_file)
    _add_action(file_menu, window, tr("desktop.graphEditor.open"), QKeySequence.StandardKey.Open, actions.open_file)
    _add_action(file_menu, window, tr("desktop.graphEditor.save"), QKeySequence.StandardKey.Save, actions.save_file)
    _add_action(
        file_menu,
        window,
        tr("desktop.graphEditor.saveAs"),
        QKeySequence.StandardKey.SaveAs,
        actions.save_as_file,
    )
    file_menu.addSeparator()
    _add_action(file_menu, window, tr("desktop.graphEditor.exportDag"), QKeySequence("Ctrl+Shift+E"), actions.export_dag)

    help_menu = menubar.addMenu(tr("common.help"))
    _add_action(
        help_menu,
        window,
        tr("desktop.graphEditor.usageGuide"),
        QKeySequence(Qt.Key.Key_F1),
        actions.show_help,
    )

    # 捐赠菜单（可选，依赖项目特定的 utils 模块）
    try:
        from utils.gui.donation import append_donation_help_menu_action

        append_donation_help_menu_action(help_menu, window)
    except ImportError:
        pass  # 捐赠功能不可用，跳过
