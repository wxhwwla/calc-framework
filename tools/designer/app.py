"""开发者工具主窗口 — 三页签：数据录入 / 布局编辑 / 主题与导出。

三页签数据共享：
- 数据录入 → 主题与导出：标准格式数据自动传递
- 布局编辑 → 主题与导出：DAG + layout 自动传递
- 切换到导出页签时自动同步
"""

from __future__ import annotations

import sys
import os

_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QLabel,
    QMainWindow,
    QMessageBox,
    QStatusBar,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from calc_framework.config.manager import AdapterManager

from tools.designer.data_editor.panel import DataEditorPanel
from tools.designer.layout_editor.canvas import LayoutCanvasPanel
from tools.designer.theme_editor.panel import ThemePanel


class DesignerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("配置包设计器")
        self.resize(1200, 800)

        self._adapter_mgr = AdapterManager()

        self._tabs = QTabWidget()
        self.setCentralWidget(self._tabs)

        self._data_panel = DataEditorPanel()
        self._layout_panel = LayoutCanvasPanel()
        self._theme_panel = ThemePanel()
        self._theme_panel.export_requested.connect(self._on_export)

        self._tabs.addTab(self._data_panel, "数据录入")
        self._tabs.addTab(self._layout_panel, "布局编辑")
        self._tabs.addTab(self._theme_panel, "主题与导出")

        self._status = QStatusBar()
        self._status_label = QLabel("就绪")
        self._status.addWidget(self._status_label)
        self.setStatusBar(self._status)

        self._tabs.currentChanged.connect(self._on_tab_changed)

        self._layout_panel.layout_changed.connect(self._on_layout_changed)

        self._update_status()

    def _on_tab_changed(self, index: int) -> None:
        if index == 1:
            self._layout_panel.populate_adapters(self._adapter_mgr.names)
        elif index == 2:
            self._auto_sync_to_theme()
        self._update_status()

    def _on_layout_changed(self, layout_data: dict | None) -> None:
        if layout_data:
            self._status_label.setText("布局已更新 — 导出页签可同步最新数据")

    def _auto_sync_to_theme(self) -> None:
        """切到导出页签时自动同步其他面板的数据。"""
        data_files = self._data_panel.get_data_files()

        layout_data = self._layout_panel.get_layout_data()
        dag_service = self._layout_panel.get_dag_service()

        dag_dict = None
        if dag_service:
            try:
                import json
                from calc_framework.dag.serializer import dag_to_dict
                dag_dict = dag_to_dict(dag_service.dag)
            except Exception:
                dag_dict = {"name": self._layout_panel.get_adapter_name(), "from_adapter": True}

        if any(data_files.values()):
            count_parts = [f"{k}={len(v)}" for k, v in data_files.items()]
            self._status_label.setText(
                f"已同步数据({', '.join(count_parts)}) + "
                f"{'布局' if layout_data else '无布局'} + "
                f"{'DAG' if dag_dict else '无DAG'}"
            )

        self._theme_panel.set_shared_data(
            data_files=data_files,
            dag_data=dag_dict,
            layout_data=layout_data,
        )
        self._theme_panel._sync_from_shared()

    def _update_status(self) -> None:
        tab_name = self._tabs.tabText(self._tabs.currentIndex())
        self._status_label.setText(f"当前页签: {tab_name}")

    def _on_export(self, path: str) -> None:
        self._status_label.setText(f"已导出 → {path}")


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("配置包设计器")
    win = DesignerWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
