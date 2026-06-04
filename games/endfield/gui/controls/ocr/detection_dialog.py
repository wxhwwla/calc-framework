#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""截图识装检测对话框 — 选择截图文件夹 → TorchVision 检测 + OCR 识别 → 映射 → 填入计算器。"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from PySide6.QtCore import QThread, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from games.endfield.framework_bridge import get_logger

_logger = get_logger("gui.ocr")


def run_ocr_detection(folder: str | Path) -> dict[str, Any] | None:
    """对截图文件夹执行目标检测 + OCR 识别 + 映射。

    Args:
        folder: 截图文件夹路径

    Returns:
        preset_dict 或 None（识别失败）
    """
    try:
        from tools.ocr.detector import YOLOXDetector
        from tools.ocr.mapper import OcrMapper
        from tools.ocr.recognizer import OCRRecognizer

        detector = YOLOXDetector(conf_threshold=0.25)
        ocr = OCRRecognizer()
        mapper = OcrMapper()

        batch = detector.detect_folder(
            str(folder),
            save_json=False,
            save_annotated=False,
        )

        all_ocr_texts: list[tuple[str, float, str | None]] = []
        mapped_preset = None

        for r in batch.results:
            for d in r.detections:
                pass
            try:
                ocr_result = ocr.recognize(r.image_path)
                for t in ocr_result.texts:
                    all_ocr_texts.append((t.text, t.confidence, None))
                if mapped_preset is None:
                    mapped = mapper.map_texts([(t.text, t.confidence, None) for t in ocr_result.texts])
                    if mapped.is_valid:
                        mapped_preset = mapped.to_loadout_preset_dict()
            except Exception:
                _logger.debug("单张截图 OCR 识别失败（已跳过）: %s", r.image_path)
                continue

        if mapped_preset is None and all_ocr_texts:
            mapped = mapper.map_texts(all_ocr_texts)
            if mapped.is_valid:
                mapped_preset = mapped.to_loadout_preset_dict()

        return mapped_preset

    except ImportError:
        return None
    except Exception:
        _logger.exception("OCR 检测异常")
        return None


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


def _summary_from_preset(preset: dict[str, Any]) -> str:
    """从 preset_dict 生成可读摘要。"""
    parts = []
    if preset.get("char_name"):
        parts.append(f"角色={preset['char_name']}")
    if preset.get("weapon_name"):
        parts.append(f"武器={preset['weapon_name']}")
    if preset.get("char_level"):
        parts.append(f"等级={preset['char_level']}")
    if preset.get("weapon_level"):
        parts.append(f"武器等级={preset['weapon_level']}")
    return "  ".join(parts) if parts else "空"


