# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""图编辑器主窗口 — 工具栏构建。

入口 ``__main__.py`` 只负责装配窗口与动作闭包；本模块把
工具栏按钮的声明式构建拆出来，便于单独验证。
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from PySide6.QtWidgets import QMainWindow, QToolBar, QToolButton

from calc_framework.ui.i18n import tr

_TOOLBAR_QSS = """
    QToolBar {
        background: #252526; border-bottom: 1px solid #3c3c3c;
        padding: 2px; spacing: 4px;
    }
    QToolButton {
        color: #cccccc; background: transparent;
        border: 1px solid transparent; border-radius: 4px;
        padding: 6px 12px; font-family: "Microsoft YaHei"; font-size: 13px;
    }
    QToolButton:hover { background: #2a2d2e; border-color: #094771; color: white; }
    QToolButton:pressed { background: #094771; color: white; }
"""


@dataclass(frozen=True)
class ToolbarActions:
    """工具栏按钮的回调集合。"""

    new_file: Callable[[], None]
    open_file: Callable[[], None]
    save_file: Callable[[], None]
    import_package: Callable[[], None]
    delete_selected: Callable[[], None]
    fit_all: Callable[[], None]
    reset_zoom: Callable[[], None]
    run_evaluate: Callable[[], None]
    export_dag: Callable[[], None]
    clear_canvas: Callable[[], None]


def build_toolbar(window: QMainWindow, actions: ToolbarActions) -> QToolBar:
    """构建主窗口工具栏并返回。

    参数:
        window: 主窗口，工具栏挂到该窗口。
        actions: 工具栏按钮回调集合。

    返回:
        已填充按钮的工具栏。
    """
    toolbar = window.addToolBar(tr("desktop.graphEditor.commonOperations"))
    toolbar.setMovable(False)
    toolbar.setStyleSheet(_TOOLBAR_QSS)

    def add_button(text: str, tip: str, callback: Callable[[], None]) -> None:
        btn = QToolButton()
        btn.setText(text)
        btn.setToolTip(tip)
        btn.clicked.connect(callback)
        toolbar.addWidget(btn)

    add_button(tr("desktop.graphEditor.newBtn"), tr("desktop.graphEditor.newTip"), actions.new_file)
    add_button(tr("desktop.graphEditor.openBtn"), tr("desktop.graphEditor.openTip"), actions.open_file)
    add_button(tr("desktop.graphEditor.saveBtn"), tr("desktop.graphEditor.saveTip"), actions.save_file)
    toolbar.addSeparator()
    add_button(tr("desktop.graphEditor.importPackageBtn"), tr("desktop.graphEditor.importPackageTip"), actions.import_package)
    toolbar.addSeparator()
    add_button(tr("common.delete"), tr("desktop.graphEditor.deleteTip"), actions.delete_selected)
    toolbar.addSeparator()
    add_button(tr("desktop.graphEditor.fitViewBtn"), tr("desktop.graphEditor.fitViewTip"), actions.fit_all)
    add_button(tr("desktop.graphEditor.resetViewBtn"), tr("desktop.graphEditor.resetViewTip"), actions.reset_zoom)
    toolbar.addSeparator()
    add_button(tr("desktop.graphEditor.evaluateBtn"), tr("desktop.graphEditor.evaluateTip"), actions.run_evaluate)
    add_button(tr("desktop.graphEditor.exportDagBtn"), tr("desktop.graphEditor.exportDagTip"), actions.export_dag)
    toolbar.addSeparator()
    add_button(tr("desktop.graphEditor.clearBtn"), tr("desktop.graphEditor.clearTip"), actions.clear_canvas)

    return toolbar
