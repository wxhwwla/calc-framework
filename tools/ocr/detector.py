# SPDX-License-Identifier: AGPL-3.0
"""

YOLOX 目标检测器 — 基于 YOLOX (Apache 2.0) 替代 Ultralytics YOLO (AGPL-3.0)。



许可证：YOLOX 由旷视 (Megvii) 以 Apache 2.0 发布，可自由用于商业项目。



用法（命令行）:

    python -m tools.ocr.cli --input <截图文件夹> --model <模型.pth>



用法（代码）:

    from tools.ocr.detector import YOLOXDetector

    d = YOLOXDetector("yolox_s.pth")

    result = d.detect_single("screenshot.png")

    batch = d.detect_folder("screenshots/", output_dir="output/")

"""

from __future__ import annotations


import json

import time

from dataclasses import dataclass, field

from pathlib import Path

from typing import Any


import numpy as np

from PIL import Image, ImageDraw, ImageFont


torch: Any = None

_detection_model: Any = None

_VISION_AVAILABLE = False


try:
    import torch

    from torchvision.models.detection import (
        fasterrcnn_resnet50_fpn_v2 as _detection_model,
    )

    _VISION_AVAILABLE = True

except ImportError:
    pass


_COCO_CLASSES: list[str] = [
    "__background__",
    "person",
    "bicycle",
    "car",
    "motorcycle",
    "airplane",
    "bus",
    "train",
    "truck",
    "boat",
    "traffic light",
    "fire hydrant",
    "stop sign",
    "parking meter",
    "bench",
    "bird",
    "cat",
    "dog",
    "horse",
    "sheep",
    "cow",
    "elephant",
    "bear",
    "zebra",
    "giraffe",
    "backpack",
    "umbrella",
    "handbag",
    "tie",
    "suitcase",
    "frisbee",
    "skis",
    "snowboard",
    "sports ball",
    "kite",
    "baseball bat",
    "baseball glove",
    "skateboard",
    "surfboard",
    "tennis racket",
    "bottle",
    "wine glass",
    "cup",
    "fork",
    "knife",
    "spoon",
    "bowl",
    "banana",
    "apple",
    "sandwich",
    "orange",
    "broccoli",
    "carrot",
    "hot dog",
    "pizza",
    "donut",
    "cake",
    "chair",
    "couch",
    "potted plant",
    "bed",
    "dining table",
    "toilet",
    "tv",
    "laptop",
    "mouse",
    "remote",
    "keyboard",
    "cell phone",
    "microwave",
    "oven",
    "toaster",
    "sink",
    "refrigerator",
    "book",
    "clock",
    "vase",
    "scissors",
    "teddy bear",
    "hair drier",
    "toothbrush",
]


@dataclass
class BBox:
    """单个检测框。"""

    class_id: int

    class_name: str

    confidence: float

    x1: float

    y1: float

    x2: float

    y2: float

    @property
    def width(self) -> float:
        """width 实现。"""
        return self.x2 - self.x1

    @property
    def height(self) -> float:
        """height 实现。"""
        return self.y2 - self.y1

    @property
    def area(self) -> float:
        """area 实现。"""
        return self.width * self.height

    def to_dict(self) -> dict[str, Any]:
        """to_dict 实现。"""
        return {
            "class_id": self.class_id,
            "class_name": self.class_name,
            "confidence": round(self.confidence, 4),
            "x1": round(self.x1, 1),
            "y1": round(self.y1, 1),
            "x2": round(self.x2, 1),
            "y2": round(self.y2, 1),
            "width": round(self.width, 1),
            "height": round(self.height, 1),
        }


@dataclass
class DetectionResult:
    """单张图片的检测结果。"""

    image_path: str

    image_size: tuple[int, int]

    detections: list[BBox] = field(default_factory=list)

    inference_ms: float = 0.0

    @property
    def num_detections(self) -> int:
        """num_detections 实现。"""
        return len(self.detections)

    def to_dict(self) -> dict[str, Any]:
        """to_dict 实现。"""
        return {
            "image_path": self.image_path,
            "image_size": list(self.image_size),
            "num_detections": self.num_detections,
            "inference_ms": round(self.inference_ms, 1),
            "detections": [d.to_dict() for d in self.detections],
        }


