# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""左侧节点面板 — 按分类列出可用的节点类型，支持拖拽创建。"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from PySide6.QtCore import QMimeData, Qt, Signal
from PySide6.QtGui import QColor, QDrag, QFont, QPixmap
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from calc_framework.ui.i18n import tr

from .registry import (
    get_nodes_by_category,
    get_package_manager,
    register_composite_type,
)

# 节点类型对应的颜色（与画布保持一致）

_NODE_TYPE_COLORS: dict[str, QColor] = {
    "const": QColor("#4ECDC4"),
    "var": QColor("#45B7D1"),
    "user_input": QColor("#96CEB4"),
    "unary": QColor("#FFEAA7"),
    "binary": QColor("#FF6B6B"),
    "condition": QColor("#DDA0DD"),
    "output": QColor("#FF8C00"),
}

# 树节点数据角色
_ROLE_TYPE_ID = Qt.ItemDataRole.UserRole + 1


class DraggableTypeList(QWidget):
    """一个分类下的节点类型列表（非"包"分类使用）。"""

    def __init__(
        self,
        entries: list[tuple[str, str, QColor]],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)

        for type_id, display_name, color in entries:
            item = _DraggableListItem(type_id, display_name, color, self)
            layout.addWidget(item)

        layout.addStretch()


