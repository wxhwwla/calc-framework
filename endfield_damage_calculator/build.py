#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
终末地伤害计算器 - 打包脚本

使用 PyInstaller onedir 生成「文件夹发布包」：exe 与游戏 JSON、许可文件分开放置，
便于遵守软件（LICENSE）与数据（DATA_LICENSE）分离分发，并支持单独更新数据。

输出：dist/终末地伤害计算器/
  ├── 终末地伤害计算器.exe
  ├── character_weapon_equipment/.../*.json
  ├── DATA_LICENSE、LICENSE、NOTICES.md
  └── 发布说明.txt
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

# 添加项目根目录到路径，确保能导入 please_read_me
sys.path.insert(0, str(Path(__file__).parent))

from packaging.release_layout import (  # noqa: E402
    RELEASE_APP_NAME,
    release_dir_from_dist,
    stage_release_folder,
)
from please_read_me import get_exe_version, get_version  # noqa: E402


def check_pyinstaller() -> bool:
    """检查 PyInstaller 是否已安装。"""
    try:
        import PyInstaller

        print(f"PyInstaller 已安装: {PyInstaller.__version__}")
        return True
    except ImportError:
        print("PyInstaller 未安装，正在安装...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        return True


def build_release() -> Path:
    """构建 onedir 发布包（exe 不内嵌 JSON）。"""
    project_root = Path(__file__).parent
    repo_root = project_root.parent

    excludes = [
        "tests",
        "scripts",
        "packaging",
        "add_character",
        "add_weapon",
        "test_",
    ]
    exclude_args: list[str] = []
    for item in excludes:
        exclude_args.extend(["--exclude-module", item])

    args = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--onedir",
        "--windowed",
        "--noconfirm",
        f"--name={RELEASE_APP_NAME}",
        "--clean",
        *exclude_args,
        str(project_root / "main.py"),
    ]

    print("=" * 60)
    print("开始打包（onedir，游戏数据不写入 exe）...")
    print("=" * 60)

    subprocess.check_call(args, cwd=project_root)

    dist_dir = project_root / "dist"
    release_root = release_dir_from_dist(dist_dir)
    exe_path = release_root / f"{RELEASE_APP_NAME}.exe"
    if not exe_path.is_file():
        raise FileNotFoundError(f"未找到打包产物: {exe_path}")

    stage_release_folder(
        release_root,
        project_root=project_root,
        repo_root=repo_root,
    )
    return release_root


def main() -> None:
    print("=" * 60)
    print(f"终末地伤害计算器 v{get_version()} - 打包工具")
    print("=" * 60)

    if not check_pyinstaller():
        sys.exit(1)

    try:
        release_root = build_release()
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        print(f"\n打包失败: {exc}")
        sys.exit(1)

    print("\n" + "=" * 60)
    print(f"打包完成！EXE v{get_exe_version()}")
    print(f"发布文件夹: {release_root}")
    print("请将整个文件夹分发给用户（勿只发 exe，否则无法加载角色/武器数据）。")
    print("=" * 60)


if __name__ == "__main__":
    main()
