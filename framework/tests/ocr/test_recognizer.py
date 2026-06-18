# SPDX-License-Identifier: AGPL-3.0
"""tools.ocr.recognizer 数据类单元测试（不启动 EasyOCR）。"""

from __future__ import annotations

import json

from tools.ocr.recognizer import GAME_TERMS, OCRResult, OCRText


class TestOCRText:
    def test_defaults(self) -> None:
        t = OCRText(text="攻击力", confidence=0.95)

        assert t.text == "攻击力"

        assert t.confidence == 0.95

        assert not t.corrected

    def test_corrected_flag(self) -> None:
        t = OCRText(text="暴击率", confidence=0.90, corrected=True)

        assert t.corrected

    def test_as_float_percent(self) -> None:
        t = OCRText(text="15.5%", confidence=0.95)

        val = t.as_float()

        assert val is not None

        assert abs(val - 15.5) < 0.001

    def test_as_float_integer(self) -> None:
        t = OCRText(text="80", confidence=0.99)

        val = t.as_float()

        assert val == 80.0

    def test_as_float_non_numeric(self) -> None:
        t = OCRText(text="暴击率", confidence=0.95)

        assert t.as_float() is None

    def test_to_dict(self) -> None:
        t = OCRText(text="基础攻击", confidence=0.88, corrected=True)

        d = t.to_dict()

        assert d["text"] == "基础攻击"

        assert d["confidence"] == 0.88

        assert d["corrected"] is True

    def test_json_serializable(self) -> None:
        t = OCRText(text="攻击力+", confidence=0.92)

        dumped = json.dumps(t.to_dict())

        loaded = json.loads(dumped)

        assert loaded["text"] == "攻击力+"

        assert loaded["confidence"] == 0.92


class TestOCRResult:
    def test_empty(self) -> None:
        r = OCRResult(image_path="/tmp/test.png")

        assert r.raw_texts == []

        assert r.number_values == []

        assert r.inference_ms == 0.0

    def test_with_texts(self) -> None:
        r = OCRResult(
            image_path="/tmp/test.png",
            texts=[
                OCRText(text="80", confidence=0.99),
                OCRText(text="暴击率", confidence=0.95),
            ],
            inference_ms=150.0,
        )

        assert len(r.raw_texts) == 2

        assert "80" in r.raw_texts

        assert "暴击率" in r.raw_texts

        assert len(r.number_values) == 1

        assert r.number_values[0] == 80.0

    def test_to_dict(self) -> None:
        r = OCRResult(
            image_path="/tmp/x.png",
            texts=[OCRText(text="秋栗", confidence=0.93)],
            inference_ms=120.5,
        )

        d = r.to_dict()

        assert d["num_texts"] == 1

        assert d["inference_ms"] == 120.5

        assert d["texts"][0]["text"] == "秋栗"

    def test_json_roundtrip(self) -> None:
        r = OCRResult(
            image_path="/tmp/y.png",
            texts=[
                OCRText(text="角色名", confidence=0.9),
                OCRText(text="等级", confidence=0.8),
            ],
            inference_ms=200.0,
        )

        dumped = json.dumps(r.to_dict(), ensure_ascii=False)

        loaded = json.loads(dumped)

        assert loaded["num_texts"] == 2

        assert loaded["inference_ms"] == 200.0


class TestGameTerms:
    def test_has_essential_terms(self) -> None:
        assert "基础攻击" in GAME_TERMS

        assert "暴击率" in GAME_TERMS

        assert "攻击力" in GAME_TERMS

        assert "防御力" in GAME_TERMS

    def test_has_typo_corrections(self) -> None:
        assert GAME_TERMS["攻去力"] == "攻击力"

        assert GAME_TERMS["防卸力"] == "防御力"

        assert GAME_TERMS["暴击车"] == "暴击率"