class _DraggableListItem(QWidget):
    """可拖拽的单行节点类型项。"""

    def __init__(self, type_id: str, display_name: str, color: QColor, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._type_id = type_id

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(8)

        pix = QPixmap(12, 12)
        pix.fill(color)

        indicator = QLabel()
        indicator.setPixmap(pix)
        indicator.setFixedSize(12, 12)
        layout.addWidget(indicator)

        name_label = QLabel(display_name)
        name_label.setFont(QFont("Microsoft YaHei", 10))
        layout.addWidget(name_label)

        layout.addStretch()

    @property
    def type_id(self) -> str:
        return self._type_id

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            drag = QDrag(self)
            mime = QMimeData()
            mime.setText(self._type_id)
            drag.setMimeData(mime)
            drag.exec(Qt.DropAction.CopyAction)


class PackageTree(QTreeWidget):
    """包标签页的树形视图 — ZIP 包可展开/收起，子图可拖拽。"""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.setHeaderHidden(True)
        self.setRootIsDecorated(True)
        self.setIndentation(16)
        self.setFont(QFont("Microsoft YaHei", 10))

        # 启用拖拽
        self.setDragEnabled(True)
        self.setDragDropMode(QTreeWidget.DragDropMode.DragOnly)

    def populate(self) -> None:
        """从 PackageManager 加载包并填充树。"""
        self.clear()

        pm = get_package_manager()
        packages = pm.loaded_packages()

        for pkg_name, tdefs in packages.items():
            # 包节点（可展开/收起）
            pkg_item = QTreeWidgetItem(self)
            pkg_item.setText(0, f"📦 {pkg_name}")
            pkg_item.setFont(0, QFont("Microsoft YaHei", 10, QFont.Weight.Bold))
            pkg_item.setFlags(pkg_item.flags() & ~Qt.ItemFlag.ItemIsDragEnabled)

            for tdef in tdefs:
                # 子图节点（可拖拽）— 树形下只显示子图名，不重复包名
                graph_name = tdef.type_id.split("/", 1)[1] if "/" in tdef.type_id else tdef.display_name
                child = QTreeWidgetItem(pkg_item)
                child.setText(0, graph_name)
                child.setToolTip(0, tdef.display_name)
                child.setData(0, _ROLE_TYPE_ID, tdef.type_id)
                child.setFlags(child.flags() | Qt.ItemFlag.ItemIsDragEnabled)

            pkg_item.setExpanded(True)

    def mimeData(self, items: Sequence[QTreeWidgetItem]) -> QMimeData:  # noqa: N802
        """支持从树拖拽子图到画布。"""
        mime = QMimeData()
        for item in items:
            type_id = item.data(0, _ROLE_TYPE_ID)
            if type_id:
                mime.setText(type_id)
                break
        return mime


class NodePanel(QTabWidget):
    """左侧节点面板，按分类展示所有可用节点类型。"""

    node_created = Signal(str)
    package_loaded = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.setTabPosition(QTabWidget.TabPosition.North)
        self._build_tabs()

    def _build_tabs(self) -> None:
        self.clear()

        cats = get_nodes_by_category()
        colors = self._colors()
        order = ["输入", "基础", "输出", "包"]

        for cat_name in order:
            if cat_name not in cats:
                continue

            entries = cats[cat_name]
            items = [(e.type_id, e.display_name, colors.get(e.type_id, QColor("#888888"))) for e in entries]

            tab = self._create_package_tab(items) if cat_name == "包" else DraggableTypeList(items, self)
            self.addTab(tab, cat_name)

    def _create_package_tab(self, items: list[tuple[str, str, QColor]]) -> QWidget:
        """创建"包"标签页 — 导入按钮 + 树形包列表。"""
        container = QWidget(self)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 导入按钮
        btn = QPushButton(tr("desktop.graphEditor.importPackageBtnText"))
        btn.setFont(QFont("Microsoft YaHei", 10))
        btn.setStyleSheet("""
            QPushButton {
                background: #094771;
                color: white;
                border: none;
                padding: 6px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background: #1068a0;
            }
        """)
        btn.clicked.connect(self._on_import_package)
        layout.addWidget(btn)

        # 树形包列表
        self._package_tree = PackageTree(container)
        self._package_tree.populate()
        layout.addWidget(self._package_tree, 1)

        return container

    def refresh_package_tab(self) -> None:
        """重新加载包选项卡（导入后调用）。"""
        self._build_tabs()

    def _on_import_package(self) -> None:
        path_str, _ = QFileDialog.getOpenFileName(
            self,
            tr("desktop.graphEditor.importPackage"),
            "",
            "计算包 (*.zip *.json);;ZIP 包 (*.zip);;计算图文件 (*.json)",
        )

        if not path_str:
            return

        path = Path(path_str)
        pm = get_package_manager()

        try:
            if path.suffix.lower() == ".zip":
                tdefs = pm.load_zip(path)

                if not tdefs:
                    QMessageBox.information(
                        self, tr("desktop.graphEditor.importResult"), tr("desktop.graphEditor.noValidJsonInZip")
                    )
                    return

                names = [t.display_name for t in tdefs]
                for t in tdefs:
                    register_composite_type(t)

                QMessageBox.information(
                    self,
                    tr("desktop.graphEditor.importSuccess"),
                    tr(
                        "desktop.graphEditor.importSuccessDetail",
                        package=path.stem,
                        count=len(tdefs),
                        names="\n".join(names),
                    ),
                )

            else:
                tdef = pm.load_json(path)
                register_composite_type(tdef)

                QMessageBox.information(
                    self,
                    tr("desktop.graphEditor.importSuccess"),
                    tr("desktop.graphEditor.importSuccessSingle", name=tdef.display_name),
                )

        except Exception as e:
            QMessageBox.critical(self, tr("desktop.graphEditor.importFailed"), tr("desktop.graphEditor.loadFailed", error=e))
            return

        self.refresh_package_tab()

        # 自动切换到包选项卡
        for i in range(self.count()):
            if self.tabText(i) == tr("desktop.graphEditor.tabPackage"):
                self.setCurrentIndex(i)
                break

        self.package_loaded.emit()

    @staticmethod
    def _colors() -> dict[str, QColor]:
        return dict(_NODE_TYPE_COLORS)

    def find_draggable_item(self, type_id: str) -> _DraggableListItem | None:
        """按类型 ID 查找面板中的拖拽项（用于测试）。"""

        for i in range(self.count()):
            tab = self.widget(i)

            if isinstance(tab, DraggableTypeList) or hasattr(tab, "findChildren"):
                for child in tab.findChildren(_DraggableListItem):
                    if child.type_id == type_id:
                        return child

        return None

    def emit_node_created(self, type_id: str) -> None:
        """测试用 — 模拟拖拽创建节点。"""

        self.node_created.emit(type_id)
