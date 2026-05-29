#!/usr/bin/env python3
"""
截图识装 — YOLO 批量检测命令行工具。

用法:
    # 交互模式（选择文件夹对话框）
    python -m tools.ocr.cli

    # 命令行模式
    python -m tools.ocr.cli --input ./截图文件夹 --model ./终末地检测模型.pt
    python -m tools.ocr.cli -i ./截图 -m ./yolov8n.pt -o ./输出 --conf 0.3
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .detector import YOLODetector


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="截图识装 — YOLO 批量检测",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "示例:\n"
            "  python -m tools.ocr.cli                        # 交互模式（弹出文件夹选择）\n"
            "  python -m tools.ocr.cli -i ./截图 -m model.pt   # 命令行批量处理\n"
            "  python -m tools.ocr.cli -i 截图.png             # 单张图片检测\n"
        ),
    )
    parser.add_argument("-i", "--input", type=str, default=None,
                        help="输入路径：图片文件或文件夹（省略则弹对话框选择）")
    parser.add_argument("-m", "--model", type=str, default=None,
                        help="YOLO 模型 .pt 文件路径（省略则用 YOLOv8n.pt）")
    parser.add_argument("-o", "--output", type=str, default=None,
                        help="输出目录（省略则在输入目录下创建 _detected）")
    parser.add_argument("--conf", type=float, default=0.25,
                        help="置信度阈值 (default: 0.25)")
    parser.add_argument("--iou", type=float, default=0.45,
                        help="IoU 阈值 (default: 0.45)")
    parser.add_argument("--device", type=str, default="cpu",
                        help='推理设备 "cpu" 或 "cuda:0" (default: cpu)')
    parser.add_argument("--no-annotated", action="store_true",
                        help="不保存标注图片")
    parser.add_argument("--no-json", action="store_true",
                        help="不保存 JSON 检测结果")
    return parser.parse_args(argv)


def _ensure_default_model(model_path: str | None) -> Path:
    """如果未指定模型，下载 YOLOv8n 作为默认。"""
    if model_path is not None:
        return Path(model_path)

    home = Path.home() / ".cache" / "endfield_ocr"
    home.mkdir(parents=True, exist_ok=True)
    default_model = home / "yolov8n.pt"

    if not default_model.exists():
        print(f"[信息] 下载默认模型 YOLOv8n → {default_model}")
        from ultralytics import YOLO
        model = YOLO("yolov8n.pt")
        model.export()  # 触发下载
        # YOLO 自动缓存到 torch hub，复制到我们的缓存目录
        import shutil
        cached = Path.home() / ".cache" / "ultralytics" / "yolov8n.pt"
        if cached.exists():
            shutil.copy2(cached, default_model)
            print("[信息] 默认模型就绪")

    if not default_model.exists():
        # fallback: 让 YOLO 直接加载名字
        return Path("yolov8n.pt")

    return default_model


def _pick_folder_dialog() -> str | None:
    """弹出系统文件夹选择对话框（需要 tkinter）。"""
    try:
        import tkinter
        from tkinter import filedialog
        root = tkinter.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        folder = filedialog.askdirectory(title="选择截图文件夹")
        root.destroy()
        return folder if folder else None
    except Exception:
        return None


def _pick_file_dialog() -> str | None:
    """弹出系统文件选择对话框（需要 tkinter）。"""
    try:
        import tkinter
        from tkinter import filedialog
        root = tkinter.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        filepath = filedialog.askopenfilename(
            title="选择 YOLO 模型文件",
            filetypes=[("PyTorch 模型", "*.pt"), ("所有文件", "*.*")],
        )
        root.destroy()
        return filepath if filepath else None
    except Exception:
        return None


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)

    # ── 交互选择输入路径 ──────────────────────────
    input_path = args.input
    if input_path is None:
        folder = _pick_folder_dialog()
        if folder is None:
            print("未选择文件夹，退出。")
            sys.exit(0)
        input_path = folder
        print(f"选择文件夹: {input_path}")

    # ── 交互选择模型 ──────────────────────────────
    model_path = _ensure_default_model(args.model)
    if model_path.name == "yolov8n.pt" and not model_path.exists():
        model_file = _pick_file_dialog()
        if model_file:
            model_path = Path(model_file)
        else:
            print("[警告] 使用 YOLOv8n 通用模型（非终末地专用）")
    else:
        print(f"模型: {model_path}")

    # ── 初始化检测器 ──────────────────────────────
    detector = YOLODetector(
        model_path=str(model_path),
        conf_threshold=args.conf,
        iou_threshold=args.iou,
        device=args.device,
    )
    print(f"类别数: {len(detector.class_names)}")
    print(f"推理设备: {args.device}")
    print()

    # ── 执行检测 ──────────────────────────────────
    result = detector.detect(
        path=input_path,
        output_dir=args.output,
    )

    print(f"\n检测完成! 类别列表: {detector.class_names[:10]}{'...' if len(detector.class_names) > 10 else ''}")


if __name__ == "__main__":
    main()