@dataclass
class BatchResult:
    """文件夹批量处理结果。"""

    folder_path: str

    results: list[DetectionResult] = field(default_factory=list)

    total_time_ms: float = 0.0

    @property
    def total_images(self) -> int:
        """total_images 实现。"""
        return len(self.results)

    @property
    def total_detections(self) -> int:
        """total_detections 实现。"""
        return sum(r.num_detections for r in self.results)

    def summary(self) -> dict[str, Any]:
        """summary 实现。"""
        class_counts: dict[str, int] = {}

        for r in self.results:
            for d in r.detections:
                class_counts[d.class_name] = class_counts.get(d.class_name, 0) + 1

        return {
            "folder": self.folder_path,
            "total_images": self.total_images,
            "total_detections": self.total_detections,
            "avg_inference_ms": round(sum(r.inference_ms for r in self.results) / max(self.total_images, 1), 1),
            "total_time_ms": round(self.total_time_ms, 1),
            "class_counts": dict(sorted(class_counts.items(), key=lambda x: -x[1])),
        }


_CLASS_COLORS: list[tuple[int, int, int]] = [
    (255, 0, 0),
    (0, 255, 0),
    (0, 0, 255),
    (255, 255, 0),
    (255, 0, 255),
    (0, 255, 255),
    (128, 0, 0),
    (0, 128, 0),
    (0, 0, 128),
    (128, 128, 0),
    (128, 0, 128),
    (0, 128, 128),
]


def _get_color(class_id: int) -> tuple[int, int, int]:
    """_get_color 实现。"""
    return _CLASS_COLORS[class_id % len(_CLASS_COLORS)]


def _to_tensor(image: Image.Image, device: str = "cpu") -> Any:
    """PIL Image → 归一化 [1,3,H,W] tensor。"""

    img = image.convert("RGB")

    arr = np.array(img, dtype=np.float32) / 255.0

    arr = arr.transpose(2, 0, 1)

    return torch.from_numpy(arr).unsqueeze(0).to(device)


