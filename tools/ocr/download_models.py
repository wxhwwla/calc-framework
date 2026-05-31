#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""
预下载 EasyOCR 模型（通过镜像）— 解决国内 GitHub 下载慢问题。

用法:
    python tools/ocr/download_models.py          # 用 ghproxy 镜像下载
    python tools/ocr/download_models.py --direct  # 从 GitHub 直连（默认）
    python tools/ocr/download_models.py --verify  # 验证已有模型
"""

from __future__ import annotations

import argparse
import hashlib
import os
import sys
import zipfile
from pathlib import Path
from urllib.request import urlopen, Request

_EASYOCR_CACHE = Path.home() / ".EasyOCR" / "model"

# 中英文需要的模型
REQUIRED_MODELS: list[dict[str, str]] = [
    {
        "name": "craft_mlt_25k (检测模型)",
        "filename": "craft_mlt_25k.pth",
        "zip_url": "https://github.com/JaidedAI/EasyOCR/releases/download/pre-v1.1.6/craft_mlt_25k.zip",
        "md5": None,
    },
    {
        "name": "zh_sim_g2 (中文识别)",
        "filename": "zh_sim_g2.pth",
        "zip_url": "https://github.com/JaidedAI/EasyOCR/releases/download/v1.3/zh_sim_g2.zip",
        "md5": None,
    },
    {
        "name": "english_g2 (英文识别)",
        "filename": "english_g2.pth",
        "zip_url": "https://github.com/JaidedAI/EasyOCR/releases/download/v1.3/english_g2.zip",
        "md5": None,
    },
]

# 国内可用的 GitHub 镜像代理
MIRRORS = [
    "https://ghproxy.net/",       # ghproxy
    "https://mirror.ghproxy.com/", # ghproxy 镜像
]


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="预下载 EasyOCR 模型（镜像加速）")
    parser.add_argument("--direct", action="store_true", help="直连 GitHub 下载（不用镜像）")
    parser.add_argument("--verify", action="store_true", help="只校验已有文件，不下载")
    parser.add_argument("--mirror", type=str, default=None,
                        help="自定义镜像地址，如 https://ghproxy.net/")
    return parser.parse_args()


def _download_with_progress(url: str, dest: Path, chunk_size: int = 8192) -> None:
    """带进度条的文件下载。"""
    req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    resp = urlopen(req, timeout=120)
    total = int(resp.headers.get("content-length", 0))
    downloaded = 0
    with open(dest, "wb") as f:
        while True:
            chunk = resp.read(chunk_size)
            if not chunk:
                break
            f.write(chunk)
            downloaded += len(chunk)
            if total:
                pct = downloaded / total * 100
                bar_len = 30
                filled = int(bar_len * downloaded / total)
                bar = "█" * filled + "─" * (bar_len - filled)
                sys.stdout.write(f"\r  [{bar}] {pct:.1f}% ({downloaded/1024/1024:.1f}/{total/1024/1024:.1f} MB)")
            else:
                sys.stdout.write(f"\r  已下载 {downloaded/1024/1024:.1f} MB")
            sys.stdout.flush()
    print()


def _verify_model(path: Path, name: str) -> bool:
    if not path.exists():
        print(f"  ❌ {name}: 文件不存在")
        return False
    size_mb = path.stat().st_size / 1024 / 1024
    print(f"  ✅ {name}: {path.name} ({size_mb:.1f} MB)")
    return True


def main() -> None:
    args = _parse_args()

    _EASYOCR_CACHE.mkdir(parents=True, exist_ok=True)

    # ── 校验模式 ──────────────────────────
    if args.verify:
        print(f"EasyOCR 模型缓存: {_EASYOCR_CACHE}")
        all_ok = True
        for model in REQUIRED_MODELS:
            pth_path = _EASYOCR_CACHE / model["filename"]
            ok = _verify_model(pth_path, model["name"])
            all_ok = all_ok and ok
        # 检查是否有多余文件
        for f in _EASYOCR_CACHE.iterdir():
            if f.suffix == ".pth" and f.name not in [m["filename"] for m in REQUIRED_MODELS]:
                print(f"  ℹ️  额外模型: {f.name} ({f.stat().st_size/1024/1024:.1f} MB)")
        print(f"\n{'全部就绪 ✅' if all_ok else '部分缺失，请运行下载'}")
        return

    # ── 下载模式 ──────────────────────────
    print(f"EasyOCR 模型缓存: {_EASYOCR_CACHE}")
    print()

    for model in REQUIRED_MODELS:
        pth_path = _EASYOCR_CACHE / model["filename"]
        zip_path = _EASYOCR_CACHE / f"{model['filename']}.zip"

        if pth_path.exists():
            print(f"✅ {model['name']}: 已存在 ({pth_path.stat().st_size/1024/1024:.1f} MB)")
            continue

        # 构建下载 URL
        if args.mirror:
            zip_url = args.mirror.rstrip("/") + "/" + model["zip_url"]
        elif args.direct:
            zip_url = model["zip_url"]
        else:
            # 尝试镜像
            zip_url = MIRRORS[0].rstrip("/") + "/" + model["zip_url"]

        print(f"\n📥 下载 {model['name']}")
        print(f"   源: {zip_url[:80]}...")
        print(f"   目标: {zip_path}")

        try:
            _download_with_progress(zip_url, zip_path)
        except Exception as e:
            print(f"   ❌ 下载失败: {e}")
            if not args.direct and not args.mirror:
                print(f"   → 尝试直连...")
                try:
                    _download_with_progress(model["zip_url"], zip_path)
                except Exception as e2:
                    print(f"   ❌ 直连也失败: {e2}")
                    print(f"   💡 试试: python tools/ocr/download_models.py --mirror https://ghproxy.net/")
                    continue
            else:
                continue

        # 解压
        print(f"   📦 解压中...")
        try:
            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(_EASYOCR_CACHE)
            zip_path.unlink()
            print(f"   ✅ 解压完成")
        except Exception as e:
            print(f"   ❌ 解压失败: {e}")
            continue

        _verify_model(pth_path, model["name"])
        print()

    print("=" * 50)
    print("下载完成！运行以下命令验证:")
    print("  python tools/ocr/download_models.py --verify")


if __name__ == "__main__":
    main()
