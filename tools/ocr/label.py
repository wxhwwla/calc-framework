#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""
截图标注工具（PySide6）— 为 TorchVision 检测模型标注终末地 UI 区域。

用法:
    python -m tools.ocr.label                      # 弹文件夹选择对话框
    python -m tools.ocr.label --input ./截图       # 指定截图文件夹
    python -m tools.ocr.label --input ./截图 --output ./终末地数据集/yolo
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

try:
    from PySide6.QtCore import Qt, QRectF, QPointF
    from PySide6.QtGui import QPixmap, QPainter, QPen, QColor, QFont, QKeyEvent, QMouseEvent, QWheelEvent
    from PySide6.QtWidgets import (
        QApplication, QWidget, QVBoxLayout, QHBoxLayout,
        QPushButton, QLabel, QComboBox, QScrollArea,
        QFileDialog, QMessageBox, QSplitter, QListWidget,
        QListWidgetItem, QSpinBox, QCheckBox,
    )
except ImportError:
    QApplication = None


# 终末地 UI 区域类别（与 endfield_classes.yaml 同步）
CLASS_NAMES = [
    "character_panel",   # 0: 角色面板
    "weapon_panel",      # 1: 武器面板
    "equipment_panel",   # 2: 装备面板
    "skill_panel",       # 3: 技能面板
    "zone_values",       # 4: 乘区数值
    "enemy_panel",       # 5: 敌方面板
]

CLASS_COLORS = [
    "#FF4444", "#44FF44", "#4488FF", "#FFDD44", "#FF44FF", "#44FFFF",
]


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="终末地截图标注工具")
    parser.add_argument("--input", "-i", default=None, help="截图文件夹路径")
    parser.add_argument("--output", "-o", default=None, help="YOLO 数据集输出路径")
    return parser.parse_args()