class _DetectionDialog(QDialog):
    """检测结果显示弹窗。"""

    _download_btn: QPushButton

    def __init__(
        self,
        folder: Path,
        parent: QWidget | None = None,
        *,
        on_apply: Callable[[dict[str, Any]], None] | None = None,
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
        """初始化实例。"""

    def _run_detection(self) -> None:
        """后台运行目标检测 + OCR + 映射。"""
        lines: list[str] = []
        lines.append(f"截图文件夹: {self._folder}")
        try:
            from tools.ocr.detector import YOLOXDetector

            detector = YOLOXDetector(conf_threshold=0.25)
            batch = detector.detect_folder(
                str(self._folder),
                save_json=False,
                save_annotated=False,
            )
            lines.append(f"总图片数: {batch.total_images}")
            lines.append(f"总检测目标: {batch.total_detections}")
            lines.append(f"平均推理: {batch.summary()['avg_inference_ms']} ms/张")
            lines.append("")

            for r in batch.results[:20]:
                lines.append(f"── {Path(r.image_path).name} ──")
                if r.detections:
                    for d in r.detections[:10]:
                        coord = f"({d.x1:.0f},{d.y1:.0f},{d.x2:.0f},{d.y2:.0f})"
                        lines.append(f"  [{d.confidence:.2f}] {d.class_name} {coord}")
                try:
                    from tools.ocr.recognizer import OCRRecognizer

                    ocr = OCRRecognizer()
                    ocr_result = ocr.recognize(r.image_path)
                    if ocr_result.texts:
                        lines.append("  OCR:")
                        for t in ocr_result.texts[:15]:
                            lines.append(f"    [{t.confidence:.2f}] {t.text}")
                except Exception as e:
                    lines.append(f"  OCR 失败: {e}")
                lines.append("")

            if len(batch.results) > 20:
                lines.append(f"... 还有 {len(batch.results) - 20} 张未显示")

            self._mapped_preset = run_ocr_detection(self._folder)
            if self._mapped_preset:
                lines.append(f"→ 识别: {_summary_from_preset(self._mapped_preset)}")
                self._apply_btn.setEnabled(True)
            else:
                lines.append("\n→ 未能识别出角色和武器名称")

        except ImportError as e:
            lines.append(f"[错误] 导入失败: {e}\n请运行: pip install torchvision easyocr")
            lines.append("或点击对话框中的「下载 OCR 模型」按钮")
        except Exception as e:
            lines.append(f"[错误] 检测失败: {e}")
            _logger.exception("截图识装检测异常")

        self._result_text.setPlainText("\n".join(lines))
        self._result_text.setStyleSheet("color: #D1D1D1;")

    def _handle_apply(self) -> None:
        """点击「填入计算器」按钮。"""
        if self._mapped_preset and self._on_apply:
            cb = self._on_apply
            assert cb is not None
            cb(self._mapped_preset)
            self.accept()

    def _on_download_model(self) -> None:
        """在后台线程下载 OCR 模型。"""
        self._download_btn.setEnabled(False)
        self._download_btn.setText("下载中...")
        self._download_progress.setVisible(True)
        self._download_progress.setValue(0)
        msg = "正在下载 EasyOCR 模型...\n\n这可能需要几分钟，请耐心等待。\n模型将下载到用户目录的 .EasyOCR/model/ 下。"
        self._result_text.setPlainText(msg)
        self._thread = _DownloadThread()
        self._thread.finished.connect(self._on_download_finished)
        self._thread.progress.connect(self._download_progress.setValue)
        self._thread.start()

    def _on_download_finished(self, success: bool) -> None:
        self._download_btn.setEnabled(True)
        self._download_btn.setText("下载 OCR 模型")
        self._download_progress.setVisible(False)
        if success:
            QMessageBox.information(self, "下载完成", "EasyOCR 模型已下载完成！\n现在可以正常使用截图识装功能。")
            self._run_detection()
        else:
            QMessageBox.critical(
                self, "下载失败", "模型下载失败。\n\n请尝试在终端手动运行:\n  python tools/ocr/download_models.py"
            )
        """on download finished。"""


class _DownloadThread(QThread):
    """后台下载 OCR 模型。"""

    finished = Signal(bool)
    progress = Signal(int)

    def run(self) -> None:
        try:
            import zipfile
            from pathlib import Path
            from urllib.request import Request, urlopen

            from tools.ocr.download_models import REQUIRED_MODELS

            cache = Path.home() / ".EasyOCR" / "model"
            cache.mkdir(parents=True, exist_ok=True)

            total_models = len(REQUIRED_MODELS)
            completed = 0
            for model in REQUIRED_MODELS:
                pth_path = cache / model["filename"]
                if pth_path.exists():
                    completed += 1
                    self.progress.emit(int(completed / total_models * 100))
                    continue

                zip_path = cache / f"{model['filename']}.zip"
                zip_url = model["zip_url"]
                try:
                    req = Request(zip_url, headers={"User-Agent": "Mozilla/5.0"})
                    resp = urlopen(req, timeout=120)
                    with open(zip_path, "wb") as f:
                        f.write(resp.read())
                    with zipfile.ZipFile(zip_path, "r") as zf:
                        zf.extractall(cache)
                    zip_path.unlink()
                except Exception:
                    _logger.warning("OCR 模型下载/解压失败", exc_info=True)
                    self.finished.emit(False)
                    return
                completed += 1
                self.progress.emit(int(completed / total_models * 100))

            self.finished.emit(True)
        except Exception:
            _logger.exception("OCR 模型下载线程异常")
            self.finished.emit(False)
        """执行主流程。"""


def _build_ui(dialog: _DetectionDialog) -> None:
    """构建对话框 UI。"""
    layout = QVBoxLayout(dialog)
    layout.setContentsMargins(16, 16, 16, 16)
    layout.setSpacing(8)

    title = QLabel("截图识装 — 目标检测 + OCR 识别")
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

    dialog._download_progress = QProgressBar()
    dialog._download_progress.setVisible(False)
    dialog._download_progress.setStyleSheet("""
        QProgressBar { background-color: #2B2B2B; border: 1px solid #464646;
                       border-radius: 4px; text-align: center; color: #D1D1D1; }
        QProgressBar::chunk { background-color: #2B6CB6; border-radius: 4px; }
    """)
    layout.addWidget(dialog._download_progress)

    btn_layout = QHBoxLayout()
    btn_layout.setSpacing(8)

    dialog._download_btn = QPushButton("下载 OCR 模型")
    dialog._download_btn.setMinimumHeight(36)
    dialog._download_btn.setStyleSheet("""
        QPushButton { background-color: transparent; color: #D1D1D1;
                      border: 1px solid #464646; border-radius: 6px; padding: 8px 14px; }
        QPushButton:hover { border-color: #48BB78; color: #48BB78; }
    """)
    dialog._download_btn.clicked.connect(dialog._on_download_model)
    btn_layout.addWidget(dialog._download_btn)

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
    dialog._apply_btn.clicked.connect(dialog._handle_apply)
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
