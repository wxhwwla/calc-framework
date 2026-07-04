# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""OCR 截图识装管道 — 纯函数模块，执行目标检测 + OCR 识别 + 映射。

不依赖 PySide6，可被 GUI/Web/CLI 复用。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from games.endfield.framework_bridge import get_logger

__all__ = ["ImageDetail", "OcrPipelineResult", "format_detail_lines", "preset_summary", "run_pipeline"]

_logger = get_logger("gui.ocr_pipeline")


@dataclass
class ImageDetail:
    """单张图片的检测详情。"""

    image_name: str
    detections: list[dict[str, Any]] = field(default_factory=list)
    ocr_texts: list[dict[str, Any]] = field(default_factory=list)
    ocr_error: str | None = None


@dataclass
class OcrPipelineResult:
    """OCR 管道完整结果。"""

    total_images: int = 0
    total_detections: int = 0
    avg_inference_ms: float = 0.0
    image_details: list[ImageDetail] = field(default_factory=list)
    mapped_preset: dict[str, Any] | None = None
    error: str | None = None


def run_pipeline(folder: str | Path, *, max_detail_images: int = 20) -> OcrPipelineResult:
    """对截图文件夹执行完整的 OCR 管道：检测 → 识别 → 映射。

    Args:
        folder: 截图文件夹路径
        max_detail_images: 最多保留详情的图片数（避免内存过大）

    Returns:
        OcrPipelineResult 包含检测统计、逐图详情和映射结果
    """
    result = OcrPipelineResult()

    try:
        from tools.ocr.detector import TorchVisionDetector
        from tools.ocr.mapper import OcrMapper
        from tools.ocr.recognizer import OCRRecognizer
    except ImportError:
        result.error = "导入失败: 请安装 torchvision 和 easyocr"
        return result

    try:
        detector = TorchVisionDetector(conf_threshold=0.25)
        ocr = OCRRecognizer()
        mapper = OcrMapper()

        batch = detector.detect_folder(
            str(folder),
            save_json=False,
            save_annotated=False,
        )

        result.total_images = batch.total_images
        result.total_detections = batch.total_detections
        result.avg_inference_ms = batch.summary().get("avg_inference_ms", 0.0)

        all_ocr_texts: list[tuple[str, float, str | None]] = []
        mapped_preset = None

        for r in batch.results:
            detail = ImageDetail(image_name=Path(r.image_path).name)

            # 检测详情
            for d in r.detections[:10]:
                detail.detections.append(
                    {
                        "confidence": d.confidence,
                        "class_name": d.class_name,
                        "x1": d.x1,
                        "y1": d.y1,
                        "x2": d.x2,
                        "y2": d.y2,
                    }
                )

            # OCR 识别
            try:
                ocr_result = ocr.recognize(r.image_path)
                for t in ocr_result.texts[:15]:
                    detail.ocr_texts.append({"text": t.text, "confidence": t.confidence})
                    all_ocr_texts.append((t.text, t.confidence, None))
                # 尝试映射（取第一个成功的）
                if mapped_preset is None:
                    mapped = mapper.map_texts([(t.text, t.confidence, None) for t in ocr_result.texts])
                    if mapped.is_valid:
                        mapped_preset = mapped.to_loadout_preset_dict()
            except Exception as e:
                detail.ocr_error = str(e)
                _logger.debug("单张截图 OCR 识别失败（已跳过）: %s", r.image_path)

            if len(result.image_details) < max_detail_images:
                result.image_details.append(detail)

        # 如果逐图映射失败，尝试合并所有文本映射
        if mapped_preset is None and all_ocr_texts:
            mapped = mapper.map_texts(all_ocr_texts)
            if mapped.is_valid:
                mapped_preset = mapped.to_loadout_preset_dict()

        result.mapped_preset = mapped_preset

    except Exception as e:
        result.error = str(e)
        _logger.exception("OCR 检测异常")

    return result


def preset_summary(preset: dict[str, Any]) -> str:
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


def format_detail_lines(result: OcrPipelineResult, folder: str | Path) -> list[str]:
    """将管道结果格式化为可读文本行（用于 GUI 显示）。"""
    lines: list[str] = []
    lines.append(f"截图文件夹: {folder}")

    if result.error:
        lines.append(f"[错误] {result.error}")
        return lines

    lines.append(f"总图片数: {result.total_images}")
    lines.append(f"总检测目标: {result.total_detections}")
    lines.append(f"平均推理: {result.avg_inference_ms:.0f} ms/张")
    lines.append("")

    for detail in result.image_details:
        lines.append(f"── {detail.image_name} ──")
        for d in detail.detections:
            coord = f"({d['x1']:.0f},{d['y1']:.0f},{d['x2']:.0f},{d['y2']:.0f})"
            lines.append(f"  [{d['confidence']:.2f}] {d['class_name']} {coord}")
        if detail.ocr_texts:
            lines.append("  OCR:")
            for t in detail.ocr_texts:
                lines.append(f"    [{t['confidence']:.2f}] {t['text']}")
        if detail.ocr_error:
            lines.append(f"  OCR 失败: {detail.ocr_error}")
        lines.append("")

    if result.total_images > len(result.image_details):
        lines.append(f"... 还有 {result.total_images - len(result.image_details)} 张未显示")

    if result.mapped_preset:
        lines.append(f"→ 识别: {preset_summary(result.mapped_preset)}")
    else:
        lines.append("\n→ 未能识别出角色和武器名称")

    return lines
