#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# SPDX-License-Identifier: AGPL-3.0
"""

构建并发布 calc-framework 到 PyPI。



用法:

    python tools/framework_publish.py build          # 只构建 wheel

    python tools/framework_publish.py publish        # 构建 + 上传到 PyPI

    python tools/framework_publish.py test           # 上传到 TestPyPI



需要已安装 build 和 twine: pip install build twine

上传需要配置 PyPI API token 到环境变量 PYPI_API_TOKEN。

"""

from __future__ import annotations


import os

import subprocess

import sys

from pathlib import Path


FRAMEWORK_DIR = Path(__file__).resolve().parent.parent / "framework"

DIST_DIR = FRAMEWORK_DIR / "dist"


def _check_deps() -> None:
    """_check_deps 实现。"""
    for mod in ("build", "twine"):
        try:
            __import__(mod)

        except ImportError:
            print(f"请先安装 {mod}: pip install build twine")

            sys.exit(1)


def _run(cmd: list[str], cwd: Path) -> None:
    """打印并执行命令。

    Args:
        cmd: 命令列表
        cwd: 工作目录
    """

    print(f"→ {' '.join(cmd)}")

    subprocess.check_call(cmd, cwd=cwd)


def cmd_build() -> None:
    """cmd_build 实现。"""
    _check_deps()

    # 清理旧构建

    for p in DIST_DIR.glob("*"):
        p.unlink()

    _run([sys.executable, "-m", "build"], FRAMEWORK_DIR)

    print(f"\n✅ 构建完成: {DIST_DIR}")

    for f in sorted(DIST_DIR.iterdir()):
        print(f"   {f.name}")


def cmd_publish() -> None:
    """cmd_publish 实现。"""
    cmd_build()

    token = os.environ.get("PYPI_API_TOKEN")

    if not token:
        print("错误: 需要设置 PYPI_API_TOKEN 环境变量")

        sys.exit(1)

    _run(
        [sys.executable, "-m", "twine", "upload", "--username", "__token__", "--password", token, "dist/*"],
        FRAMEWORK_DIR,
    )

    print("\n✅ 已发布到 PyPI")


def cmd_test_publish() -> None:
    """构建并上传框架包到 TestPyPI。"""

    cmd_build()

    _run(
        [sys.executable, "-m", "twine", "upload", "--repository-url", "https://test.pypi.org/legacy/", "dist/*"],
        FRAMEWORK_DIR,
    )

    print("\n✅ 已发布到 TestPyPI")


def main() -> None:
    """CLI 入口：解析命令并执行对应操作。"""

    if len(sys.argv) < 2:
        print(__doc__)

        sys.exit(1)

    command = sys.argv[1]

    funcs = {
        "build": cmd_build,
        "publish": cmd_publish,
        "test": cmd_test_publish,
    }

    if command not in funcs:
        print(f"未知命令: {command}")

        print(__doc__)

        sys.exit(1)

    funcs[command]()


if __name__ == "__main__":
    main()