class YOLOXDetector:
    """基于 TorchVision (MIT) 的目标检测器，接口兼容 Detectron2 / Ultralytics。



    TorchVision 的预训练模型使用 MIT 许可证，可自由用于商业项目。

    默认使用 Faster R-CNN ResNet50 FPN v2。

    """

    def __init__(
        self,
        model_path: str | Path | None = None,
        conf_threshold: float = 0.5,
        iou_threshold: float = 0.5,
        device: str = "cpu",
    ) -> None:
        if not _VISION_AVAILABLE:
            raise ImportError(
                "需要安装 torch + torchvision: "
                "pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu"
            )

        self._conf = conf_threshold

        self._iou = iou_threshold

        self._device = device

        self._model_path = str(model_path) if model_path else None

        self._model = _detection_model(
            weights="DEFAULT",
            box_score_thresh=conf_threshold,
            box_nms_thresh=iou_threshold,
        )

        self._model.to(device)

        self._model.eval()

    @property
    def class_names(self) -> list[str]:
        """class_names 实现。"""
        return _COCO_CLASSES

    # ── Public API ─────────────────────────────────────

    def detect_single(self, image_path: str | Path) -> DetectionResult:
        """检测单张图片，返回结构化的检测结果。"""

        path = Path(image_path)

        if not path.exists():
            raise FileNotFoundError(f"图片不存在: {image_path}")

        img = Image.open(path)

        w, h = img.size

        tensor = _to_tensor(img, self._device)

        t0 = time.perf_counter()

        with torch.no_grad():
            predictions = self._model(tensor)

        elapsed_ms = (time.perf_counter() - t0) * 1000

        detections: list[BBox] = []

        boxes = predictions[0].get("boxes", torch.empty(0, 4))

        scores = predictions[0].get("scores", torch.empty(0))

        labels = predictions[0].get("labels", torch.empty(0, dtype=torch.int64))

        for i in range(len(boxes)):
            x1, y1, x2, y2 = boxes[i].tolist()

            conf = float(scores[i])

            cls_id = int(labels[i])

            detections.append(
                BBox(
                    class_id=cls_id,
                    class_name=self.class_names[cls_id] if cls_id < len(self.class_names) else f"class_{cls_id}",
                    confidence=conf,
                    x1=x1,
                    y1=y1,
                    x2=x2,
                    y2=y2,
                )
            )

        return DetectionResult(
            image_path=str(path),
            image_size=(w, h),
            detections=detections,
            inference_ms=elapsed_ms,
        )

    def detect_folder(
        self,
        folder_path: str | Path,
        output_dir: str | Path | None = None,
        extensions: tuple[str, ...] = (".png", ".jpg", ".jpeg", ".bmp", ".webp"),
        save_json: bool = True,
        save_annotated: bool = True,
    ) -> BatchResult:
        """批量检测文件夹内所有图片。"""

        folder = Path(folder_path)

        if not folder.is_dir():
            raise NotADirectoryError(f"路径不是文件夹: {folder_path}")

        image_paths = sorted(p for p in folder.iterdir() if p.suffix.lower() in extensions)

        if not image_paths:
            print(f"[警告] 文件夹内无图片文件: {folder_path}")

            return BatchResult(folder_path=str(folder))

        if output_dir is None:
            output_dir = folder / "_detected"

        out = Path(output_dir)

        out.mkdir(parents=True, exist_ok=True)

        t_start = time.perf_counter()

        results: list[DetectionResult] = []

        for idx, img_path in enumerate(image_paths, 1):
            print(f"[{idx}/{len(image_paths)}] 处理: {img_path.name}")

            result = self.detect_single(img_path)

            results.append(result)

            stem = img_path.stem

            if save_json:
                json_path = out / f"{stem}.json"

                with open(json_path, "w", encoding="utf-8") as f:
                    json.dump(result.to_dict(), f, ensure_ascii=False, indent=2)

            if save_annotated:
                anno_path = out / f"{stem}_annotated{img_path.suffix}"

                self._draw_annotations(img_path, result.detections, anno_path)

            print(f"  -> {result.num_detections} 个检测目标 ({result.inference_ms:.0f} ms)")

        batch = BatchResult(
            folder_path=str(folder),
            results=results,
            total_time_ms=(time.perf_counter() - t_start) * 1000,
        )

        summary_path = out / "_summary.json"

        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(batch.summary(), f, ensure_ascii=False, indent=2)

        print(f"\n完成! 处理 {len(results)} 张图片, {batch.total_detections} 个检测目标")

        print(f"平均推理: {batch.summary()['avg_inference_ms']} ms/张")

        print(f"输出目录: {out}")

        return batch

    def detect(
        self,
        path: str | Path,
        output_dir: str | Path | None = None,
    ) -> DetectionResult | BatchResult:
        """自动判断路径类型：单图 -> detect_single，文件夹 -> detect_folder。"""

        p = Path(path)

        if p.is_file():
            return self.detect_single(p)

        return self.detect_folder(p, output_dir=output_dir)

    # ── Internal helpers ───────────────────────────────

    def _draw_annotations(
        self,
        image_path: Path,
        detections: list[BBox],
        output_path: Path,
    ) -> None:
        """在图片上绘制检测框并保存。"""

        img = Image.open(image_path).convert("RGB")

        draw = ImageDraw.Draw(img)

        try:
            font = ImageFont.truetype("arial.ttf", size=16)

        except OSError:
            try:
                font = ImageFont.truetype("segoeui.ttf", size=16)

            except OSError:
                font = ImageFont.load_default()

        for det in detections:
            color = _get_color(det.class_id)

            draw.rectangle([det.x1, det.y1, det.x2, det.y2], outline=color, width=2)

            label = f"{det.class_name} {det.confidence:.2f}"

            bbox = draw.textbbox((det.x1, det.y1), label, font=font)

            draw.rectangle(bbox, fill=color)

            draw.text((det.x1, det.y1), label, fill=(0, 0, 0), font=font)

        img.save(output_path)
