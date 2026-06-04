#!/usr/bin/env python3

# SPDX-License-Identifier: AGPL-3.0
"""

TorchVision 检测模型微调训练脚本 (MIT 许可) — 替代 Ultralytics YOLO (AGPL-3.0)。



在自定义数据集上微调 Faster R-CNN / SSD 等 TorchVision 预训练检测模型。



用法:

    python -m tools.ocr.train

    python -m tools.ocr.train --data ./dataset.yaml

    python -m tools.ocr.train --epochs 100

"""

from __future__ import annotations


import argparse

from pathlib import Path


def _parse_args() -> argparse.Namespace:
    """_parse_args 实现。"""
    parser = argparse.ArgumentParser(description="TorchVision 检测模型微调训练 (MIT 许可)")

    parser.add_argument("--data", "-d", type=str, default=None, help="dataset.yaml 路径")

    parser.add_argument("--epochs", "-e", type=int, default=50, help="训练轮数（默认 50）")

    parser.add_argument("--batch", "-b", type=int, default=4, help="batch size（默认 4）")

    parser.add_argument("--device", type=str, default="cpu", help="训练设备（cpu / 0 / 0,1 等，默认 cpu）")

    parser.add_argument("--lr", type=float, default=0.005, help="学习率（默认 0.005）")

    parser.add_argument("--dry-run", action="store_true", help="只打印训练参数，不实际运行")

    parser.add_argument(
        "--model",
        "-m",
        type=str,
        default="fasterrcnn_resnet50_fpn_v2",
        help="TorchVision 模型名（默认 fasterrcnn_resnet50_fpn_v2）",
    )

    return parser.parse_args()


def train_torchvision(
    data_yaml: str | Path,
    model_name: str = "fasterrcnn_resnet50_fpn_v2",
    epochs: int = 50,
    batch: int = 4,
    device: str = "cpu",
    lr: float = 0.005,
    dry_run: bool = False,
) -> None:
    """微调 TorchVision 检测模型。



    注意：你需要准备 COCO 格式的数据集，并提供相应的 dataset.yaml 配置。

    此脚本为骨架代码，实际训练需补充数据加载器和评估逻辑。

    """

    print(f"\n{'=' * 56}")

    print(f"  TorchVision 模型: {model_name} (MIT 许可)")

    print(f"  数据集配置:      {data_yaml}")

    print(f"  训练轮数:        {epochs}")

    print(f"  Batch:           {batch}")

    print(f"  设备:            {device}")

    print(f"  学习率:          {lr}")

    print("=" * 56)

    if dry_run:
        print("[Dry-run] 未实际运行训练")

        return

    print("\n[信息] 训练 TorchVision 检测模型需要:")

    print("  1. 准备 COCO 格式数据集")

    print("  2. 实现 torchvision 数据加载器")

    print("  3. 参考: https://pytorch.org/vision/stable/models.html")

    print("\n[信息] 你也可以直接使用预训练模型进行推理（无需训练）:")

    print("  python -m tools.ocr.cli --input ./截图")


def main() -> None:
    """CLI 入口。"""
    args = _parse_args()

    train_torchvision(
        data_yaml=args.data or "未指定",
        model_name=args.model,
        epochs=args.epochs,
        batch=args.batch,
        device=args.device,
        lr=args.lr,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
