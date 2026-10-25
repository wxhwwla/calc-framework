# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""布局编辑器画布 — 拖拽式布局编辑 + 乘区变量映射。

左侧变量池 → 拖拽到画布上 Section 内 → 保存为 layout.json。
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from calc_framework.logging import get_logger
from calc_framework.ui.i18n import tr
from calc_framework.ui.layout import Section, load_layout
from PySide6.QtCore import QPointF, Qt, Signal
from PySide6.QtGui import (
    QBrush,
    QColor,
    QContextMenuEvent,
    QDragEnterEvent,
    QDragMoveEvent,
    QDropEvent,
    QFont,
    QLinearGradient,
    QMouseEvent,
    QPainter,
    QPen,
    QPixmap,
)
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QGraphicsItem,
    QGraphicsRectItem,
    QGraphicsScene,
    QGraphicsSimpleTextItem,
    QGraphicsView,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

_logger = get_logger(__name__)

_SECTION_COLOR = QColor("#2D2D2D")
_SECTION_BORDER = QColor("#555555")
_CONTROL_COLOR = QColor("#3D3D3D")
_CONTROL_BORDER = QColor("#4ECDC4")
_SECTION_WIDTH = 500
_SECTION_HEADER_H = 28
_CONTROL_H = 30
_CONTROL_MARGIN = 10
_GRID_SIZE = 20


class _ControlItem(QGraphicsRectItem):
    """画布上的一个乘区变量控件。"""

    def __init__(self, var_name: str, label: str, parent_section, parent=None):
        super().__init__(0, 0, _SECTION_WIDTH - _CONTROL_MARGIN * 2, _CONTROL_H, parent)
        self._var_name = var_name
        self._label = label
        self._parent_section = parent_section
        self.setBrush(QBrush(_CONTROL_COLOR))
        self.setPen(QPen(_CONTROL_BORDER, 1))
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAcceptHoverEvents(True)

        text = QGraphicsSimpleTextItem(label, self)
        text.setFont(QFont("Microsoft YaHei", 9))
        text.setBrush(QBrush(QColor("#D1D1D1")))
        text.setPos(8, 6)

        # 删除按钮（×）
        self._del_btn = QGraphicsSimpleTextItem("×", self)
        self._del_btn.setFont(QFont("Microsoft YaHei", 10, QFont.Weight.Bold))
        self._del_btn.setBrush(QBrush(QColor("#FF6B6B")))
        self._del_btn.setPos(_SECTION_WIDTH - _CONTROL_MARGIN * 2 - 20, 5)
        self._del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._del_btn.setVisible(False)

    def hoverEnterEvent(self, event) -> None:  # noqa: N802
        """鼠标悬停时显示删除按钮。"""
        self._del_btn.setVisible(True)
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event) -> None:  # noqa: N802
        """鼠标离开时隐藏删除按钮。"""
        self._del_btn.setVisible(False)
        super().hoverLeaveEvent(event)

    def mousePressEvent(self, event) -> None:  # noqa: N802
        """点击删除按钮时移除此控件。"""
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.pos()
            btn_rect = self._del_btn.boundingRect()
            btn_pos = self._del_btn.pos()
            if (
                pos.x() >= btn_pos.x()
                and pos.x() <= btn_pos.x() + btn_rect.width()
                and pos.y() >= btn_pos.y()
                and pos.y() <= btn_pos.y() + btn_rect.height()
            ):
                if self._parent_section:
                    self._parent_section.remove_control(self._var_name)
                    if self.scene():
                        panel = self.scene().parent()
                        if hasattr(panel, "_on_canvas_changed"):
                            panel._on_canvas_changed()
                return
        super().mousePressEvent(event)

    @property
    def var_name(self) -> str:
        """var_name 实现。"""
        return self._var_name


