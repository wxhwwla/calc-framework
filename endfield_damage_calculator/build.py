#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
终末地伤害计算器 - 打包脚本

使用 PyInstaller onedir 生成「文件夹发布包」：exe 与游戏 JSON、许可文件分开放置，
便于遵守软件（LICENSE）与数据（DATA_LICENSE）分离分发，并支持单独更新数据。

输出：dist/终末地伤害计算器/
  ├── 终末地伤害计算器.exe
  ├── character_weapon_equipment/.../*.json（含 equipments.json）
  ├── DATA_LICENSE、LICENSE、NOTICES.md
  ├── 发布说明.txt
  └── search_output/（首次全量/MVP 搜索后自动创建，与 exe 同级）
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

# 添加项目根目录到路径，确保能导入 please_read_me
sys.path.insert(0, str(Path(__file__).parent))

from release_bundle.release_layout import (  # noqa: E402
    RELEASE_APP_NAME,
    release_dir_from_dist,
    stage_release_folder,
)
from please_read_me import get_exe_version, get_version  # noqa: E402
from utils.platform_win32_patch import apply_platform_win32_patch  # noqa: E402


def check_build_dependencies() -> bool:
    """检查打包依赖：PyInstaller 及其所需的 PyPI ``packaging``（勿与 release_bundle 混淆）。"""
    import importlib.util
    from importlib.metadata import PackageNotFoundError, version

    print("正在检查打包依赖…", flush=True)
    if importlib.util.find_spec("PyInstaller") is None:
        print("缺少打包依赖。请在 [包] 目录执行：")
        print('  pip install -e ".[build]"')
        return False
    try:
        import packaging.requirements  # noqa: F401
    except ImportError as exc:
        print("缺少打包依赖。请在 [包] 目录执行：")
        print('  pip install -e ".[build]"')
        print(f"详情: {exc}")
        return False
    try:
        pyi_ver = version("pyinstaller")
    except PackageNotFoundError:
        pyi_ver = "未知"
    print(f"PyInstaller 已安装: {pyi_ver}", flush=True)

    from utils.optional_deps import is_matplotlib_available

    if not is_matplotlib_available():
        print("缺少运行时依赖 matplotlib。请在 [包] 目录执行：")
        print('  pip install -e .')
        return False
    print("matplotlib 已安装（将打入发布包）", flush=True)
    return True


def build_release() -> Path:
    """构建 onedir 发布包（exe 不内嵌 JSON）。"""
    project_root = Path(__file__).parent
    repo_root = project_root.parent

    excludes = [
        "tests",
        "scripts",
        "release_bundle",
        "add_character",
        "add_weapon",
        "test_",
    ]
    exclude_args: list[str] = []
    for item in excludes:
        exclude_args.extend(["--exclude-module", item])

    # matplotlib 需随包收集字体/后端，否则 exe 内仪表盘空白或报错
    pyinstaller_collect_args = [
        "--collect-all",
        "matplotlib",
        "--hidden-import",
        "matplotlib.backends.backend_tkagg",
    ]

    args = [
        sys.executable,
        "-m",
        "release_bundle.pyinstaller_entry",
        "--onedir",
        "--windowed",
        "--noconfirm",
        f"--name={RELEASE_APP_NAME}",
        "--clean",
        *pyinstaller_collect_args,
        *exclude_args,
        str(project_root / "main.py"),
    ]

    print("=" * 60)
    print("开始打包（onedir，游戏数据不写入 exe）...")
    print("（PyInstaller 分析依赖可能需数分钟，请耐心等待下方日志）")
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
    apply_platform_win32_patch()

    print("=" * 60)
    print(f"终末地伤害计算器 v{get_version()} - 打包工具")
    print("=" * 60)

    if not check_build_dependencies():
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