class Canvas(QLabel):
    """标注画布 — 显示图片 + 绘制/编辑/删除标注框。"""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._pixmap: QPixmap | None = None
        self._scale: float = 1.0
        self._offset_x: float = 0.0
        self._offset_y: float = 0.0

        self._boxes: list[_Box] = []
        self._selected_idx: int | None = None

        self._drawing: bool = False
        self._draw_start: QPointF | None = None
        self._draw_end: QPointF | None = None

        self._current_class: int = 0

        self.setMouseTracking(True)
        self.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.setMinimumSize(400, 300)
        self.setStyleSheet("background-color: #1E1E1E;")

    def load_image(self, path: Path) -> None:
        self._pixmap = QPixmap(str(path))
        if self._pixmap.isNull():
            return
        self._fit_image()
        self._boxes = []
        self._selected_idx = None
        self._load_existing_labels(path)
        self.update()

    def _fit_image(self) -> None:
        if self._pixmap is None:
            return
        view_w = self.width() - 4
        view_h = self.height() - 4
        img_w = self._pixmap.width()
        img_h = self._pixmap.height()
        self._scale = min(view_w / img_w, view_h / img_h, 1.0)
        self._offset_x = (view_w - img_w * self._scale) / 2
        self._offset_y = (view_h - img_h * self._scale) / 2

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if self._pixmap:
            self._fit_image()
            self.update()

    def set_current_class(self, cls_id: int) -> None:
        self._current_class = cls_id

    def _img_to_canvas(self, x: float, y: float) -> tuple[float, float]:
        return (x * self._scale + self._offset_x, y * self._scale + self._offset_y)

    def _canvas_to_img(self, x: float, y: float) -> tuple[float, float]:
        return ((x - self._offset_x) / self._scale, (y - self._offset_y) / self._scale)

    def mousePressEvent(self, event: QMouseEvent | None) -> None:
        if event is None or self._pixmap is None:
            return
        pos = event.position()
        img_x, img_y = self._canvas_to_img(pos.x(), pos.y())
        if img_x < 0 or img_y < 0 or img_x > self._pixmap.width() or img_y > self._pixmap.height():
            return

        if event.button() == Qt.MouseButton.LeftButton:
            self._drawing = True
            self._draw_start = QPointF(img_x, img_y)
            self._draw_end = QPointF(img_x, img_y)

        elif event.button() == Qt.MouseButton.RightButton:
            idx = self._hit_test(img_x, img_y)
            if idx is not None:
                self._boxes.pop(idx)
                self._selected_idx = None
                self.update()

    def mouseMoveEvent(self, event: QMouseEvent | None) -> None:
        if event is None or not self._drawing or self._draw_start is None:
            return
        pos = event.position()
        img_x, img_y = self._canvas_to_img(pos.x(), pos.y())
        self._draw_end = QPointF(img_x, img_y)
        self.update()

    def mouseReleaseEvent(self, event: QMouseEvent | None) -> None:
        if event is None or not self._drawing or self._draw_start is None or self._draw_end is None:
            return
        self._drawing = False

        x1 = min(self._draw_start.x(), self._draw_end.x())
        y1 = min(self._draw_start.y(), self._draw_end.y())
        x2 = max(self._draw_start.x(), self._draw_end.x())
        y2 = max(self._draw_start.y(), self._draw_end.y())

        if (x2 - x1) > 5 and (y2 - y1) > 5:
            box = _Box(
                class_id=self._current_class,
                x1=x1, y1=y1, x2=x2, y2=y2,
            )
            self._boxes.append(box)
            self._selected_idx = len(self._boxes) - 1

        self._draw_start = None
        self._draw_end = None
        self.update()

    def _hit_test(self, img_x: float, img_y: float) -> int | None:
        for i, box in enumerate(reversed(self._boxes)):
            if box.x1 <= img_x <= box.x2 and box.y1 <= img_y <= box.y2:
                return len(self._boxes) - 1 - i
        return None

    def _load_existing_labels(self, image_path: Path) -> None:
        label_path = image_path.with_suffix(".txt")
        if not label_path.exists():
            return
        img_w = self._pixmap.width() if self._pixmap else 1
        img_h = self._pixmap.height() if self._pixmap else 1
        for line in label_path.read_text(encoding="utf-8").strip().split("\n"):
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) != 5:
                continue
            cls_id = int(parts[0])
            cx = float(parts[1]) * img_w
            cy = float(parts[2]) * img_h
            w = float(parts[3]) * img_w
            h = float(parts[4]) * img_h
            self._boxes.append(_Box(
                class_id=cls_id,
                x1=cx - w / 2,
                y1=cy - h / 2,
                x2=cx + w / 2,
                y2=cy + h / 2,
            ))

    def paintEvent(self, event) -> None:
        super().paintEvent(event)
        if self._pixmap is None:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw image
        img_w = self._pixmap.width() * self._scale
        img_h = self._pixmap.height() * self._scale
        painter.drawPixmap(int(self._offset_x), int(self._offset_y),
                           int(img_w), int(img_h), self._pixmap)

        # Draw existing boxes
        for i, box in enumerate(self._boxes):
            is_selected = (i == self._selected_idx)
            color = QColor(CLASS_COLORS[box.class_id % len(CLASS_COLORS)])
            x1, y1 = self._img_to_canvas(box.x1, box.y1)
            x2, y2 = self._img_to_canvas(box.x2, box.y2)
            pen_width = 3 if is_selected else 2
            painter.setPen(QPen(color, pen_width))
            painter.drawRect(QRectF(x1, y1, x2 - x1, y2 - y1))

            label = f"{CLASS_NAMES[box.class_id]}"
            painter.setFont(QFont("Consolas", 10))
            text_rect = QRectF(x1, y1 - 18, x2 - x1, 18)
            painter.fillRect(text_rect, color)
            painter.setPen(QColor("#FFFFFF"))
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, label)

        # Draw current drawing box
        if self._drawing and self._draw_start and self._draw_end:
            x1, y1 = self._img_to_canvas(
                min(self._draw_start.x(), self._draw_end.x()),
                min(self._draw_start.y(), self._draw_end.y()),
            )
            x2, y2 = self._img_to_canvas(
                max(self._draw_start.x(), self._draw_end.x()),
                max(self._draw_start.y(), self._draw_end.y()),
            )
            color = QColor(CLASS_COLORS[self._current_class % len(CLASS_COLORS)])
            painter.setPen(QPen(color, 2, Qt.PenShape.DashLine))
            painter.drawRect(QRectF(x1, y1, x2 - x1, y2 - y1))

        painter.end()

    def save_labels(self, image_path: Path) -> None:
        if not self._pixmap or not self._boxes:
            return
        img_w = self._pixmap.width()
        img_h = self._pixmap.height()
        lines: list[str] = []
        for box in self._boxes:
            cx = (box.x1 + box.x2) / 2 / img_w
            cy = (box.y1 + box.y2) / 2 / img_h
            w = (box.x2 - box.x1) / img_w
            h = (box.y2 - box.y1) / img_h
            lines.append(f"{box.class_id} {cx:.6f} {cy:.6f} {w:.6f} {h:.6f}")
        label_path = image_path.with_suffix(".txt")
        label_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def remove_selected(self) -> None:
        if self._selected_idx is not None:
            self._boxes.pop(self._selected_idx)
            self._selected_idx = None
            self.update()

    def clear_all(self) -> None:
        self._boxes.clear()
        self._selected_idx = None
        self.update()

    @property
    def box_count(self) -> int:
        return len(self._boxes)


