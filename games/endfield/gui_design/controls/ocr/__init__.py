#!/usr/bin/env python3
"""截图识装检测对话框 — 选择截图文件夹 → YOLO 检测 + OCR 识别 → 显示结果。"""

from __future__ import annotations

import json
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from calc_framework.logging import get_logger

_logger = get_logger("gui.ocr")


def open_ocr_detection_dialog(parent: QWidget | None = None) -> None:
    """打开截图识装对话框：选择文件夹 → 检测 → 显示结果。"""
    folder = QFileDialog.getExistingDirectory(
        parent,
        "选择截图文件夹",
        "",
        QFileDialog.Option.ShowDirsOnly,
    )
    if not folder:
        return

    folder_path = Path(folder)
    if not folder_path.is_dir():
        return

    dialog = _DetectionDialog(folder_path, parent)
    dialog.exec()


class _DetectionDialog(QDialog):
    """检测结果显示弹窗。"""

    def __init__(self, folder: Path, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._folder = folder
        self._result_json: str = ""

        self.setWindowTitle("截图识装检测结果")
        self.setMinimumSize(700, 500)
        self.setStyleSheet("background-color: #1E1E1E; color: #D1D1D1;")
        _build_ui(self)

        # 开始检测（异步）
        self._run_detection()

    def _run_detection(self) -> None:
        """后台运行 YOLO + OCR 检测。"""
        try:
            from tools.ocr.detector import YOLODetector
            from tools.ocr.recognizer import OCRRecognizer

            # 使用默认 YOLOv8n 模型
            detector = YOLODetector("yolov8n.pt", conf_threshold=0.25)
            ocr = OCRRecognizer()

            batch = detector.detect_folder(
                str(self._folder),
                save_json=False,
                save_annotated=False,
            )

            lines: list[str] = []
            lines.append(f"截图文件夹: {self._folder}")
            lines.append(f"总图片数: {batch.total_images}")
            lines.append(f"总检测目标: {batch.total_detections}")
            lines.append(f"平均推理: {batch.summary()['avg_inference_ms']} ms/张")
            lines.append("")

            for r in batch.results[:20]:
                lines.append(f"── {Path(r.image_path).name} ──")
                if r.detections:
                    for d in r.detections[:10]:
                        lines.append(f"  [{d.confidence:.2f}] {d.class_name} ({d.x1:.0f},{d.y1:.0f},{d.x2:.0f},{d.y2:.0f})")
                # OCR the full image
                try:
                    ocr_result = ocr.recognize(r.image_path)
                    if ocr_result.texts:
                        lines.append(f"  OCR:")
                        for t in ocr_result.texts[:15]:
                            lines.append(f"    [{t.confidence:.2f}] {t.text}")
                except Exception as e:
                    lines.append(f"  OCR 失败: {e}")
                lines.append("")

            if len(batch.results) > 20:
                lines.append(f"... 还有 {len(batch.results) - 20} 张未显示")

            self._result_json = json.dumps(batch.summary(), ensure_ascii=False, indent=2)
            self._result_text.setPlainText("\n".join(lines))
            self._result_text.setStyleSheet("color: #D1D1D1;")

        except ImportError as e:
            self._result_text.setPlainText(f"[错误] 导入失败: {e}\n请运行: pip install ultralytics easyocr")
        except Exception as e:
            self._result_text.setPlainText(f"[错误] 检测失败: {e}")
            _logger.exception("截图识装检测异常")


def _build_ui(dialog: _DetectionDialog) -> None:
    """构建对话框 UI。"""
    layout = QVBoxLayout(dialog)
    layout.setContentsMargins(16, 16, 16, 16)
    layout.setSpacing(8)

    title = QLabel("🔍 截图识装 — YOLO 检测 + OCR 识别")
    title_font = QFont()
    title_font.setPointSize(14)
    title.setFont(title_font)
    title.setStyleSheet("color: #FFFFFF;")
    layout.addWidget(title)

    dialog._result_text = QPlainTextEdit()
    dialog._result_text.setReadOnly(True)
    dialog._result_text.setFont(QFont("Consolas", 10))
    dialog._result_text.setStyleSheet("""
        QPlainTextEdit {
            background-color: #2B2B2B; color: #D1D1D1;
            border: 1px solid #464646; border-radius: 6px;
            padding: 8px;
        }
    """)
    layout.addWidget(dialog._result_text, stretch=1)

    btn_layout = QHBoxLayout()
    btn_layout.setSpacing(8)

    close_btn = QPushButton("关闭")
    close_btn.setMinimumHeight(32)
    close_btn.setStyleSheet("""
        QPushButton {
            background-color: transparent; color: #D1D1D1;
            border: 1px solid #464646; border-radius: 6px; padding: 6px 16px;
        }
        QPushButton:hover { border-color: #2B6CB6; color: white; }
    """)
    close_btn.clicked.connect(dialog.accept)
    btn_layout.addStretch()
    btn_layout.addWidget(close_btn)

    layout.addLayout(btn_layout)
