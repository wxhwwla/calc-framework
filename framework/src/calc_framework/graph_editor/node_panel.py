# SPDX-License-Identifier: AGPL-3.0
"""左侧节点面板 — 按分类列出可用的节点类型，支持拖拽创建。"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QDrag, QFont, QPixmap
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTabWidget,
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


class DraggableTypeList(QWidget):
    """一个分类下的节点类型列表。"""

    def __init__(self, entries: list[tuple[str, str, QColor]], parent: QWidget | None = None) -> None:
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
            from PySide6.QtCore import QMimeData

            drag = QDrag(self)

            mime = QMimeData()

            mime.setText(self._type_id)

            drag.setMimeData(mime)

            drag.exec(Qt.DropAction.CopyAction)


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

            tab = DraggableTypeList(items, self)

            _tab_key_map = {
                "输入": "desktop.graphEditor.tabInput",
                "基础": "desktop.graphEditor.tabBasic",
                "输出": "desktop.graphEditor.tabOutput",
                "包": "desktop.graphEditor.tabPackage",
            }
            tab_label = (
                tr(_tab_key_map.get(cat_name, f"desktop.graphEditor.tab_{cat_name}")) if cat_name in _tab_key_map else cat_name
            )

            self.addTab(tab, tab_label)

        # 包选项卡前面加一个带导入按钮的包装器

        if "包" in cats:
            pkg_idx = self.indexOf(self._find_tab(tr("desktop.graphEditor.tabPackage")))  # type: ignore[arg-type]

            if pkg_idx >= 0:
                old_widget = self.widget(pkg_idx)

                wrapper = QWidget()

                wrapper_layout = QVBoxLayout(wrapper)

                wrapper_layout.setContentsMargins(0, 0, 0, 0)

                wrapper_layout.setSpacing(0)

                import_btn = QPushButton(tr("desktop.graphEditor.importPackageBtnText"))

                import_btn.setFont(QFont("Microsoft YaHei", 10))

                import_btn.setStyleSheet("""

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

                import_btn.clicked.connect(self._on_import_package)

                wrapper_layout.addWidget(import_btn)

                wrapper_layout.addWidget(old_widget, 1)  # type: ignore[arg-type]

                self.removeTab(pkg_idx)

                self.insertTab(pkg_idx, wrapper, tr("desktop.graphEditor.tabPackage"))

    def _find_tab(self, name: str) -> QWidget | None:
        for i in range(self.count()):
            if self.tabText(i) == name:
                return self.widget(i)

        return None

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
