# SPDX-License-Identifier: AGPL-3.0
"""ocr 包 — OCR 识别工具集，支持文本检测、识别与游戏术语映射。"""

from __future__ import annotations

from .detector import BBox, BatchResult, DetectionResult, YOLOXDetector
from .mapper import OcrMapper, OcrMatchResult
from .recognizer import OCRRecognizer, OCRResult, OCRText, GAME_TERMS

__all__ = [
    "BBox",
    "BatchResult",
    "DetectionResult",
    "YOLOXDetector",
    "OcrMapper",
    "OcrMatchResult",
    "OCRRecognizer",
    "OCRResult",
    "OCRText",
    "GAME_TERMS",
]
