#!/usr/bin/env python3
"""截图识装检测对话框 — 选择截图文件夹 → YOLO 检测 + OCR 识别 → 映射 → 填入计算器。"""

from __future__ import annotations

from pathlib import Path
from typing import Any

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


def open_ocr_detection_dialog(
    parent: QWidget | None = None,
    *,
    on_apply: Any = None,
) -> None:
    """打开截图识装对话框：选择文件夹 → 检测 → 显示结果。

    Args:
        parent: 父窗口
        on_apply: 回调 (char_name, weapon_name, char_level, weapon_level, trust_level) → None
    """
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

    dialog = _DetectionDialog(folder_path, parent, on_apply=on_apply)
    dialog.exec()


class _DetectionDialog(QDialog):
    """检测结果显示弹窗。"""

    def __init__(
        self,
        folder: Path,
        parent: QWidget | None = None,
        *,
        on_apply: Any = None,
    ) -> None:
        super().__init__(parent)
        self._folder = folder
        self._on_apply = on_apply
        self._mapped_preset: dict[str, Any] | None = None

        self.setWindowTitle("截图识装检测结果")
        self.setMinimumSize(750, 550)
        self.setStyleSheet("background-color: #1E1E1E; color: #D1D1D1;")
        _build_ui(self)

        # 开始检测
        self._run_detection()

    def _run_detection(self) -> None:
        """后台运行 YOLO + OCR + 映射。"""
        try:
            from tools.ocr.detector import YOLODetector
            from tools.ocr.mapper import OcrMapper
            from tools.ocr.recognizer import OCRRecognizer

            detector = YOLODetector("yolov8n.pt", conf_threshold=0.25)
            ocr = OCRRecognizer()
            mapper = OcrMapper()

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

            all_ocr_texts: list[tuple[str, float, str | None]] = []
            mapped_preset = None

            for r in batch.results[:20]:
                lines.append(f"── {Path(r.image_path).name} ──")
                if r.detections:
                    for d in r.detections[:10]:
                        lines.append(f"  [{d.confidence:.2f}] {d.class_name} ({d.x1:.0f},{d.y1:.0f},{d.x2:.0f},{d.y2:.0f})")

                try:
                    ocr_result = ocr.recognize(r.image_path)
                    if ocr_result.texts:
                        lines.append(f"  OCR:")
                        for t in ocr_result.texts[:15]:
                            lines.append(f"    [{t.confidence:.2f}] {t.text}")

                        # Collect for mapping
                        for t in ocr_result.texts:
                            all_ocr_texts.append((t.text, t.confidence, None))

                        # Map the first image's results
                        if mapped_preset is None:
                            mapped = mapper.map_texts([(t.text, t.confidence, None) for t in ocr_result.texts])
                            if mapped.is_valid:
                                mapped_preset = mapped.to_loadout_preset_dict()
                                lines.append(f"  → 识别: {mapped.summary()}")
                except Exception as e:
                    lines.append(f"  OCR 失败: {e}")
                lines.append("")

            if len(batch.results) > 20:
                lines.append(f"... 还有 {len(batch.results) - 20} 张未显示")

            # Try mapping from all texts if first image didn't yield results
            if mapped_preset is None and all_ocr_texts:
                mapped = mapper.map_texts(all_ocr_texts)
                if mapped.is_valid:
                    mapped_preset = mapped.to_loadout_preset_dict()
                    lines.append(f"\n→ 综合识别: {mapped.summary()}")
                else:
                    lines.append(f"\n→ 未能识别出角色和武器名称")

            self._mapped_preset = mapped_preset
            if mapped_preset:
                self._apply_btn.setEnabled(True)

            self._result_text.setPlainText("\n".join(lines))
            self._result_text.setStyleSheet("color: #D1D1D1;")

        except ImportError as e:
            self._result_text.setPlainText(f"[错误] 导入失败: {e}\n请运行: pip install ultralytics easyocr")
        except Exception as e:
            self._result_text.setPlainText(f"[错误] 检测失败: {e}")
            _logger.exception("截图识装检测异常")

    def _on_apply(self) -> None:
        """点击「填入计算器」按钮。"""
        if self._mapped_preset and self._on_apply:
            self._on_apply(self._mapped_preset)
            self.accept()


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

    dialog._apply_btn = QPushButton("📥 填入计算器")
    dialog._apply_btn.setMinimumHeight(36)
    dialog._apply_btn.setEnabled(False)
    dialog._apply_btn.setStyleSheet("""
        QPushButton {
            background-color: #2B6CB6; color: white; font-weight: bold;
            border: none; border-radius: 6px; padding: 8px 20px;
        }
        QPushButton:hover { background-color: #3182CE; }
        QPushButton:disabled { background-color: #444; color: #888; }
    """)
    dialog._apply_btn.clicked.connect(dialog._on_apply)
    btn_layout.addWidget(dialog._apply_btn)

    close_btn = QPushButton("关闭")
    close_btn.setMinimumHeight(36)
    close_btn.setStyleSheet("""
        QPushButton {
            background-color: transparent; color: #D1D1D1;
            border: 1px solid #464646; border-radius: 6px; padding: 8px 20px;
        }
        QPushButton:hover { border-color: #2B6CB6; color: white; }
    """)
    close_btn.clicked.connect(dialog.accept)
    btn_layout.addWidget(close_btn)

    layout.addLayout(btn_layout)
