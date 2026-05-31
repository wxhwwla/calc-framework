#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""
截图数据集采集与整理工具 — 为 YOLO 标注做准备。

将游戏截图按面板类型分类到命名子目录，支持重命名、预览、统计。

用法:
    python -m tools.ocr.collect        # 交互模式
    python -m tools.ocr.collect -i ./截图 -o ./终末地数据集
    python -m tools.ocr.collect --stats # 统计已有数据集
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path
from datetime import datetime

# 预定义的面板类型分类
PANEL_CATEGORIES: dict[str, str] = {
    "角色面板": "character_panel",
    "武器面板": "weapon_panel",
    "装备面板": "equipment_panel",
    "技能面板": "skill_panel",
    "乘区数值": "zone_values",
    "敌方面板": "enemy_panel",
    "完整界面": "full_screen",
    "其他": "uncategorized",
}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="截图数据集采集与整理工具",
    )
    parser.add_argument("-i", "--input", default=None,
                        help="源截图文件夹（省略则弹对话框）")
    parser.add_argument("-o", "--output", default=None,
                        help="数据集根目录（默认: ./终末地数据集）")
    parser.add_argument("--stats", action="store_true",
                        help="只统计已有数据集，不做整理")
    return parser.parse_args()


def _pick_folder(title: str) -> str | None:
    try:
        import tkinter
        from tkinter import filedialog
        root = tkinter.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        folder = filedialog.askdirectory(title=title)
        root.destroy()
        return folder if folder else None
    except Exception:
        return None


def _collect_images(src: Path, dst_root: Path, extensions: tuple[str, ...] = (".png", ".jpg", ".jpeg", ".bmp", ".webp")) -> int:
    """交互式分类整理截图。"""
    images = sorted(p for p in src.iterdir() if p.suffix.lower() in extensions)
    if not images:
        print("[信息] 源文件夹无图片")
        return 0

    print(f"找到 {len(images)} 张图片\n")
    print("面板类型:")
    keys = list(PANEL_CATEGORIES.keys())
    for i, name in enumerate(keys, 1):
        print(f"  {i}. {name}")
    print(f"  s. 跳过当前图片")
    print(f"  q. 退出\n")

    copied = 0
    for img in images:
        print(f"\n─── {img.name} ───")
        try:
            from PIL import Image
            pil_img = Image.open(img)
            print(f"    尺寸: {pil_img.size[0]}×{pil_img.size[1]}")
        except Exception:
            print(f"    无法读取")

        choice = input(f"  分类 (1-{len(keys)}/s/q): ").strip().lower()
        if choice == "q":
            break
        if choice == "s":
            continue

        try:
            idx = int(choice) - 1
            if idx < 0 or idx >= len(keys):
                print("  无效输入，跳过")
                continue
            cat_key = keys[idx]
            cat_dir = dst_root / PANEL_CATEGORIES[cat_key]
            cat_dir.mkdir(parents=True, exist_ok=True)

            # 以 "面板类型_序号_原始名" 格式重命名
            existing = list(cat_dir.iterdir())
            seq = len(existing) + 1
            new_name = f"{PANEL_CATEGORIES[cat_key]}_{seq:04d}{img.suffix}"
            shutil.copy2(img, cat_dir / new_name)
            copied += 1
            print(f"  → {cat_key}/{new_name}")
        except (ValueError, IndexError):
            print("  无效输入，跳过")

    return copied


def _print_stats(root: Path) -> None:
    """统计数据集目录结构。"""
    if not root.is_dir():
        print(f"[警告] 数据集目录不存在: {root}")
        return

    print(f"\n📊 数据集统计: {root}")
    print(f"{'='*50}")
    total = 0
    for cat_dir in sorted(root.iterdir()):
        if not cat_dir.is_dir():
            continue
        images = [f for f in cat_dir.iterdir()
                  if f.suffix.lower() in (".png", ".jpg", ".jpeg", ".bmp", ".webp")]
        if not images:
            continue
        count = len(images)
        total += count
        cat_label = next((k for k, v in PANEL_CATEGORIES.items() if v == cat_dir.name), cat_dir.name)
        print(f"  {cat_label}: {count} 张")
    print(f"{'='*50}")
    print(f"  总计: {total} 张")


def main() -> None:
    args = _parse_args()

    # ── 统计模式 ──────────────────────────
    if args.stats:
        root = Path(args.output or "终末地数据集")
        _print_stats(root)
        return

    # ── 选择源文件夹 ──────────────────────
    src_path = args.input
    if src_path is None:
        folder = _pick_folder("选择截图源文件夹")
        if folder is None:
            print("未选择文件夹，退出。")
            sys.exit(0)
        src_path = folder
    src = Path(src_path)
    if not src.is_dir():
        print(f"[错误] 源文件夹不存在: {src}")
        sys.exit(1)

    # ── 目标数据集目录 ────────────────────
    dst_root = Path(args.output or "终末地数据集")
    dst_root.mkdir(parents=True, exist_ok=True)

    # ── 创建分类子目录 ────────────────────
    for cat_dir in PANEL_CATEGORIES.values():
        (dst_root / cat_dir).mkdir(exist_ok=True)

    copied = _collect_images(src, dst_root)
    print(f"\n整理完成: 共复制 {copied} 张图片到 {dst_root}")
    _print_stats(dst_root)


if __name__ == "__main__":
    main()
