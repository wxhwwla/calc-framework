#!/usr/bin/env python3

# SPDX-License-Identifier: AGPL-3.0
"""

OCR 文本识别器 — EasyOCR 引擎封装 + 终末地专有名词字典。



支持：

- 整图 OCR

- 区域 OCR（对 bounding box crop 后识别）

- 数字专用识别

- 专有名词纠错字典

"""

from __future__ import annotations


import re

import time

from dataclasses import dataclass, field

from pathlib import Path

from typing import Any


from PIL import Image


try:
    import easyocr

except ImportError:
    easyocr = None  # type: ignore[assignment, misc]


# ── 终末地专有名词字典 ──────────────────────────


GAME_TERMS: dict[str, str] = {
    "基础攻击": "基础攻击",
    "暴击率": "暴击率",
    "暴击伤害": "暴击伤害",
    "攻击力": "攻击力",
    "防御力": "防御力",
    "生命值": "生命值",
    "力量": "力量",
    "敏捷": "敏捷",
    "智识": "智识",
    "意志": "意志",
    "伤害加成": "伤害加成",
    "伤害减免": "伤害减免",
    "增幅": "增幅",
    "虚弱": "虚弱",
    "庇护": "庇护",
    "脆弱": "脆弱",
    "易伤": "易伤",
    "失衡易伤": "失衡易伤",
    "抗性": "抗性",
    "连击增伤": "连击增伤",
    "特殊乘区": "特殊乘区",
    "暴击车": "暴击率",
    "暴击伤客": "暴击伤害",
    "攻去力": "攻击力",
    "防卸力": "防御力",
    "连击培伤": "连击增伤",
}


_NUMBER_RE = re.compile(r"^-?\d+(\.\d+)?$")

_PERCENT_RE = re.compile(r"^(-?\d+(\.\d+)?)\s*%?$")


@dataclass
class OCRText:
    """单个 OCR 识别结果。"""

    text: str

    confidence: float

    corrected: bool = False

    def as_float(self) -> float | None:
        """as_float 实现。"""
        m = _PERCENT_RE.match(self.text.strip())

        if m:
            return float(m.group(1))

        try:
            return float(self.text.strip())

        except ValueError:
            return None

    def to_dict(self) -> dict[str, Any]:
        """to_dict 实现。"""
        return {
            "text": self.text,
            "confidence": round(self.confidence, 4),
            "corrected": self.corrected,
        }


@dataclass
class OCRResult:
    """单张图片的 OCR 结果。"""

    image_path: str

    texts: list[OCRText] = field(default_factory=list)

    inference_ms: float = 0.0

    @property
    def raw_texts(self) -> list[str]:
        """raw_texts 实现。"""
        return [t.text for t in self.texts]

    @property
    def number_values(self) -> list[float]:
        """number_values 实现。"""
        vals: list[float] = []

        for t in self.texts:
            v = t.as_float()

            if v is not None:
                vals.append(v)

        return vals

    def to_dict(self) -> dict[str, Any]:
        """to_dict 实现。"""
        return {
            "image_path": self.image_path,
            "num_texts": len(self.texts),
            "inference_ms": round(self.inference_ms, 1),
            "texts": [t.to_dict() for t in self.texts],
        }


class OCRRecognizer:
    """EasyOCR 封装。



    用法:

        ocr = OCRRecognizer()

        result = ocr.recognize("screenshot.png")

        print(result.raw_texts)



        texts = ocr.recognize_region("screenshot.png", (x1, y1, x2, y2))

    """

    def __init__(
        self,
        lang_list: list[str] | None = None,
        gpu: bool = False,
        term_dict: dict[str, str] | None = None,
    ) -> None:
        if easyocr is None:
            raise ImportError("需要安装 EasyOCR: pip install easyocr")

        self._lang = lang_list or ["ch_sim", "en"]

        self._reader = easyocr.Reader(self._lang, gpu=gpu)

        self._term_dict = {**GAME_TERMS, **(term_dict or {})}

    def recognize(self, image_path: str | Path) -> OCRResult:
        """识别整张图片的文本。"""

        path = Path(image_path)

        if not path.exists():
            raise FileNotFoundError(f"图片不存在: {image_path}")

        t0 = time.perf_counter()

        raw = self._reader.readtext(str(path))

        elapsed_ms = (time.perf_counter() - t0) * 1000

        texts = self._parse_raw(raw)

        return OCRResult(
            image_path=str(path),
            texts=texts,
            inference_ms=elapsed_ms,
        )

    def recognize_region(
        self,
        image_path: str | Path,
        bbox: tuple[float, float, float, float],
    ) -> list[OCRText]:
        """识别图片指定区域 (x1, y1, x2, y2) 的文本。"""

        img = Image.open(image_path)

        x1, y1, x2, y2 = bbox

        roi = img.crop((x1, y1, x2, y2))

        temp_path = Path(image_path).parent / f"__ocr_crop_{id(roi)}.png"

        try:
            roi.save(temp_path)

            return self.recognize(temp_path).texts

        finally:
            if temp_path.exists():
                temp_path.unlink()

    def recognize_crops(
        self,
        image_path: str | Path,
        boxes: list[tuple[float, float, float, float]],
    ) -> list[list[OCRText]]:
        """recognize_crops 实现。

        Args:
            image_path: 参数描述。
            boxes: 参数描述。

        Returns:
            返回值描述。
        """
        return [self.recognize_region(image_path, b) for b in boxes]

    def extract_numbers(self, image_path: str | Path) -> list[float]:
        """extract_numbers 实现。

        Args:
            image_path: 参数描述。

        Returns:
            返回值描述。
        """
        result = self.recognize(image_path)

        return result.number_values

    def _parse_raw(self, raw: list) -> list[OCRText]:
        """_parse_raw 实现。"""
        texts: list[OCRText] = []

        for bbox, text, confidence in raw:
            if confidence < 0.3:
                continue

            corrected = self._apply_term_dict(text)

            texts.append(
                OCRText(
                    text=corrected,
                    confidence=confidence,
                    corrected=(corrected != text),
                )
            )

        return texts

    def _apply_term_dict(self, text: str) -> str:
        """_apply_term_dict 实现。"""
        if text in self._term_dict:
            return self._term_dict[text]

        return text
