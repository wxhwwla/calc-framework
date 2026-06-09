# SPDX-License-Identifier: AGPL-3.0
"""tools.ocr.detector 单元测试。"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from tools.ocr.detector import BatchResult, BBox, DetectionResult, TorchVisionDetector

# ── 数据类测试 ────────────────────────────────────


class TestBBox:
    def test_to_dict(self) -> None:
        b = BBox(class_id=0, class_name="test", confidence=0.95, x1=10, y1=20, x2=100, y2=200)

        d = b.to_dict()

        assert d["class_id"] == 0

        assert d["class_name"] == "test"

        assert d["confidence"] == 0.95

        assert d["width"] == 90

        assert d["height"] == 180

    def test_properties(self) -> None:
        b = BBox(0, "t", 0.5, 10, 20, 110, 70)

        assert b.width == 100

        assert b.height == 50

        assert b.area == 5000

    def test_json_serializable(self) -> None:
        b = BBox(1, "cat", 0.8, 0, 0, 100, 100)

        dumped = json.dumps(b.to_dict())

        loaded = json.loads(dumped)

        assert loaded["class_name"] == "cat"


class TestDetectionResult:
    def test_empty_detection(self) -> None:
        r = DetectionResult(image_path="a.png", image_size=(1920, 1080))

        assert r.num_detections == 0

        assert r.to_dict()["num_detections"] == 0

    def test_with_detections(self) -> None:
        boxes = [BBox(0, "a", 0.9, 0, 0, 10, 10), BBox(1, "b", 0.8, 5, 5, 15, 15)]

        r = DetectionResult(image_path="b.png", image_size=(100, 100), detections=boxes, inference_ms=15.0)

        assert r.num_detections == 2

        assert len(r.to_dict()["detections"]) == 2

    def test_json_roundtrip(self) -> None:
        boxes = [BBox(0, "x", 0.7, 1, 2, 3, 4)]

        r = DetectionResult(image_path="c.png", image_size=(50, 50), detections=boxes, inference_ms=5.0)

        d = json.loads(json.dumps(r.to_dict()))

        assert d["image_size"] == [50, 50]

        assert d["detections"][0]["confidence"] == 0.7


class TestBatchResult:
    def test_summary_zero_images(self) -> None:
        b = BatchResult(folder_path="/x")

        assert b.total_images == 0

        assert b.total_detections == 0

        s = b.summary()

        assert s["total_images"] == 0

    def test_summary_counts(self) -> None:
        r1 = DetectionResult(
            "1.png",
            (10, 10),
            detections=[
                BBox(0, "panel", 0.9, 0, 0, 5, 5),
                BBox(1, "text", 0.8, 2, 2, 4, 4),
            ],
        )

        r2 = DetectionResult(
            "2.png",
            (10, 10),
            detections=[
                BBox(0, "panel", 0.85, 1, 1, 6, 6),
            ],
        )

        b = BatchResult(folder_path="/x", results=[r1, r2])

        assert b.total_images == 2

        assert b.total_detections == 3

        s = b.summary()

        assert s["class_counts"]["panel"] == 2

        assert s["class_counts"]["text"] == 1


# ── TorchVisionDetector 集成测试 ─────────────────────────


_TEST_IMAGE_DIR = Path(__file__).parents[2] / "tests_ocr_data"

_HAS_TORCHVISION = False

try:
    d = TorchVisionDetector()

    _HAS_TORCHVISION = True

except Exception:
    pass


@pytest.mark.skipif(not _HAS_TORCHVISION, reason="torch/torchvision 不可用")
class TestTorchVisionDetectorIntegration:
    def test_load_model(self) -> None:
        d = TorchVisionDetector()

        assert d.class_names

        assert len(d.class_names) == 81

    def test_detect_single_runs(self) -> None:
        img = _TEST_IMAGE_DIR / "test_0.png"

        if not img.exists():
            pytest.skip("测试图片不存在")

        d = TorchVisionDetector()

        r = d.detect_single(img)

        assert r.image_size == (640, 480)

        assert r.inference_ms > 0

    def test_detect_folder_creates_outputs(self, tmp_path: Path) -> None:
        if not _TEST_IMAGE_DIR.is_dir():
            pytest.skip("测试图片目录不存在")

        d = TorchVisionDetector()

        batch = d.detect_folder(str(_TEST_IMAGE_DIR), output_dir=str(tmp_path))

        assert batch.total_images > 0

        json_files = list(tmp_path.glob("*.json"))

        assert any(f.name == "_summary.json" for f in json_files)

        png_files = list(tmp_path.glob("*_annotated.png"))

        assert len(png_files) > 0

    def test_detect_auto_single_file(self) -> None:
        img = _TEST_IMAGE_DIR / "test_0.png"

        if not img.exists():
            pytest.skip("测试图片不存在")

        d = TorchVisionDetector()

        r = d.detect(str(img))

        assert isinstance(r, DetectionResult)

    def test_detect_auto_folder(self, tmp_path: Path) -> None:
        if not _TEST_IMAGE_DIR.is_dir():
            pytest.skip("测试图片目录不存在")

        d = TorchVisionDetector()

        r = d.detect(str(_TEST_IMAGE_DIR), output_dir=str(tmp_path))

        assert isinstance(r, BatchResult)

        assert r.total_images > 0
