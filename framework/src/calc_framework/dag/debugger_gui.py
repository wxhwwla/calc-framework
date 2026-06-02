# SPDX-License-Identifier: AGPL-3.0
"""DAG 分步调试器 GUI — PySide6 可视化逐步执行界面。

用法::

    from calc_framework.dag.debugger_gui import StepDebuggerWidget

    widget = StepDebuggerWidget(dag_graph, context)
    widget.show()
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from calc_framework.logging import get_logger

if TYPE_CHECKING:
    from calc_framework.dag.schema import DAGGraph

logger = get_logger(__name__)

try:
    from PySide6 import QtGui as _QtGui
    from PySide6 import QtWidgets as _QtWidgets

    _HAS_PYSIDE = True
except ImportError:
    _HAS_PYSIDE = False


if _HAS_PYSIDE:
    from calc_framework.dag.debugger import StepDebugger, StepStatus


    class _NodeItem:
        def __init__(self, node_id: str, node_type: str, label: str = "") -> None:
            self.node_id = node_id
            self.node_type = node_type
            self.label = label or node_id
            self.value: float | None = None
            self.executed = False
            self.is_breakpoint = False

    class StepDebuggerWidget(_QtWidgets.QWidget):  # type: ignore[no-redef]
        def __init__(
            self,
            dag_graph: DAGGraph,
            context: dict,
            parent: _QtWidgets.QWidget | None = None,  # type: ignore[reportGeneralTypeIssues]
        ) -> None:
            super().__init__(parent)
            self._debugger = StepDebugger(dag_graph, context)
            self._node_items: list[_NodeItem] = []
            self._setup_ui()
            self._build_node_list()

        def _setup_ui(self) -> None:
            self.setWindowTitle("DAG 分步调试器")
            self.resize(700, 500)

            layout = _QtWidgets.QVBoxLayout(self)  # type: ignore[reportGeneralTypeIssues]

            self._list_widget = _QtWidgets.QListWidget()  # type: ignore[reportGeneralTypeIssues]
            self._list_widget.setAlternatingRowColors(True)
            layout.addWidget(self._list_widget, stretch=1)

            btn_layout = _QtWidgets.QHBoxLayout()  # type: ignore[reportGeneralTypeIssues]

            self._btn_step = _QtWidgets.QPushButton("单步执行 (n)")  # type: ignore[reportGeneralTypeIssues]
            self._btn_step.clicked.connect(self._on_step)
            btn_layout.addWidget(self._btn_step)

            self._btn_run = _QtWidgets.QPushButton("全部执行 (r)")  # type: ignore[reportGeneralTypeIssues]
            self._btn_run.clicked.connect(self._on_run)
            btn_layout.addWidget(self._btn_run)

            self._btn_reset = _QtWidgets.QPushButton("重置")  # type: ignore[reportGeneralTypeIssues]
            self._btn_reset.clicked.connect(self._on_reset)
            btn_layout.addWidget(self._btn_reset)

            layout.addLayout(btn_layout)

            self._status_label = _QtWidgets.QLabel("进度: 0/0")  # type: ignore[reportGeneralTypeIssues]
            layout.addWidget(self._status_label)

        def _build_node_list(self) -> None:
            self._list_widget.clear()
            self._node_items.clear()
            for nid in self._debugger.execution_order:
                info = self._debugger.get_node_info(nid)
                ntype = info.type if info else ""
                label = info.label if info and info.label else nid
                item = _NodeItem(nid, ntype, label)
                self._node_items.append(item)

                list_item = _QtWidgets.QListWidgetItem(f"\u23f3 {label}  [{ntype}]")  # type: ignore[reportGeneralTypeIssues]
                list_item.setForeground(_QtGui.QColor("#888"))  # type: ignore[reportGeneralTypeIssues]
                self._list_widget.addItem(list_item)

            self._update_status()

        def _on_step(self) -> None:
            if self._debugger.finished:
                self._status_label.setText("已完成 \u2014 点击重置重新开始")
                return
            result = self._debugger.step()
            if result is None:
                self._status_label.setText("全部执行完成")
                return
            self._update_node_display(result.node_id, result.value, result.status == StepStatus.BREAKPOINT)
            self._update_status()

        def _on_run(self) -> None:
            if self._debugger.finished:
                self._on_reset()
                return
            results = self._debugger.run_all()
            for r in results:
                self._update_node_display(r.node_id, r.value, r.status == StepStatus.BREAKPOINT)
            self._update_status()

        def _on_reset(self) -> None:
            self._debugger.reset()
            for i, item in enumerate(self._node_items):
                item.executed = False
                item.value = None
                self._list_widget.item(i).setText(f"\u23f3 {item.label}  [{item.node_type}]")
                self._list_widget.item(i).setForeground(_QtGui.QColor("#888"))  # type: ignore[reportGeneralTypeIssues]
            self._update_status()

        def _update_node_display(self, node_id: str, value: float, is_bp: bool) -> None:
            for i, item in enumerate(self._node_items):
                if item.node_id == node_id:
                    item.executed = True
                    item.value = value
                    icon = "\U0001f534" if is_bp else "\u2705"
                    self._list_widget.item(i).setText(
                        f"{icon} {item.label} = {value}  [{item.node_type}]"
                    )
                    self._list_widget.item(i).setForeground(
                        _QtGui.QColor("#FF6B6B") if is_bp else _QtGui.QColor("#4ECDC4")  # type: ignore[reportGeneralTypeIssues]
                    )
                    self._list_widget.scrollToItem(self._list_widget.item(i))
                    break

        def _update_status(self) -> None:
            done, total = self._debugger.progress
            pct = done / total * 100 if total else 0
            bp_count = len(self._debugger.list_breakpoints())
            self._status_label.setText(f"进度: {done}/{total} ({pct:.0f}%)  |  断点: {bp_count}")

        @property
        def debugger(self) -> StepDebugger:
            return self._debugger

else:

    class StepDebuggerWidget:  # type: ignore[no-redef]
        def __init__(self, *args: object, **kwargs: object) -> None:
            _ = args, kwargs
            raise ImportError(
                "PySide6 未安装。请执行: pip install calc-framework[ui]"
            )
