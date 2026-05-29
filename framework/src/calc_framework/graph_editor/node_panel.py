"""左侧节点面板 — 按分类列出可用的节点类型，支持拖拽创建。"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QDrag, QFont, QPixmap
from PySide6.QtWidgets import QHBoxLayout, QLabel, QTabWidget, QVBoxLayout, QWidget

from calc_framework.graph_editor.registry import get_nodes_by_category

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

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            drag = QDrag(self)
            mime = drag.mimeData()
            mime.setText(self._type_id)
            drag.setMimeData(mime)
            drag.exec(Qt.DropAction.CopyAction)


class NodePanel(QTabWidget):
    """左侧节点面板，按分类展示所有可用节点类型。"""

    node_created = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setTabPosition(QTabWidget.TabPosition.West)
        self._build_tabs()

    def _build_tabs(self) -> None:
        cats = get_nodes_by_category()
        colors = self._colors()

        # 定义分类显示顺序
        order = ["输入", "基础", "输出"]
        for cat_name in order:
            if cat_name not in cats:
                continue
            entries = cats[cat_name]
            items = [(e.type_id, e.display_name, colors.get(e.type_id, QColor("#888888")))
                     for e in entries]
            tab = DraggableTypeList(items)
            self.addTab(tab, cat_name)

    @staticmethod
    def _colors() -> dict[str, QColor]:
        return dict(_NODE_TYPE_COLORS)

    def find_draggable_item(self, type_id: str) -> _DraggableListItem | None:
        """按类型 ID 查找面板中的拖拽项（用于测试）。"""
        for i in range(self.count()):
            tab = self.widget(i)
            for child in tab.findChildren(_DraggableListItem):
                if child.type_id == type_id:
                    return child
        return None

    def emit_node_created(self, type_id: str) -> None:
        """发射 node_created 信号（用于测试/编程创建）。"""
        self.node_created.emit(type_id)
