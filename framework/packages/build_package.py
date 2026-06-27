#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""将子目录打包成 ZIP 子图包。"""

import zipfile
from pathlib import Path


def build_package(source_dir: Path, output_path: Path) -> None:
    """将目录中的 .json 文件打包成 ZIP。

    Args:
        source_dir: 包含 .json 文件的目录
        output_path: 输出 ZIP 文件路径
    """
    if not source_dir.is_dir():
        print(f"错误: 目录不存在 {source_dir}")
        return

    json_files = list(source_dir.glob("*.json"))

    if not json_files:
        print(f"错误: 目录中没有 .json 文件 {source_dir}")
        return

    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for json_file in json_files:
            zf.write(json_file, json_file.name)
            print(f"  添加: {json_file.name}")

    print(f"\n打包完成: {output_path}")
    print(f"文件大小: {output_path.stat().st_size / 1024:.1f} KB")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("用法: python build_package.py <子图目录> [输出文件名]")
        print("示例: python build_package.py 战斗计算包 战斗计算包.zip")
        sys.exit(1)

    source = Path(sys.argv[1])
    output = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(f"{source.name}.zip")

    build_package(source, output)
