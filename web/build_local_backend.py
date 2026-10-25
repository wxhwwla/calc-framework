# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""
一键构建本地搜索服务器（PyInstaller 打包）

用法:
  python web/build_local_backend.py               # 构建 + 打包 + 压缩
  python web/build_local_backend.py --no-zip      # 构建 + 打包，跳过 zip
  python web/build_local_backend.py --no-build    # 仅打包，跳过前端构建

输出:
  dist/Game Calc Platform/
    └── Web 搜索服务器由启动器内嵌 Web 面板启动

从启动器（Game Calc Platform.exe）的「本地 Web 服务器」区域启动即可。
"""

from __future__ import annotations

import os
import subprocess
import sys
import zipfile
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_APP_NAME = "终末地本地搜索服务器"


def _check_pyinstaller() -> None:
    try:
        import PyInstaller  # noqa: F401
    except ImportError:
        print("[REQUIRED] 正在安装 PyInstaller...")
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "pyinstaller"],
            check=True,
        )


def _build_frontend() -> None:
    """构建前端 dist/。"""
    frontend_dir = _REPO_ROOT / "web" / "frontend"
    dist_dir = frontend_dir / "dist"
    if dist_dir.is_dir() and any(dist_dir.iterdir()):
        print("[1/4] 前端 dist/ 已存在，跳过构建")
        return

    print("[1/4] 构建前端...")
    npm_cmd = "npm.cmd" if os.name == "nt" else "npm"
    subprocess.run([npm_cmd, "install"], cwd=str(frontend_dir), check=True)
    subprocess.run([npm_cmd, "run", "build"], cwd=str(frontend_dir), check=True)
    print("  [OK] 前端构建完成")


def _run_pyinstaller() -> Path:
    """直接通过 PyInstaller 打包本地搜索服务器。"""
    print("[2/4] PyInstaller 打包...")
    import tempfile

    work_dir = tempfile.mkdtemp(prefix="build_local_backend_")
    spec_dir = tempfile.mkdtemp(prefix="spec_local_backend_")
    release_dir = _REPO_ROOT / "dist" / _APP_NAME
    entry = str(_REPO_ROOT / "web" / "backend" / "run_packaged_main.py")

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--onefile",
        "--console",
        f"--name={_APP_NAME}",
        f"--distpath={release_dir!s}",
        f"--workpath={work_dir}",
        f"--specpath={spec_dir}",
        "--noconfirm",
        "--clean",
        "--paths",
        str(_REPO_ROOT / "framework" / "src"),
        "--paths",
        str(_REPO_ROOT / "games"),
        "--paths",
        str(_REPO_ROOT / "web" / "backend"),
        "--add-data",
        f"{_REPO_ROOT / 'web' / 'frontend' / 'dist'};web/frontend/dist",
        "--add-data",
        f"{_REPO_ROOT / 'games' / 'endfield'};games/endfield",
        entry,
    ]

    result = subprocess.run(cmd, cwd=str(_REPO_ROOT), capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stdout[-3000:])
        print(result.stderr[-3000:])
        raise RuntimeError(f"PyInstaller 打包失败 (exit={result.returncode})")
    print(result.stdout[-2000:])

    exe_path = release_dir / f"{_APP_NAME}.exe"
    if not exe_path.exists():
        raise FileNotFoundError(f"未找到打包后的 exe: {exe_path}")

    mb_size = exe_path.stat().st_size / 1024 / 1024
    print(f"  [OK] exe 已生成: {exe_path} ({mb_size:.1f} MB)")

    # 复制游戏数据和许可文件
    import shutil

    from release_bundle.release_layout import LICENSE_FILES, RELEASE_DATA_FILES, _launcher_readme

    for dest_rel, src_rel in RELEASE_DATA_FILES:
        src = _REPO_ROOT / src_rel
        if src.is_file():
            dest = release_dir / dest_rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)

    for dest_rel, src_rel in LICENSE_FILES:
        src = _REPO_ROOT / src_rel
        if src.is_file():
            shutil.copy2(src, release_dir / dest_rel)

    # 生成发布说明
    (release_dir / "发布说明.txt").write_text(
        _launcher_readme("?", "?"),
        encoding="utf-8",
    )

    return release_dir


def _create_zip(release_dir: Path) -> Path:
    """将发布目录压缩为 zip。"""
    print("[3/4] 压缩发布包...")
    zip_path = release_dir / "local-backend.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _dirs, files in os.walk(release_dir):
            for fname in files:
                if fname.endswith(".zip"):
                    continue  # 不打包自己
                fpath = Path(root) / fname
                arcname = str(fpath.relative_to(release_dir))
                zf.write(str(fpath), arcname)

    mb_size = zip_path.stat().st_size / 1024 / 1024
    print(f"  [OK] zip 已生成: {zip_path} ({mb_size:.1f} MB)")
    return zip_path


def _show_summary(release_dir: Path, zip_path: Path | None) -> None:
    """打印构建摘要。"""
    exe_path = release_dir / "终末地本地搜索服务器.exe"
    exe_mb = exe_path.stat().st_size / 1024 / 1024

    print()
    print("=" * 60)
    print("  构建完成！")
    print("=" * 60)
    print(f"  exe: {exe_path} ({exe_mb:.1f} MB)")
    if zip_path:
        zip_mb = zip_path.stat().st_size / 1024 / 1024
        print(f"  zip: {zip_path} ({zip_mb:.1f} MB)")
    print()
    print("  [上传到 PythonAnywhere]")
    print("    python web/scripts/deploy_pythonanywhere.py --all")
    print()
    print("  [用户使用]")
    print("    下载 zip → 解压 → 双击「终末地本地搜索服务器.exe」")
    print(f"    {'=' * 40}")
    print()


def main() -> None:
    no_zip = "--no-zip" in sys.argv
    no_build = "--no-build" in sys.argv

    if not no_build:
        _build_frontend()
    else:
        print("[跳过] 前端构建")

    _check_pyinstaller()
    release_dir = _run_pyinstaller()

    zip_path = None
    if not no_zip:
        zip_path = _create_zip(release_dir)

    _show_summary(release_dir, zip_path)


if __name__ == "__main__":
    main()
