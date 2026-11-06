# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""图编辑器主窗口 — 导出与求值动作。

入口 ``__main__.py`` 保留动作闭包，但把带对话框的导出/求值流程
拆到这里，避免入口文件继续膨胀。
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtWidgets import QFileDialog, QMainWindow, QMessageBox

from calc_framework.ui.i18n import tr

from ...dag.engine import evaluate_graph
from ..compiler import compile_graph
from ..file_actions import collect_document

if TYPE_CHECKING:
    from ..graph_editor_widget import GraphEditorWidget
    from ..tab_manager import TabManager


def export_dag_interactive(window: QMainWindow, canvas: GraphEditorWidget, tab_manager: TabManager) -> None:
    """编译当前画布并导出为 .dag.json 文件。

    参数:
        window: 主窗口，作为对话框父对象。
        canvas: 当前画布。
        tab_manager: 标签页管理器，用于推断默认文件名。
    """
    try:
        doc = collect_document(canvas)
        dag = compile_graph(doc)
    except Exception as e:
        QMessageBox.critical(window, tr("desktop.graphEditor.exportDagFailed"), str(e))
        return

    # 默认文件名：从当前标签页名称推断
    tab_text = tab_manager.tabText(tab_manager.currentIndex()).replace("*", "").strip()
    untitled = tr("desktop.graphEditor.untitled")
    default_name = tab_text if tab_text and tab_text != untitled else "untitled"
    default_path = f"{default_name}.dag.json"

    path_str, _ = QFileDialog.getSaveFileName(
        window,
        tr("desktop.graphEditor.exportDag"),
        default_path,
        tr("desktop.graphEditor.exportDagFileFilter"),
    )
    if not path_str:
        return

    try:
        from ...dag.serializer import save_dag

        save_dag(dag, Path(path_str))
        QMessageBox.information(
            window,
            tr("desktop.graphEditor.exportDagSuccess"),
            tr("desktop.graphEditor.exportDagSuccessDetail", path=path_str),
        )
    except Exception as e:
        QMessageBox.critical(window, tr("desktop.graphEditor.exportDagFailed"), str(e))


def show_evaluation_report(window: QMainWindow, canvas: GraphEditorWidget) -> None:
    """编译并求值当前画布，用消息框显示输出与节点值。

    参数:
        window: 主窗口，作为消息框父对象。
        canvas: 当前画布。
    """
    try:
        doc = collect_document(canvas)
        dag = compile_graph(doc)
        res = evaluate_graph(dag, {})
        output_lines = [f"{k}: {v}" for k, v in res.outputs.items()]
        node_lines = [f"{k}: {v}" for k, v in res.node_values.items()]
        msg = (
            tr("desktop.graphEditor.evalOutputResult") + "\n" + "\n".join(output_lines)
            if output_lines
            else tr("desktop.graphEditor.evalNoOutput")
        )
        msg += "\n\n" + tr("desktop.graphEditor.evalNodeValues") + "\n" + "\n".join(node_lines) if node_lines else ""
        QMessageBox.information(window, tr("desktop.graphEditor.evalResult"), msg)
    except Exception as e:
        QMessageBox.critical(window, tr("desktop.graphEditor.evalFailed"), str(e))
