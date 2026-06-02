#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""OCR 截图识装 — 公共 API。"""

from __future__ import annotations

from .detection_dialog import open_ocr_detection_dialog, run_ocr_detection

__all__ = [
    "open_ocr_detection_dialog",
    "run_ocr_detection",
]
