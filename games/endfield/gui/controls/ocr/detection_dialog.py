#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""截图识装检测对话框 — 选择截图文件夹 → TorchVision 检测 + OCR 识别 → 映射 → 填入计算器。"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from calc_framework.ui.i18n import tr
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
from games.endfield.gui.controls.ocr.ocr_pipeline import (
    format_detail_lines,
    preset_summary,
    run_pipeline,
)

_logger = get_logger("gui.ocr")


def run_ocr_detection(folder: str | Path) -> dict[str, Any] | None:
    """对截图文件夹执行目标检测 + OCR 识别 + 映射。

    Args:
        folder: 截图文件夹路径

    Returns:
        preset_dict 或 None（识别失败）
    """
    result = run_pipeline(folder)
    return result.mapped_preset


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
    """从 preset_dict 生成可读摘要（委托 ocr_pipeline）。"""
    return preset_summary(preset)


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

        self.setWindowTitle(tr("desktop.endfield.ocrResultTitle"))
        self.setMinimumSize(750, 550)
        self.setStyleSheet("background-color: #1E1E1E; color: #D1D1D1;")
        _build_ui(self)

        # 开始检测
        self._run_detection()
        """初始化实例。"""

    def _run_detection(self) -> None:
        """后台运行目标检测 + OCR + 映射（委托 ocr_pipeline）。"""
        pipeline_result = run_pipeline(self._folder)
        lines = format_detail_lines(pipeline_result, self._folder)

        if pipeline_result.error:
            if "ImportError" in pipeline_result.error or "导入失败" in pipeline_result.error:
                lines.append("或点击对话框中的「下载 OCR 模型」按钮")

        self._mapped_preset = pipeline_result.mapped_preset
        if self._mapped_preset:
            self._apply_btn.setEnabled(True)

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
        self._download_btn.setText(tr("desktop.endfield.ocrDownloading"))
        self._download_progress.setVisible(True)
        self._download_progress.setValue(0)
        msg = tr("desktop.endfield.ocrDownloadingMsg")
        self._result_text.setPlainText(msg)
        self._thread = _DownloadThread()
        self._thread.finished.connect(self._on_download_finished)
        self._thread.progress.connect(self._download_progress.setValue)
        self._thread.start()

    def _on_download_finished(self, success: bool) -> None:
        self._download_btn.setEnabled(True)
        self._download_btn.setText(tr("desktop.endfield.ocrDownloadModel"))
        self._download_progress.setVisible(False)
        if success:
            QMessageBox.information(
                self,
                tr("desktop.endfield.ocrDownloadComplete"),
                tr("desktop.endfield.ocrDownloadCompleteMsg"),
            )
            self._run_detection()
        else:
            QMessageBox.critical(
                self,
                tr("desktop.endfield.ocrDownloadFailed"),
                tr("desktop.endfield.ocrDownloadFailedMsg"),
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
                pth_path = cache / model["filename"]  # type: ignore[operator]
                if pth_path.exists():
                    completed += 1
                    self.progress.emit(int(completed / total_models * 100))
                    continue

                zip_path = cache / f"{model['filename']}.zip"
                zip_url = model["zip_url"]
                try:
                    req = Request(zip_url, headers={"User-Agent": "Mozilla/5.0"})  # type: ignore[arg-type]
                    resp = urlopen(req, timeout=120)
                    with open(zip_path, "wb") as f:
                        f.write(resp.read())
                    with zipfile.ZipFile(zip_path, "r") as zf:
                        # Zip Slip 防护：验证所有条目路径在目标目录内
                        for info in zf.infolist():
                            target_path = (cache / info.filename).resolve()
                            if not str(target_path).startswith(str(cache.resolve())):
                                raise RuntimeError(f"Zip Slip 检测: {info.filename}")
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

    title = QLabel(tr("desktop.endfield.ocrMainTitle"))
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

    dialog._download_btn = QPushButton(tr("desktop.endfield.ocrDownloadModel"))
    dialog._download_btn.setMinimumHeight(36)
    dialog._download_btn.setStyleSheet("""
        QPushButton { background-color: transparent; color: #D1D1D1;
                      border: 1px solid #464646; border-radius: 6px; padding: 8px 14px; }
        QPushButton:hover { border-color: #48BB78; color: #48BB78; }
    """)
    dialog._download_btn.clicked.connect(dialog._on_download_model)
    btn_layout.addWidget(dialog._download_btn)

    dialog._apply_btn = QPushButton(tr("desktop.endfield.ocrFillCalculator"))
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

    close_btn = QPushButton(tr("common.close"))
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
