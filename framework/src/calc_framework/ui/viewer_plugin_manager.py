# SPDX-License-Identifier: AGPL-3.0
"""插件管理器对话框 — 导入/打包/查看插件。"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class PluginManagerDialog(QDialog):
    """插件管理器对话框 — 导入/打包/查看插件。"""

    def __init__(self, parent: QWidget | None = None, status_callback: Callable[[str], None] | None = None):
        super().__init__(parent)
        self._status_callback = status_callback
        self._build_ui()

    def _build_ui(self) -> None:
        """_build_ui。"""
        from ..plugin.registry import get_registry, list_plugins

        plugins = list_plugins()
        reg = get_registry()

        self.setWindowTitle(f"插件管理器 ({len(plugins)} 已注册)")
        self.resize(560, 460)
        layout = QVBoxLayout(self)

        toolbar = QHBoxLayout()
        import_btn = QPushButton("导入 .calcplugin...")
        import_btn.setStyleSheet("""
            QPushButton { background-color: #2B6CB6; color: white;
                          border: none; border-radius: 4px; padding: 6px 14px; }
            QPushButton:hover { background-color: #3182CE; }
        """)
        import_btn.clicked.connect(self._import_plugin)
        toolbar.addWidget(import_btn)

        build_btn = QPushButton("打包插件目录...")
        build_btn.setStyleSheet("""
            QPushButton { background-color: #2B6CB6; color: white;
                          border: none; border-radius: 4px; padding: 6px 14px; }
            QPushButton:hover { background-color: #3182CE; }
        """)
        build_btn.clicked.connect(self._build_plugin)
        toolbar.addWidget(build_btn)

        refresh_btn = QPushButton("刷新")
        refresh_btn.setStyleSheet("""
            QPushButton { background-color: transparent; color: #D1D1D1;
                          border: 1px solid #464646; border-radius: 4px; padding: 6px 14px; }
            QPushButton:hover { border-color: #2B6CB6; }
        """)
        refresh_btn.clicked.connect(self._refresh)
        toolbar.addWidget(refresh_btn)
        toolbar.addStretch()
        layout.addLayout(toolbar)

        if not plugins:
            layout.addWidget(
                QLabel(
                    "暂无已注册的插件。\n点击「导入 .calcplugin」安装一个插件，或「打包插件目录」将源码目录打包为 .calcplugin。"
                )
            )
        else:
            for name in plugins:
                plugin = reg.get(name)
                if plugin is None:
                    continue
                meta = plugin.meta
                group = QGroupBox(f"{meta.name}  v{meta.version}")
                fl = QFormLayout(group)
                fl.addRow("描述:", QLabel(meta.description))
                fl.addRow("作者:", QLabel(meta.author or "—"))
                if meta.dependencies:
                    fl.addRow("依赖:", QLabel(", ".join(meta.dependencies)))
                layout.addWidget(group)

        layout.addStretch()
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

    def _import_plugin(self) -> None:
        """导入 .calcplugin 文件。"""
        path, _ = QFileDialog.getOpenFileName(
            self,
            "导入插件",
            "",
            "CalcPlugin (*.calcplugin);;ZIP (*.zip);;All Files (*)",
        )
        if not path:
            return
        try:
            from tools.plugin_pack import install_plugin

            repo = Path(__file__).resolve().parents[3]
            target = repo / "web" / "hub" / "plugins"
            installed = install_plugin(path, target)
            msg = f"插件已安装: {installed.name}"
            if self._status_callback:
                self._status_callback(msg)
            QMessageBox.information(self, "导入成功", f"插件已安装到:\n{installed}\n\n点击「刷新」查看已注册的插件。")
        except Exception as e:
            QMessageBox.critical(self, "导入失败", f"导入插件时出错:\n{e}")

    def _build_plugin(self) -> None:
        """从目录打包 .calcplugin。"""
        dir_path = QFileDialog.getExistingDirectory(self, "选择插件源码目录")
        if not dir_path:
            return
        try:
            from tools.plugin_pack import build_plugin

            output, _ = QFileDialog.getSaveFileName(
                self,
                "保存为 .calcplugin",
                "",
                "CalcPlugin (*.calcplugin)",
            )
            if not output:
                return
            result = build_plugin(dir_path, output)
            msg = f"插件已打包: {result.name}"
            if self._status_callback:
                self._status_callback(msg)
            QMessageBox.information(self, "打包成功", f"插件已打包:\n{result}")
        except Exception as e:
            QMessageBox.critical(self, "打包失败", f"打包插件时出错:\n{e}")

        """_refresh。"""

    def _refresh(self) -> None:
        self.accept()
        dialog = PluginManagerDialog(self.parent(), self._status_callback)  # type: ignore[arg-type]
        dialog.exec()
