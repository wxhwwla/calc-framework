#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""打包计算器为 .calcpack 文件。"""

import zipfile
from pathlib import Path


def build_calcpack():
    """打包为 .calcpack 文件。"""
    print("=" * 60)
    print("打包计算器")
    print("=" * 60)

    # 源目录
    src_dir = Path(__file__).parent

    # 输出文件
    output_path = src_dir / "my_first_calculator.calcpack"

    # 需要打包的文件
    files_to_pack = [
        "meta.json",
        "formula.dag.json",
        "functions.py",
        "attr_schema.json",
        "ui/layout.json",
    ]

    print(f"\n源目录: {src_dir}")
    print(f"输出文件: {output_path}")

    # 打包
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for file_name in files_to_pack:
            file_path = src_dir / file_name
            if file_path.exists():
                zf.write(file_path, file_name)
                print(f"  ✓ 添加: {file_name}")
            else:
                print(f"  ✗ 缺少: {file_name}")

    # 验证
    print(f"\n打包完成: {output_path}")
    print(f"文件大小: {output_path.stat().st_size / 1024:.1f} KB")

    # 列出包内容
    print("\n包内容:")
    with zipfile.ZipFile(output_path, "r") as zf:
        for info in zf.infolist():
            print(f"  {info.filename} ({info.file_size} bytes)")

    print("\n" + "=" * 60)
    print("✓ 打包成功！")
    print("=" * 60)
    print("\n使用方式:")
    print("  1. 双击 .calcpack 文件（如果关联了应用）")
    print("  2. 或使用 CalcPackViewer 加载:")
    print("     from calc_framework.ui import CalcPackViewer")
    print("     viewer = CalcPackViewer()")
    print(f"     viewer.load_calcpack('{output_path}')")


if __name__ == "__main__":
    import io
    import sys

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

    build_calcpack()
