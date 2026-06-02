#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""单张截图 OCR — 供 Web `/api/ocr/detect` 调用。"""

from __future__ import annotations

from typing import Any


def ocr_detect_from_file(image_path: str) -> dict[str, Any]:
    """识别单张截图中的角色/武器名（与桌面 mapper 一致）。"""
    from tools.ocr.mapper import OcrMapper
    from tools.ocr.recognizer import OCRRecognizer

    ocr = OCRRecognizer()
    mapper = OcrMapper()
    ocr_result = ocr.recognize(image_path)
    texts = [(t.text, t.confidence, None) for t in ocr_result.texts]
    if not texts:
        return {"char_name": None, "weapon_name": None, "texts": [], "message": "未识别到文字"}

    mapped = mapper.map_texts(texts)
    out: dict[str, Any] = {
        "char_name": mapped.char_name or None,
        "weapon_name": mapped.weapon_name or None,
        "char_level": mapped.char_level or None,
        "weapon_level": mapped.weapon_level or None,
        "trust_level": mapped.trust_level or None,
        "texts": [t[0] for t in texts[:30]],
    }
    if mapped.is_valid:
        out["preset"] = mapped.to_loadout_preset_dict()
    return out
