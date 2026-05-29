#!/usr/bin/env python3
"""
YOLO 微调训练脚本 — 在终末地截图数据集上微调检测模型。

用法:
    python -m tools.ocr.train                      # 自动找 ./终末地数据集/yolo/dataset.yaml
    python -m tools.ocr.train --data ./dataset.yaml # 指定数据集配置
    python -m tools.ocr.train --epochs 100          # 训练 100 轮
    python -m tools.ocr.train --resume              # 从断点续训
    python -m tools.ocr.train --export-onnx         # 训练完导出 ONNX
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="终末地 YOLO 检测模型微调训练")
    parser.add_argument("--data", "-d", type=str, default=None,
                        help="dataset.yaml 路径（默认自动查找）")
    parser.add_argument("--model", "-m", type=str, default="yolov8n.pt",
                        help="基础模型（默认 yolov8n.pt）")
    parser.add_argument("--epochs", "-e", type=int, default=50,
                        help="训练轮数（默认 50）")
    parser.add_argument("--imgsz", type=int, default=640,
                        help="输入图片尺寸（默认 640）")
    parser.add_argument("--batch", "-b", type=int, default=None,
                        help="batch size（默认自动）")
    parser.add_argument("--device", type=str, default="cpu",
                        help="训练设备（cpu / 0 / 0,1 等，默认 cpu）")
    parser.add_argument("--resume", action="store_true",
                        help="从上次断点继续训练")
    parser.add_argument("--export-onnx", action="store_true",
                        help="训练完导出 ONNX 格式")
    parser.add_argument("--patience", type=int, default=20,
                        help="早停耐心值（默认 20）")
    parser.add_argument("--project", type=str, default="runs/ocr_train",
                        help="输出项目目录")
    parser.add_argument("--name", type=str, default=None,
                        help="实验名称（默认 auto）")
    parser.add_argument("--lr", type=float, default=0.01,
                        help="学习率（默认 0.01）")
    parser.add_argument("--dry-run", action="store_true",
                        help="只打印训练参数，不实际运行")
    return parser.parse_args()


def _find_dataset_yaml() -> Path | None:
    candidates = [
        Path.cwd() / "终末地数据集" / "yolo" / "dataset.yaml",
        Path.cwd() / "dataset.yaml",
        Path.cwd() / "data.yaml",
    ]
    for p in candidates:
        if p.exists():
            return p
    return None


def train_yolo(
    data_yaml: str | Path,
    model: str = "yolov8n.pt",
    epochs: int = 50,
    imgsz: int = 640,
    batch: int | None = None,
    device: str = "cpu",
    resume: bool = False,
    export_onnx: bool = False,
    patience: int = 20,
    project: str = "runs/ocr_train",
    name: str | None = None,
    lr: float = 0.01,
    dry_run: bool = False,
) -> str | None:
    """微调 YOLO 检测模型。

    Args:
        data_yaml: dataset.yaml 路径
        model: 基础模型路径或名称（默认 yolov8n.pt）
        epochs: 训练轮数
        imgsz: 输入图片尺寸
        batch: batch size（None=自动）
        device: 训练设备
        resume: 是否续训
        export_onnx: 是否导出 ONNX
        patience: 早停耐心值
        project: 输出目录
        name: 实验名称
        lr: 学习率
        dry_run: 只打印参数不训练

    Returns:
        最佳模型路径，失败返回 None
    """
    data_path = Path(data_yaml)
    if not data_path.exists():
        print(f"[错误] dataset.yaml 不存在: {data_path}")
        return None

    print("=" * 56)
    print("  终末地 YOLO 模型微调训练")
    print("=" * 56)
    print(f"  数据配置:   {data_path}")
    print(f"  基础模型:   {model}")
    print(f"  训练轮数:   {epochs}")
    print(f"  图片尺寸:   {imgsz}")
    print(f"  Batch:      {batch or 'auto'}")
    print(f"  设备:       {device}")
    print(f"  学习率:     {lr}")
    print(f"  早停:       {patience} 轮")
    print(f"  输出:       {project}")
    print(f"  续训:       {'是' if resume else '否'}")
    print(f"  导出 ONNX:  {'是' if export_onnx else '否'}")
    print("=" * 56)

    if dry_run:
        print("[Dry-run] 未实际运行训练")
        return "yolov8n.pt"  # 返回模拟路径

    try:
        from ultralytics import YOLO
    except ImportError:
        print("[错误] 需要安装 ultralytics: pip install ultralytics")
        return None

    yolo_model = YOLO(model)

    kwargs: dict = {
        "data": str(data_path),
        "epochs": epochs,
        "imgsz": imgsz,
        "patience": patience,
        "project": project,
        "lr0": lr,
        "device": device,
        "verbose": True,
    }
    if batch is not None:
        kwargs["batch"] = batch
    if name is not None:
        kwargs["name"] = name

    if resume:
        print("\n▶ 从断点续训...")
        results = yolo_model.train(resume=True)
    else:
        print(f"\n▶ 开始训练 (基础模型: {model})...")
        results = yolo_model.train(**kwargs)

    best_model = Path(project) / (name or "train") / "weights" / "best.pt"
    if best_model.exists():
        print(f"\n✅ 训练完成！最佳模型: {best_model}")
    else:
        best_model = Path("runs") / "detect" / (name or "train") / "weights" / "best.pt"
        if best_model.exists():
            print(f"\n✅ 训练完成！最佳模型: {best_model}")
        else:
            print(f"\n✅ 训练完成！(模型位置: runs/.../weights/best.pt)")
            best_model = None

    if export_onnx and best_model and best_model.exists():
        from ultralytics import YOLO
        export_model = YOLO(str(best_model))
        onnx_path = export_model.export(format="onnx", imgsz=imgsz)
        print(f"  ONNX 导出: {onnx_path}")

    return str(best_model) if best_model else None


def main() -> None:
    args = _parse_args()

    if not args.data:
        found = _find_dataset_yaml()
        if not found:
            print("[错误] 未找到 dataset.yaml，请指定 --data")
            print("        python -m tools.ocr.train --data path/to/dataset.yaml")
            sys.exit(1)
        args.data = str(found)
        print(f"ℹ️  自动找到数据集: {args.data}")

    train_yolo(
        data_yaml=args.data,
        model=args.model,
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        device=args.device,
        resume=args.resume,
        export_onnx=args.export_onnx,
        patience=args.patience,
        project=args.project,
        name=args.name,
        lr=args.lr,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