class _Box:
    """内部标注框数据。"""
    def __init__(self, class_id: int, x1: float, y1: float, x2: float, y2: float):
        self.class_id = class_id
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2


class LabelTool(QWidget):
    """截图标注工具主窗口。"""

    def __init__(self, input_dir: str | None = None, output_dir: str | None = None) -> None:
        super().__init__()
        self._input_dir: Path | None = Path(input_dir) if input_dir else None
        self._output_dir: Path | None = Path(output_dir) if output_dir else None
        self._image_files: list[Path] = []
        self._current_idx: int = -1
        self._current_image_path: Path | None = None

        self.setWindowTitle("终末地截图标注工具")
        self.setMinimumSize(1100, 700)
        self.setStyleSheet("background-color: #252526; color: #D1D1D1;")
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        left_panel = QWidget()
        left_panel.setMaximumWidth(250)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(6)

        open_btn = QPushButton("📂 打开截图文件夹")
        open_btn.setMinimumHeight(36)
        open_btn.setStyleSheet(self._btn_style())
        open_btn.clicked.connect(self._open_folder)
        left_layout.addWidget(open_btn)

        self._image_list = QListWidget()
        self._image_list.setStyleSheet("""
            QListWidget {
                background-color: #1E1E1E; border: 1px solid #464646;
                border-radius: 4px; padding: 4px;
            }
            QListWidget::item:selected { background-color: #2B6CB6; }
        """)
        self._image_list.currentRowChanged.connect(self._on_image_selected)
        left_layout.addWidget(self._image_list, stretch=1)

        left_layout.addWidget(QLabel("类别:"))
        self._class_combo = QComboBox()
        self._class_combo.addItems(CLASS_NAMES)
        self._class_combo.setStyleSheet(self._combo_style())
        self._class_combo.currentIndexChanged.connect(
            lambda i: self._canvas.set_current_class(i)
        )
        left_layout.addWidget(self._class_combo)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(4)
        delete_btn = QPushButton("删除选中")
        delete_btn.setMinimumHeight(32)
        delete_btn.setStyleSheet(self._btn_style())
        delete_btn.clicked.connect(lambda: self._canvas.remove_selected())
        btn_row.addWidget(delete_btn)

        clear_btn = QPushButton("全部清除")
        clear_btn.setMinimumHeight(32)
        clear_btn.setStyleSheet(self._btn_style())
        clear_btn.clicked.connect(lambda: self._canvas.clear_all())
        btn_row.addWidget(clear_btn)
        left_layout.addLayout(btn_row)

        nav_row = QHBoxLayout()
        nav_row.setSpacing(4)
        prev_btn = QPushButton("◀ 上一张")
        prev_btn.setMinimumHeight(32)
        prev_btn.setStyleSheet(self._btn_style())
        prev_btn.clicked.connect(self._prev_image)
        nav_row.addWidget(prev_btn)

        next_btn = QPushButton("下一张 ▶")
        next_btn.setMinimumHeight(32)
        next_btn.setStyleSheet(self._btn_style())
        next_btn.clicked.connect(self._next_image)
        nav_row.addWidget(next_btn)
        left_layout.addLayout(nav_row)

        self._save_btn = QPushButton("💾 保存标注")
        self._save_btn.setMinimumHeight(36)
        self._save_btn.setStyleSheet(self._btn_style(primary=True))
        self._save_btn.clicked.connect(self._save_labels)
        left_layout.addWidget(self._save_btn)

        self._export_btn = QPushButton("导出标注数据集")
        self._export_btn.setMinimumHeight(36)
        self._export_btn.setStyleSheet(self._btn_style())
        self._export_btn.clicked.connect(self._export_dataset)
        left_layout.addWidget(self._export_btn)

        self._status_label = QLabel("就绪")
        self._status_label.setStyleSheet("color: #888888; padding: 4px;")
        left_layout.addWidget(self._status_label)

        layout.addWidget(left_panel)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        self._canvas = Canvas()
        scroll.setWidget(self._canvas)
        layout.addWidget(scroll, stretch=1)

        self._load_input_dir()

    def _btn_style(self, primary: bool = False) -> str:
        if primary:
            return """
                QPushButton {
                    background-color: #2B6CB6; color: white;
                    border: none; border-radius: 6px; padding: 6px 12px;
                    font-weight: bold;
                }
                QPushButton:hover { background-color: #3182CE; }
                QPushButton:pressed { background-color: #1A4F8B; }
            """
        return """
            QPushButton {
                background-color: transparent; color: #D1D1D1;
                border: 1px solid #464646; border-radius: 6px; padding: 6px 12px;
            }
            QPushButton:hover { border-color: #2B6CB6; color: white; }
        """

    def _combo_style(self) -> str:
        return """
            QComboBox {
                background-color: #1E1E1E; color: #D1D1D1;
                border: 1px solid #464646; border-radius: 4px;
                padding: 4px 8px;
            }
            QComboBox::drop-down { border: none; }
            QComboBox QAbstractItemView {
                background-color: #1E1E1E; color: #D1D1D1;
                selection-background-color: #2B6CB6;
            }
        """

    def _open_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(
            self, "选择截图文件夹", "",
            QFileDialog.Option.ShowDirsOnly,
        )
        if not folder:
            return
        self._input_dir = Path(folder)
        self._load_input_dir()

    def _load_input_dir(self) -> None:
        if not self._input_dir:
            return
        extensions = (".png", ".jpg", ".jpeg", ".bmp", ".webp")
        self._image_files = sorted(
            p for p in self._input_dir.iterdir()
            if p.suffix.lower() in extensions
        )
        self._image_list.clear()
        for f in self._image_files:
            item = QListWidgetItem(f.name)
            self._image_list.addItem(item)

        if self._image_files:
            self._image_list.setCurrentRow(0)

        self._status_label.setText(f"📁 {len(self._image_files)} 张图片")

    def _on_image_selected(self, row: int) -> None:
        if row < 0 or row >= len(self._image_files):
            return
        self._current_idx = row
        self._current_image_path = self._image_files[row]
        self._canvas.load_image(self._current_image_path)
        self._update_status()

    def _prev_image(self) -> None:
        if self._current_idx > 0:
            self._save_labels()
            self._image_list.setCurrentRow(self._current_idx - 1)

    def _next_image(self) -> None:
        if self._current_idx < len(self._image_files) - 1:
            self._save_labels()
            self._image_list.setCurrentRow(self._current_idx + 1)

    def _save_labels(self) -> None:
        if self._current_image_path and self._canvas.box_count > 0:
            self._canvas.save_labels(self._current_image_path)
            self._update_status()

    def _update_status(self) -> None:
        total = len(self._image_files)
        idx = self._current_idx + 1
        boxes = self._canvas.box_count
        name = self._current_image_path.name if self._current_image_path else ""
        self._status_label.setText(
            f"[{idx}/{total}] {name} | {boxes} 个标注"
        )

    def _export_dataset(self) -> None:
        if not self._input_dir:
            QMessageBox.warning(self, "提示", "请先打开截图文件夹")
            return

        output = self._output_dir or (self._input_dir.parent / "yolo_dataset")
        train_img = output / "images" / "train"
        train_lbl = output / "labels" / "train"

        train_img.mkdir(parents=True, exist_ok=True)
        train_lbl.mkdir(parents=True, exist_ok=True)

        copied = 0
        for img_path in self._image_files:
            label_path = img_path.with_suffix(".txt")
            if not label_path.exists() or label_path.stat().st_size == 0:
                continue
            shutil.copy2(img_path, train_img / img_path.name)
            shutil.copy2(label_path, train_lbl / img_path.name)
            copied += 1

        dataset_yaml = output / "dataset.yaml"
        dataset_yaml.write_text(
            f"path: {output.as_posix()}\n"
            f"train: images/train\n"
            f"val: images/train\n"
            f"nc: {len(CLASS_NAMES)}\n"
            f"names: {CLASS_NAMES}\n",
            encoding="utf-8",
        )

        QMessageBox.information(
            self, "导出完成",
            f"标注数据集导出到:\n{output}\n\n"
            f"{copied} 张已标注图片\n\n"
            f"可用以下命令训练:\n"
            f"  python -m tools.ocr.train --data {output / 'dataset.yaml'}\n"
        )

    def keyPressEvent(self, event: QKeyEvent | None) -> None:
        if event is None:
            return
        key = event.key()
        if key == Qt.Key.Key_Left:
            self._prev_image()
        elif key == Qt.Key.Key_Right:
            self._next_image()
        elif key == Qt.Key.Key_S and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self._save_labels()
        elif key == Qt.Key.Key_Delete:
            self._canvas.remove_selected()
        super().keyPressEvent(event)


def main() -> None:
    args = _parse_args()

    if QApplication is None:
        print("[错误] 需要 PySide6: pip install PySide6")
        sys.exit(1)

    app = QApplication(sys.argv)

    if not args.input:
        root = type("_", (), {"destroy": lambda: None})()
        folder = QFileDialog.getExistingDirectory(
            type("_", (), {"winId": lambda: 0})(),
            "选择截图文件夹",
            "",
            QFileDialog.Option.ShowDirsOnly,
        )
        if not folder:
            print("未选择文件夹")
            return
        args.input = folder

    tool = LabelTool(input_dir=args.input, output_dir=args.output)
    tool.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