class _SectionItem(QGraphicsRectItem):
    """画布上的一个 Section 区块。"""

    def __init__(
        self,
        section_id: str,
        title: str,
        section_type: str,
        columns: int,
        widget_type: str = "",
        widget_config: dict | None = None,
        parent=None,
    ):
        h = _SECTION_HEADER_H + _CONTROL_MARGIN
        super().__init__(0, 0, _SECTION_WIDTH, h, parent)
        self._section_id = section_id
        self._section_type = section_type
        self._columns = columns
        self._widget_type = widget_type
        self._widget_config = widget_config or {}
        self._title = title
        self._controls: list[_ControlItem] = []

        grad = QLinearGradient(0, 0, 0, _SECTION_HEADER_H)
        grad.setColorAt(0, QColor("#3D3D3D"))
        grad.setColorAt(1, QColor("#353535"))
        self._header_brush = QBrush(grad)
        self.setBrush(QBrush(_SECTION_COLOR))
        self.setPen(QPen(_SECTION_BORDER, 1))
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self.setAcceptDrops(True)
        self.setAcceptHoverEvents(True)

        title_parts = [title, f"[{section_type}]"]
        if widget_type:
            title_parts.append(f"({widget_type})")
        title_text = " ".join(title_parts)
        self._title_item = QGraphicsSimpleTextItem(title_text, self)
        self._title_item.setFont(QFont("Microsoft YaHei", 10, QFont.Weight.Bold))
        self._title_item.setBrush(QBrush(QColor("#F0F0F0")))
        self._title_item.setPos(8, 5)

        type_tag = QGraphicsSimpleTextItem(f"col={columns}", self)
        type_tag.setFont(QFont("Microsoft YaHei", 8))
        type_tag.setBrush(QBrush(QColor("#888888")))
        type_tag.setPos(_SECTION_WIDTH - 60, 6)

    def add_control(self, var_name: str, label: str) -> _ControlItem:
        """add_control 实现。

        Args:
            var_name: 参数描述。
            label: 参数描述。

        Returns:
            返回值描述。
        """
        ctrl = _ControlItem(var_name, label, self)
        y = _SECTION_HEADER_H + _CONTROL_MARGIN + len(self._controls) * (_CONTROL_H + 4)
        ctrl.setPos(_CONTROL_MARGIN, y)
        self._controls.append(ctrl)
        self._resize_to_fit()
        self._update_header()
        return ctrl

    def remove_control(self, var_name: str) -> bool:
        """remove_control 实现。

        Args:
            var_name: 参数描述。

        Returns:
            返回值描述。
        """
        for ctrl in self._controls[:]:
            if ctrl.var_name == var_name:
                self._controls.remove(ctrl)
                self.scene().removeItem(ctrl)
                self._reposition_controls()
                self._resize_to_fit()
                self._update_header()
                return True
        return False

    def _reposition_controls(self) -> None:
        """_reposition_controls 实现。"""
        for i, ctrl in enumerate(self._controls):
            y = _SECTION_HEADER_H + _CONTROL_MARGIN + i * (_CONTROL_H + 4)
            ctrl.setPos(_CONTROL_MARGIN, y)

    def _update_header(self) -> None:
        """更新标题栏，显示变量名列表。"""
        parts = [self._title, f"[{self._section_type}]"]
        if self._widget_type:
            parts.append(f"({self._widget_type})")

        if self._controls:
            names = [c.var_name for c in self._controls]
            # 显示变量名（缩短：去掉常见前缀）
            short = []
            for n in names:
                for prefix in ("character.", "weapon.", "equipment.", "enemy.", "user.", "user_input.", "computed."):
                    if n.startswith(prefix):
                        n = n[len(prefix) :]
                        break
                short.append(n)
            display = ", ".join(short)
            if len(display) > 60:
                display = display[:57] + "..."
            parts.append(f"  {display}")

        self._title_item.setText(" ".join(parts))

    def _resize_to_fit(self) -> None:
        """_resize_to_fit 实现。"""
        total = _SECTION_HEADER_H + _CONTROL_MARGIN
        if self._controls:
            total += len(self._controls) * (_CONTROL_H + 4) + _CONTROL_MARGIN
        else:
            total += 40
        self.setRect(0, 0, _SECTION_WIDTH, total)

    @property
    def section_id(self) -> str:
        """section_id 实现。"""
        return self._section_id

    @property
    def section_type(self) -> str:
        """section_type 实现。"""
        return self._section_type

    @property
    def section_title(self) -> str:
        """section_title 实现。"""
        return self._title

    def to_section(self) -> Section:
        """to_section 实现。"""
        if self._section_type == "widget":
            return Section(
                id=self._section_id,
                title=self._title,
                type="widget",
                widget_type=self._widget_type,
                widget_config=dict(self._widget_config),
            )
        inp_vars = [
            c.var_name
            for c in self._controls
            if c.var_name.startswith("character.")
            or c.var_name.startswith("weapon.")
            or c.var_name.startswith("equipment.")
            or c.var_name.startswith("enemy.")
            or c.var_name.startswith("user.")
        ]
        out_vars = [
            c.var_name
            for c in self._controls
            if not (
                c.var_name.startswith("character.")
                or c.var_name.startswith("weapon.")
                or c.var_name.startswith("equipment.")
                or c.var_name.startswith("enemy.")
                or c.var_name.startswith("user.")
            )
        ]
        if self._section_type == "inputs":
            return Section(
                id=self._section_id,
                title=self._title,
                type="inputs",
                variables=inp_vars,
                outputs=[],
                columns=self._columns,
            )
        else:
            return Section(
                id=self._section_id,
                title=self._title,
                type="outputs",
                variables=[],
                outputs=out_vars,
                columns=self._columns,
            )


