#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""CalcPack 导入工具 — 将 .calcpack 文件导入到框架适配器目录。

用法::

    python scripts/tools/import_calcpack.py                    # GUI 模式（文件对话框）
    python scripts/tools/import_calcpack.py path/to/game.calcpack  # CLI 模式
    python scripts/tools/import_calcpack.py path/to/game.calcpack --dir custom/path  # 指定目标
"""

from __future__ import annotations

import json
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _path_setup import ensure_root

ensure_root()

ADAPTERS_DIR = Path(__file__).resolve().parents[2] / "framework" / "adapters"


def get_adapters_dir() -> Path:
    """返回框架适配器根目录。"""
    return ADAPTERS_DIR


def import_calcpack(calcpack_path: str | Path, target_dir: str | Path | None = None) -> dict:
    """将 .calcpack 导入到框架适配器目录。

    Args:
        calcpack_path: .calcpack 文件路径
        target_dir: 目标目录（None = framework/adapters/{name}/）

    Returns:
        导入结果信息

    Raises:
        FileNotFoundError: calcpack 文件不存在
        ValueError: calcpack 格式无效
        FileExistsError: 适配器目录已存在
    """
    cp = Path(calcpack_path)
    if not cp.exists():
        raise FileNotFoundError(f"文件不存在: {calcpack_path}")

    with zipfile.ZipFile(cp, "r") as zf:
        # 验证 meta.json
        if "meta.json" not in zf.namelist():
            raise ValueError("calcpack 中缺少 meta.json")

        meta = json.loads(zf.read("meta.json"))
        name = meta.get("name", "").strip()
        if not name:
            raise ValueError("meta.json 中缺少 name 字段")

        # 确定目标目录
        if target_dir is None:
            dest = ADAPTERS_DIR / name
        else:
            dest = Path(target_dir)

        # 检查是否已存在
        if dest.exists():
            raise FileExistsError(f"适配器目录已存在: {dest}\n如需覆盖请手动删除后再试")

        # 解包
        dest.mkdir(parents=True)
        for member in zf.namelist():
            if member.endswith("/"):
                continue
            data = zf.read(member)
            fp = dest / member
            fp.parent.mkdir(parents=True, exist_ok=True)
            fp.write_bytes(data)

        # 返回信息
        files = [m for m in zf.namelist() if not m.endswith("/")]
        return {
            "name": meta.get("name", name),
            "version": meta.get("version", "0.0.0"),
            "description": meta.get("description", ""),
            "directory": str(dest),
            "files": files,
        }


def main() -> None:
    """命令行入口。"""
    import argparse

    parser = argparse.ArgumentParser(description="导入 .calcpack 适配器包")
    parser.add_argument("file", nargs="?", help=".calcpack 文件路径")
    parser.add_argument("--dir", help="目标目录（默认 framework/adapters/{name}/）")
    args = parser.parse_args()

    if args.file:
        # CLI 模式
        try:
            result = import_calcpack(args.file, args.dir)
            print(f"导入成功: {result['name']} v{result['version']}")
            print(f"目录: {result['directory']}")
            print(f"文件: {len(result['files'])} 个")
            for f in result["files"]:
                print(f"  - {f}")
        except Exception as e:
            print(f"导入失败: {e}")
            sys.exit(1)
    else:
        # GUI 模式 — 使用 tkinter 文件对话框
        import tkinter as tk
        from tkinter import filedialog, messagebox

        try:
            root = tk.Tk()
            root.withdraw()

            file_path = filedialog.askopenfilename(
                title="选择 .calcpack 文件",
                filetypes=[("CalcPack 文件", "*.calcpack"), ("所有文件", "*.*")],
            )
            if not file_path:
                return

            result = import_calcpack(file_path, args.dir)
            messagebox.showinfo(
                "导入成功",
                f"适配器: {result['name']} v{result['version']}\n"
                f"目录: {result['directory']}\n"
                f"文件: {len(result['files'])} 个",
            )
        except FileExistsError as e:
            messagebox.showerror("导入失败", str(e))
        except Exception as e:
            messagebox.showerror("导入失败", str(e))


if __name__ == "__main__":
    main()