class SectionEditDialog(QDialog):
    """新建/编辑 Section 的对话框。"""

    def __init__(self, title="", section_type="inputs", columns=2, widget_type="", parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("desktop.packDesigner.sectionDialogTitle"))
        self._result: dict | None = None
        layout = QFormLayout(self)

        self._title_edit = QLineEdit(title)
        layout.addRow(tr("desktop.packDesigner.fieldTitle"), self._title_edit)

        self._type_combo = QComboBox()
        self._type_combo.addItems(["inputs", "outputs", "widget"])
        self._type_combo.setCurrentText(section_type)
        self._type_combo.currentTextChanged.connect(self._on_type_changed)
        layout.addRow(tr("desktop.packDesigner.fieldType"), self._type_combo)

        self._widget_type_combo = QComboBox()
        self._widget_type_combo.addItems(["donation"])
        self._widget_type_combo.setCurrentText(widget_type or "donation")
        self._widget_type_label = QLabel(tr("desktop.packDesigner.fieldWidgetType"))
        layout.addRow(self._widget_type_label, self._widget_type_combo)

        self._cols_spin = QSpinBox()
        self._cols_spin.setRange(1, 6)
        self._cols_spin.setValue(columns)
        layout.addRow(tr("desktop.packDesigner.fieldColumns"), self._cols_spin)

        btns = QHBoxLayout()
        ok_btn = QPushButton(tr("common.ok"))
        ok_btn.clicked.connect(self._accept)
        cancel_btn = QPushButton(tr("common.cancel"))
        cancel_btn.clicked.connect(self.reject)
        btns.addWidget(ok_btn)
        btns.addWidget(cancel_btn)
        layout.addRow(btns)

        self._on_type_changed(section_type)

    def _on_type_changed(self, sec_type: str) -> None:
        """_on_type_changed 实现。"""
        is_widget = sec_type == "widget"
        self._widget_type_combo.setVisible(is_widget)
        self._widget_type_label.setVisible(is_widget)
        self._cols_spin.setVisible(not is_widget)

    def _accept(self) -> None:
        """_accept 实现。"""
        self._result = {
            "title": self._title_edit.text() or tr("desktop.packDesigner.defaultSectionTitle"),
            "type": self._type_combo.currentText(),
            "columns": self._cols_spin.value(),
            "widget_type": self._widget_type_combo.currentText() if self._type_combo.currentText() == "widget" else "",
        }
        self.accept()

    @property
    def section_result(self) -> dict | None:
        """section_result 实现。"""
        return self._result


class DonationConfigDialog(QDialog):
    """配置捐赠组件的文字和图片。"""

    def __init__(self, text="", image_path="", parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("desktop.packDesigner.donationDialogTitle"))
        self.setMinimumWidth(450)
        self._result: dict | None = None

        layout = QFormLayout(self)

        self._text_edit = QLineEdit(text or tr("desktop.packDesigner.donationDefaultText"))
        layout.addRow(tr("desktop.packDesigner.fieldDescription"), self._text_edit)

        path_layout = QHBoxLayout()
        self._path_edit = QLineEdit(image_path)
        self._path_edit.setPlaceholderText(tr("desktop.packDesigner.donationImagePlaceholder"))
        path_layout.addWidget(self._path_edit, stretch=1)
        browse_btn = QPushButton(tr("desktop.packDesigner.browse"))
        browse_btn.clicked.connect(self._browse_image)
        path_layout.addWidget(browse_btn)
        layout.addRow(tr("desktop.packDesigner.fieldImagePath"), path_layout)

        btns = QHBoxLayout()
        ok_btn = QPushButton(tr("common.ok"))
        ok_btn.clicked.connect(self._accept)
        cancel_btn = QPushButton(tr("common.cancel"))
        cancel_btn.clicked.connect(self.reject)
        btns.addWidget(ok_btn)
        btns.addWidget(cancel_btn)
        layout.addRow(btns)

    def _browse_image(self) -> None:
        """_browse_image 实现。"""
        path, _ = QFileDialog.getOpenFileName(
            self,
            tr("desktop.packDesigner.selectDonationImage"),
            "",
            tr("desktop.packDesigner.imageFilter"),
        )
        if path:
            self._path_edit.setText(path)

    def _accept(self) -> None:
        """_accept 实现。"""
        self._result = {
            "text": self._text_edit.text().strip(),
            "image_path": self._path_edit.text().strip(),
        }
        self.accept()

    @property
    def config_result(self) -> dict | None:
        """config_result 实现。"""
        return self._result


class _DragListWidget(QListWidget):
    """支持拖拽文本的 QListWidget。"""

    def mimeData(self, items):  # noqa: N802
        """确保拖拽时提供文本 MIME 数据。"""
        from PySide6.QtCore import QMimeData

        mime = QMimeData()
        if items:
            mime.setText(items[0].text())
        return mime


class _DropView(QGraphicsView):
    """支持拖放 + Ctrl+滚轮缩放的 QGraphicsView。"""

    ZOOM_MIN = 0.25  # 最小缩放 25%
    ZOOM_MAX = 4.0  # 最大缩放 400%
    ZOOM_STEP = 0.15  # 每次滚轮缩放步长

    drop_callback = None
    zoom_changed = None  # 回调 (zoom_factor: float) -> None
    delete_callback = None  # 回调 () -> None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._zoom_factor = 1.0

    def wheelEvent(self, event) -> None:  # noqa: N802
        """Ctrl+滚轮缩放画布，普通滚轮平移。"""
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            delta = event.angleDelta().y()
            if delta > 0:
                new_zoom = min(self._zoom_factor * (1 + self.ZOOM_STEP), self.ZOOM_MAX)
            else:
                new_zoom = max(self._zoom_factor * (1 - self.ZOOM_STEP), self.ZOOM_MIN)

            if new_zoom != self._zoom_factor:
                # 以鼠标位置为中心缩放
                anchor = self.transformationAnchor()
                self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
                ratio = new_zoom / self._zoom_factor
                self.scale(ratio, ratio)
                self.setTransformationAnchor(anchor)
                self._zoom_factor = new_zoom
                if self.zoom_changed:
                    self.zoom_changed(self._zoom_factor)
            event.accept()
        else:
            super().wheelEvent(event)

    def reset_zoom(self) -> None:
        """重置缩放到 100%。"""
        if self._zoom_factor != 1.0:
            ratio = 1.0 / self._zoom_factor
            self.scale(ratio, ratio)
            self._zoom_factor = 1.0
            if self.zoom_changed:
                self.zoom_changed(self._zoom_factor)

    def set_zoom(self, factor: float) -> None:
        """设置指定缩放比例。"""
        factor = max(self.ZOOM_MIN, min(self.ZOOM_MAX, factor))
        if factor != self._zoom_factor:
            ratio = factor / self._zoom_factor
            self.scale(ratio, ratio)
            self._zoom_factor = factor
            if self.zoom_changed:
                self.zoom_changed(self._zoom_factor)

    @property
    def zoom_factor(self) -> float:
        """当前缩放比例。"""
        return self._zoom_factor

    def keyPressEvent(self, event) -> None:  # noqa: N802
        """Delete 键删除选中项。"""
        if event.key() == Qt.Key.Key_Delete and self.delete_callback:
            self.delete_callback()
        else:
            super().keyPressEvent(event)

    def contextMenuEvent(self, event: QContextMenuEvent) -> None:  # noqa: N802
        """禁用右键菜单。"""
        event.accept()

    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        """按下中键时切换为拖拽模式（平移画布）。"""
        if event.button() == Qt.MouseButton.MiddleButton:
            self._saved_drag_mode = self.dragMode()
            self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
            # 伪造一个左键按下事件，让 ScrollHandDrag 开始拖拽
            fake = QMouseEvent(
                event.type(),
                event.position(),
                event.globalPosition(),
                Qt.MouseButton.LeftButton,
                Qt.MouseButton.LeftButton,
                event.modifiers(),
            )
            super().mousePressEvent(fake)
        else:
            super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        """释放中键时恢复原来的拖拽模式。"""
        if event.button() == Qt.MouseButton.MiddleButton:
            fake = QMouseEvent(
                event.type(),
                event.position(),
                event.globalPosition(),
                Qt.MouseButton.LeftButton,
                Qt.MouseButton.NoButton,
                event.modifiers(),
            )
            super().mouseReleaseEvent(fake)
            self.setDragMode(getattr(self, "_saved_drag_mode", QGraphicsView.DragMode.RubberBandDrag))
        else:
            super().mouseReleaseEvent(event)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:  # noqa: N802
        if event.mimeData().hasText():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event: QDragMoveEvent) -> None:  # noqa: N802
        if event.mimeData().hasText():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:  # noqa: N802
        if self.drop_callback and event.mimeData().hasText():
            self.drop_callback(event.position(), event.mimeData().text())
            event.acceptProposedAction()
        else:
            event.ignore()


class LayoutCanvasPanel(QWidget):
    """布局编辑器面板 — 拖拽式 Section + 控件放置。"""

    layout_changed = Signal(object)  # layout_data dict

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._dag_service = None
        self._adapter_name = ""
        self._dag_data: dict | None = None
        self._section_id_counter = 0
        self._build_ui()

    def _build_ui(self) -> None:
        """_build_ui 实现。"""
        layout = QVBoxLayout(self)

        toolbar = QHBoxLayout()

        add_section_btn = QPushButton(tr("desktop.packDesigner.addSection"))
        add_section_btn.clicked.connect(self._add_section)
        toolbar.addWidget(add_section_btn)

        del_section_btn = QPushButton(tr("desktop.packDesigner.deleteSelected"))
        del_section_btn.clicked.connect(self._delete_selected)
        toolbar.addWidget(del_section_btn)

        donation_section_btn = QPushButton(tr("desktop.packDesigner.addDonation"))
        donation_section_btn.setStyleSheet("QPushButton { color: #e74c3c; }")
        donation_section_btn.clicked.connect(self._add_donation_section)
        toolbar.addWidget(donation_section_btn)

        toolbar.addWidget(QLabel(tr("desktop.packDesigner.adapterLabel")))
        self._adapter_selector = QComboBox()
        self._adapter_selector.setMinimumWidth(160)
        self._adapter_selector.currentIndexChanged.connect(self._on_adapter_selected)
        toolbar.addWidget(self._adapter_selector)

        clear_btn = QPushButton(tr("desktop.packDesigner.clearCanvas"))
        clear_btn.clicked.connect(self._clear_canvas)
        toolbar.addWidget(clear_btn)

        preview_btn = QPushButton(tr("desktop.packDesigner.renderPreview"))
        preview_btn.clicked.connect(self._open_preview)
        toolbar.addWidget(preview_btn)

        save_btn = QPushButton(tr("desktop.packDesigner.saveLayout"))
        save_btn.clicked.connect(self._save_layout)
        save_btn.setStyleSheet("QPushButton { font-weight: bold; }")
        toolbar.addWidget(save_btn)

        toolbar.addStretch()
        layout.addLayout(toolbar)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        left = QWidget()
        left_layout = QVBoxLayout(left)

        left_layout.addWidget(QLabel(tr("desktop.packDesigner.inputVarsHint")))
        self._var_list = _DragListWidget()
        self._var_list.setDragEnabled(True)
        self._var_list.setAcceptDrops(False)
        self._var_list.setDragDropMode(QAbstractItemView.DragDropMode.DragOnly)
        self._var_list.setDefaultDropAction(Qt.DropAction.CopyAction)
        self._var_list.setStyleSheet("QListWidget::item { padding: 4px; }")
        left_layout.addWidget(self._var_list)

        left_layout.addWidget(QLabel(tr("desktop.packDesigner.outputVarsHint")))
        self._output_list = _DragListWidget()
        self._output_list.setDragEnabled(True)
        self._output_list.setAcceptDrops(False)
        self._output_list.setDragDropMode(QAbstractItemView.DragDropMode.DragOnly)
        self._output_list.setDefaultDropAction(Qt.DropAction.CopyAction)
        self._output_list.setStyleSheet("QListWidget::item { padding: 4px; }")
        left_layout.addWidget(self._output_list)

        splitter.addWidget(left)

        self._scene = QGraphicsScene()
        self._scene.setSceneRect(0, 0, 3000, 2000)

        self._view = _DropView(self._scene)
        self._view.drop_callback = self._on_drop_on_canvas
        self._view.zoom_changed = self._on_zoom_changed
        self._view.delete_callback = self._delete_selected
        self._view.setAcceptDrops(True)
        self._view.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self._view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self._view.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self._set_grid_background()
        splitter.addWidget(self._view)

        right = QWidget()
        self._right_layout = QVBoxLayout(right)
        self._right_layout.addWidget(QLabel(tr("desktop.packDesigner.propsHeading")))
        self._prop_group = QGroupBox(tr("desktop.packDesigner.selectedItem"))
        prop_form = QFormLayout(self._prop_group)
        self._prop_title = QLabel(tr("desktop.packDesigner.noneSelected"))
        prop_form.addRow("", self._prop_title)

        # 重命名行
        rename_row = QHBoxLayout()
        self._rename_edit = QLineEdit()
        self._rename_edit.setPlaceholderText(tr("desktop.packDesigner.renamePlaceholder"))
        self._rename_btn = QPushButton(tr("desktop.packDesigner.rename"))
        self._rename_btn.setFixedWidth(48)
        self._rename_btn.clicked.connect(self._rename_selected_section)
        rename_row.addWidget(self._rename_edit)
        rename_row.addWidget(self._rename_btn)
        self._rename_widget = QWidget()
        self._rename_widget.setLayout(rename_row)
        self._rename_widget.setVisible(False)
        prop_form.addRow(tr("desktop.packDesigner.renameLabel"), self._rename_widget)

        self._prop_detail = QLabel("")
        self._prop_detail.setWordWrap(True)
        prop_form.addRow(tr("desktop.packDesigner.detailLabel"), self._prop_detail)
        self._right_layout.addWidget(self._prop_group)
        self._right_layout.addStretch()
        splitter.addWidget(right)

        splitter.setSizes([200, 550, 180])
        layout.addWidget(splitter, stretch=1)

        # 缩放控件（放在 _view 创建之后，因为依赖 self._view）
        zoom_bar = QHBoxLayout()
        zoom_bar.addStretch()
        zoom_bar.addWidget(QLabel(tr("desktop.packDesigner.zoomLabel")))

        zoom_out_btn = QPushButton("➖")
        zoom_out_btn.setFixedWidth(32)
        zoom_out_btn.setToolTip(tr("desktop.packDesigner.zoomOutTip"))
        zoom_out_btn.clicked.connect(lambda: self._view.set_zoom(self._view.zoom_factor * 0.8))
        zoom_bar.addWidget(zoom_out_btn)

        self._zoom_label = QLabel("100%")
        self._zoom_label.setFixedWidth(48)
        self._zoom_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._zoom_label.setStyleSheet("QLabel { font-size: 11px; color: #AAAAAA; }")
        zoom_bar.addWidget(self._zoom_label)

        zoom_in_btn = QPushButton("➕")
        zoom_in_btn.setFixedWidth(32)
        zoom_in_btn.setToolTip(tr("desktop.packDesigner.zoomInTip"))
        zoom_in_btn.clicked.connect(lambda: self._view.set_zoom(self._view.zoom_factor * 1.2))
        zoom_bar.addWidget(zoom_in_btn)

        zoom_reset_btn = QPushButton(tr("common.reset"))
        zoom_reset_btn.setFixedWidth(48)
        zoom_reset_btn.setToolTip(tr("desktop.packDesigner.zoomResetTip"))
        zoom_reset_btn.clicked.connect(self._view.reset_zoom)
        zoom_bar.addWidget(zoom_reset_btn)
        zoom_bar.addStretch()
        layout.addLayout(zoom_bar)

        self._status_label = QLabel(tr("desktop.packDesigner.canvasReady"))
        layout.addWidget(self._status_label)

        self._scene.selectionChanged.connect(self._on_selection_changed)

    def _set_grid_background(self) -> None:
        """_set_grid_background 实现。"""
        pix = QPixmap(_GRID_SIZE * 2, _GRID_SIZE * 2)
        pix.fill(QColor("#1E1E1E"))
        from PySide6.QtGui import QPainter

        p = QPainter(pix)
        p.setPen(QPen(QColor("#2A2A2A"), 1))
        p.drawPoint(0, 0)
        p.drawPoint(_GRID_SIZE, 0)
        p.drawPoint(0, _GRID_SIZE)
        p.drawPoint(_GRID_SIZE, _GRID_SIZE)
        p.end()
        self._view.setBackgroundBrush(QBrush(pix))

    def _add_section(self) -> None:
        """_add_section 实现。"""
        dialog = SectionEditDialog(parent=self)
        if dialog.exec() != QDialog.DialogCode.Accepted or not dialog.section_result:
            return
        r = dialog.section_result
        self._section_id_counter += 1
        sid = f"section_{self._section_id_counter}"
        sec_item = _SectionItem(sid, r["title"], r["type"], r["columns"], r.get("widget_type", ""))
        # 在当前视图中心位置创建 Section
        center = self._view.mapToScene(self._view.viewport().rect().center())
        x = center.x() - _SECTION_WIDTH / 2
        y = center.y() - 50
        sec_item.setPos(x, y)
        self._scene.addItem(sec_item)
        self._view.centerOn(sec_item)
        self._status_label.setText(tr("desktop.packDesigner.statusAddedSection", title=r["title"]))
        self._emit_layout_changed()
        _logger.debug("added section %s (%s) at (%.0f, %.0f)", r["title"], r["type"], x, y)

    def _add_donation_section(self) -> None:
        """_add_donation_section 实现。"""
        dialog = DonationConfigDialog(parent=self)
        if dialog.exec() != QDialog.DialogCode.Accepted or not dialog.config_result:
            return
        cfg = dialog.config_result
        self._section_id_counter += 1
        sid = f"widget_donation_{self._section_id_counter}"
        sec_item = _SectionItem(
            sid,
            tr("desktop.packDesigner.donationSectionTitle"),
            "widget",
            1,
            widget_type="donation",
            widget_config=cfg,
        )
        x = 30 + (self._section_id_counter % 3) * 40
        y = 30 + (self._section_id_counter % 3) * 30
        sec_item.setPos(x, y)
        sec_item._resize_to_fit()
        self._scene.addItem(sec_item)
        self._status_label.setText(tr("desktop.packDesigner.statusAddedDonation"))
        self._emit_layout_changed()

    def _delete_selected(self) -> None:
        """_delete_selected 实现。"""
        for item in self._scene.selectedItems():
            if isinstance(item, _SectionItem):
                self._scene.removeItem(item)
                self._status_label.setText(tr("desktop.packDesigner.statusDeletedSection", title=item.section_title))
            elif isinstance(item, _ControlItem):
                if item._parent_section:
                    item._parent_section.remove_control(item.var_name)
                    self._status_label.setText(tr("desktop.packDesigner.statusDeletedVar", name=item.var_name))
        self._on_canvas_changed()

    def _clear_canvas(self) -> None:
        """_clear_canvas 实现。"""
        self._scene.clear()
        self._set_grid_background()
        self._section_id_counter = 0
        self._status_label.setText(tr("desktop.packDesigner.statusCanvasCleared"))
        self._emit_layout_changed()

    def _on_drop_on_canvas(self, scene_pos: QPointF, text: str) -> None:
        """_on_drop_on_canvas 实现。"""
        _logger.debug("drop received text=%r pos=(%.1f, %.1f)", text, scene_pos.x(), scene_pos.y())
        var_name = text.split("  [")[0].strip()
        if not var_name:
            _logger.debug("drop ignored: empty var name")
            return
        scene_pt = self._view.mapToScene(int(scene_pos.x()), int(scene_pos.y()))
        sec_item = self._find_section_at(scene_pt)
        if sec_item is None:
            _logger.debug("drop: no section at (%.1f, %.1f)", scene_pt.x(), scene_pt.y())
            QMessageBox.information(
                self,
                tr("common.info"),
                tr("desktop.packDesigner.dropNeedSection"),
            )
            return
        for existing in sec_item._controls:
            if existing.var_name == var_name:
                self._status_label.setText(tr("desktop.packDesigner.statusVarExists", name=var_name))
                return
        sec_item.add_control(var_name, var_name)
        self._status_label.setText(
            tr(
                "desktop.packDesigner.statusAddedVar",
                name=var_name,
                section=sec_item.section_title,
            )
        )
        self._on_canvas_changed()
        _logger.debug("drop added var %s", var_name)

    def _find_section_at(self, scene_pt: QPointF) -> _SectionItem | None:
        """_find_section_at 实现。"""
        for item in self._scene.items(scene_pt):
            if isinstance(item, _SectionItem):
                return item
            parent = item.parentItem()
            while parent:
                if isinstance(parent, _SectionItem):
                    return parent
                parent = parent.parentItem()
        return None

    def _on_selection_changed(self) -> None:
        """_on_selection_changed 实现。"""
        selected = self._scene.selectedItems()
        if not selected:
            self._prop_title.setText(tr("desktop.packDesigner.noneSelected"))
            self._prop_detail.setText("")
            self._rename_widget.setVisible(False)
            return
        item = selected[0]
        if isinstance(item, _SectionItem):
            self._prop_title.setText(tr("desktop.packDesigner.propSectionTitle", title=item.section_title))
            self._rename_widget.setVisible(True)
            self._rename_edit.setText(item.section_title)
            # 详细信息：类型 + 控件列表
            lines = [
                tr("desktop.packDesigner.propType", type=item.section_type),
                tr("desktop.packDesigner.propControlCount", n=len(item._controls)),
            ]
            if item._controls:
                lines.append("---")
                for c in item._controls:
                    lines.append(f"  {c.var_name}")
            self._prop_detail.setText("\n".join(lines))
        elif isinstance(item, _ControlItem):
            self._prop_title.setText(tr("desktop.packDesigner.propControlTitle", name=item.var_name))
            self._rename_widget.setVisible(False)
            self._prop_detail.setText(tr("desktop.packDesigner.propLabel", label=item._label))
        else:
            self._prop_title.setText(type(item).__name__)
            self._rename_widget.setVisible(False)

    def _rename_selected_section(self) -> None:
        """重命名选中的 Section。"""
        selected = self._scene.selectedItems()
        if not selected or not isinstance(selected[0], _SectionItem):
            return
        new_title = self._rename_edit.text().strip()
        if not new_title:
            return
        sec = selected[0]
        sec._title = new_title
        sec._update_header()
        self._on_selection_changed()
        self._emit_layout_changed()
        self._status_label.setText(tr("desktop.packDesigner.statusRenamed", title=new_title))

    def _on_canvas_changed(self) -> None:
        """画布内容变化后刷新右侧面板和信号。"""
        self._on_selection_changed()
        self._emit_layout_changed()

    def _on_zoom_changed(self, zoom_factor: float) -> None:
        """缩放比例变化时更新状态栏显示。"""
        self._zoom_label.setText(f"{zoom_factor * 100:.0f}%")

    def populate_adapters(self, names: list[str]) -> None:
        """populate_adapters 实现。

        Args:
            names: 参数描述。

        Returns:
            返回值描述。
        """
        self._adapter_selector.blockSignals(True)
        current = self._adapter_selector.currentText()
        self._adapter_selector.clear()
        self._adapter_selector.addItem(tr("desktop.packDesigner.selectAdapterPlaceholder"))
        for name in names:
            self._adapter_selector.addItem(name)
        idx = self._adapter_selector.findText(current)
        if idx >= 0:
            self._adapter_selector.setCurrentIndex(idx)
        self._adapter_selector.blockSignals(False)

    def _on_adapter_selected(self, index: int) -> None:
        """_on_adapter_selected 实现。"""
        if index <= 0:
            return
        name = self._adapter_selector.currentText()
        self._adapter_name = name
        try:
            from calc_framework.config.manager import AdapterManager

            mgr = AdapterManager()
            pkg = mgr.load(name)
            self._dag_service = pkg.dag_service
            self._dag_data = {"from_adapter": name}

            self._var_list.clear()
            self._output_list.clear()
            for var_name, var_def in pkg.dag_service.dag.variables.items():
                source = var_def.source if hasattr(var_def, "source") else ""
                item = QListWidgetItem(f"{var_name}  [{source}]")
                item.setData(Qt.ItemDataRole.UserRole, var_name)
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsDragEnabled)
                if source in ("character", "weapon", "equipment", "enemy", "user_input"):
                    self._var_list.addItem(item)
                else:
                    self._output_list.addItem(item)

            layout_path = Path(str(pkg._adapter_dir)) / "ui" / "layout.json"
            if layout_path.is_file():
                data = json.loads(layout_path.read_text(encoding="utf-8"))
                self._load_layout_to_canvas(data)
                self._status_label.setText(
                    tr(
                        "desktop.packDesigner.statusLoadedWithLayout",
                        name=name,
                        n=len(pkg.dag_service.dag.variables),
                    )
                )
            else:
                self._status_label.setText(
                    tr(
                        "desktop.packDesigner.statusLoadedNoLayout",
                        name=name,
                        n=len(pkg.dag_service.dag.variables),
                    )
                )
        except Exception as exc:
            QMessageBox.warning(self, tr("desktop.packDesigner.loadFailed"), str(exc))

    def _load_layout_to_canvas(self, data: dict) -> None:
        """_load_layout_to_canvas 实现。"""
        self._scene.clear()
        self._set_grid_background()
        try:
            layout = load_layout(data)
        except Exception as exc:
            _logger.warning("布局数据加载失败，跳过: %s", exc)
            return
        self._section_id_counter = 0
        for i, sec in enumerate(layout.sections):
            self._section_id_counter += 1
            sec_item = _SectionItem(sec.id, sec.title, sec.type, sec.columns, sec.widget_type, dict(sec.widget_config))
            sec_item.setPos(30 + (i % 2) * 60, 30 + (i % 2) * 30)
            self._scene.addItem(sec_item)
            if sec.type == "widget":
                sec_item._resize_to_fit()
                continue
            for var_name in sec.variables:
                sec_item.add_control(var_name, var_name)
            for out_name in sec.outputs:
                sec_item.add_control(out_name, out_name)

    def _emit_layout_changed(self) -> None:
        """_emit_layout_changed 实现。"""
        data = self._build_layout_data()
        self.layout_changed.emit(data)

    def _build_layout_data(self) -> dict:
        """_build_layout_data 实现。"""
        sections = []
        for item in self._scene.items():
            if isinstance(item, _SectionItem):
                sec = item.to_section()
                sections.append(
                    {
                        "id": sec.id,
                        "type": sec.type,
                        "title": sec.title,
                        "variables": sec.variables,
                        "outputs": sec.outputs,
                        "columns": sec.columns,
                        "widget_type": sec.widget_type,
                        "widget_config": sec.widget_config,
                    }
                )
        return {
            "schema_version": "ui-v1",
            "name": self._adapter_name or "Computed Layout",
            "description": "",
            "sections": sections,
        }

    def _save_layout(self) -> None:
        """_save_layout 实现。"""
        if not self._adapter_name or self._adapter_selector.currentIndex() <= 0:
            QMessageBox.information(self, tr("common.info"), tr("desktop.packDesigner.needAdapter"))
            return
        from calc_framework.config.manager import AdapterManager

        mgr = AdapterManager()
        pkg = mgr.load(self._adapter_name)
        adapter_path = Path(str(pkg._adapter_dir))
        ui_dir = adapter_path / "ui"
        ui_dir.mkdir(parents=True, exist_ok=True)
        data = self._build_layout_data()
        path = ui_dir / "layout.json"
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        self._status_label.setText(tr("desktop.packDesigner.statusLayoutSaved", path=path))
        self._emit_layout_changed()

    def _open_preview(self) -> None:
        """_open_preview 实现。"""
        from calc_framework.ui.compute_sheet import ComputeSheet
        from calc_framework.ui.layout import load_layout

        data = self._build_layout_data()
        if not data["sections"]:
            QMessageBox.information(self, tr("common.info"), tr("desktop.packDesigner.previewEmpty"))
            return
        if not self._dag_service:
            QMessageBox.information(self, tr("common.info"), tr("desktop.packDesigner.previewNeedDag"))
            return

        dialog = QDialog(self)
        dialog.setWindowTitle(tr("desktop.packDesigner.previewTitle", name=self._adapter_name))
        dialog.resize(900, 600)
        dl = QVBoxLayout(dialog)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        cl = QVBoxLayout(container)
        try:
            layout_obj = load_layout(data)
            sheet = ComputeSheet(
                dag_service=self._dag_service,
                layout=layout_obj,
                variables=self._dag_service.dag.variables,
                base_context={},
                parent=container,
            )
            cl.addWidget(sheet.widget)
            cl.addStretch()
            scroll.setWidget(container)
            dl.addWidget(scroll)
            sheet.evaluate()
        except Exception as e:
            dl.addWidget(QLabel(tr("desktop.packDesigner.previewRenderFailed", error=e)))
        close_btn = QPushButton(tr("common.close"))
        close_btn.clicked.connect(dialog.accept)
        dl.addWidget(close_btn)
        dialog.exec()

    def get_layout_data(self) -> dict | None:
        """get_layout_data 实现。"""
        if not self._adapter_selector.currentIndex():
            return None
        return self._build_layout_data()

    def get_dag_service(self):
        """get_dag_service 实现。"""
        return self._dag_service

    def get_adapter_name(self) -> str:
        """get_adapter_name 实现。"""
        return self._adapter_name
