#!/usr/bin/env python3

# SPDX-License-Identifier: AGPL-3.0
"""

打包脚本 — 根入口



使用方法：

    python main_build.py                     # 默认打包全部

    python main_build.py --target calculator # 仅打包计算器

    python main_build.py --target designer   # 仅打包数据设计器

    python main_build.py --target pack-designer # 仅打包配置包设计器



输出：

  dist/终末地伤害计算器/  ── 伤害计算器

  dist/数据设计器/  ── 数据设计器

  dist/配置包设计器/  ── 配置包设计器

"""



from __future__ import annotations



import argparse

import os

import shutil

import subprocess

import sys

import tempfile

import time

from pathlib import Path



_REPO_ROOT = Path(__file__).resolve().parent

if str(_REPO_ROOT) not in sys.path:

    sys.path.insert(0, str(_REPO_ROOT))



_GAMES = _REPO_ROOT / "games" / "endfield"

if str(_GAMES) not in sys.path:

    sys.path.insert(0, str(_GAMES))



from please_read_me import get_exe_version, get_version

from release_bundle.release_layout import (

    BuildTarget,

    release_dir_from_dist,

    stage_release_folder,

    target_app_name,

    target_entry,

)

from utils.platform_win32_patch import apply_platform_win32_patch



DEFAULT_BUILD_TIMEOUT_SECONDS = 20 * 60

DEFAULT_HEARTBEAT_SECONDS = 15





def _read_int_env(name: str, default: int) -> int:

    raw = os.getenv(name, "").strip()

    if not raw:

        return default

    try:

        value = int(raw)

    except ValueError:

        return default

    return value if value > 0 else default





def _terminate_process_tree(proc: subprocess.Popen[bytes]) -> None:

    if proc.poll() is not None:

        return

    try:

        if os.name == "nt":

            subprocess.run(

                ["taskkill", "/PID", str(proc.pid), "/T", "/F"],

                check=False,

                stdout=subprocess.DEVNULL,

                stderr=subprocess.DEVNULL,

            )

        else:

            proc.kill()

    except Exception:

        try:

            proc.kill()

        except Exception:

            pass





def _run_with_watchdog(

    cmd: list[str],

    *,

    cwd: Path,

    timeout_seconds: int,

    heartbeat_seconds: int,

) -> subprocess.CompletedProcess[bytes]:

    proc = subprocess.Popen(cmd, cwd=str(cwd))

    deadline = time.monotonic() + timeout_seconds



    while True:

        elapsed = time.monotonic()

        remaining = deadline - elapsed

        if remaining <= 0:

            _terminate_process_tree(proc)

            raise TimeoutError(

                f"打包超时 {timeout_seconds}s，已终止进程树 (PID={proc.pid})"

            )



        ret = proc.poll()

        if ret is not None:

            return subprocess.CompletedProcess(cmd, ret)



        if int(elapsed) % heartbeat_seconds == 0:

            print(f"[看门狗] 运行中… ({int(remaining)}s 剩余)")

        time.sleep(1)





def _build_target(

    target: BuildTarget,

    base_dir: Path,

    dist_dir: Path,

    *,

    extra_args: list[str] | None = None,

) -> Path:

    app_name = target_app_name(target)

    release_root = release_dir_from_dist(dist_dir, target=target)

    entry = target_entry(target)

    print(f"\n{'=' * 60}")

    print(f"  [{target}] {app_name}")

    print(f"  入口: {entry}")

    print(f"  输出: {release_root}")

    print(f"{'=' * 60}")



    work_dir = tempfile.mkdtemp(prefix=f"build_{target}_", dir=base_dir)

    spec_dir = tempfile.mkdtemp(prefix=f"spec_{target}_", dir=base_dir)

    cmd: list[str] = [

        sys.executable,

        "-m",

        "PyInstaller",

        "--onefile",

        "--windowed",

        f"--name={app_name}",

        f"--distpath={release_root}",

        f"--workpath={work_dir}",

        f"--specpath={spec_dir}",

        "--noconfirm",

        "--clean",

    ]

    is_local_backend = target == "local-backend"

    if extra_args:
        cmd.extend(extra_args)

    if not is_local_backend:
        donation_data = f"{base_dir / 'resources' / 'donation'};resources/donation"
        cmd.extend(["--add-data", donation_data])

    if is_local_backend:
        # 控制台模式（服务器需要在终端运行）
        cmd[cmd.index("--windowed")] = "--console"
        cmd.extend([
            "--paths", str(base_dir / "framework" / "src"),
            "--paths", str(base_dir / "games"),
            "--paths", str(base_dir / "web" / "backend"),
            # 内嵌前端构建产物
            "--add-data", f"{base_dir / 'web' / 'frontend' / 'dist'};web/frontend/dist",
            # 内嵌游戏数据（用于 _path_setup.py 路径解析）
            "--add-data", f"{base_dir / 'games' / 'endfield'};games/endfield",
        ])
    elif target == "calculator":
        cmd.extend([
            "--paths", str(base_dir / "games"),
            "--paths", str(base_dir / "games" / "endfield"),
        ])
    elif target == "designer":
        cmd.extend(["--paths", str(base_dir / "tools")])
    elif target == "pack-designer":
        cmd.extend(["--paths", str(base_dir / "tools")])

    cmd.append(entry)



    timeout = _read_int_env("ENDFIELD_BUILD_TIMEOUT_SECONDS", DEFAULT_BUILD_TIMEOUT_SECONDS)

    heartbeat = _read_int_env("ENDFIELD_BUILD_HEARTBEAT_SECONDS", DEFAULT_HEARTBEAT_SECONDS)



    result = _run_with_watchdog(

        cmd, cwd=base_dir, timeout_seconds=timeout, heartbeat_seconds=heartbeat,

    )



    shutil.rmtree(work_dir, ignore_errors=True)

    shutil.rmtree(spec_dir, ignore_errors=True)



    if result.returncode != 0:

        raise RuntimeError(f"PyInstaller 打包 [{target}] 失败 (exit={result.returncode})")



    exe_path = release_root / f"{app_name}.exe"

    if not exe_path.exists():

        raise FileNotFoundError(f"打包成功但未找到 exe: {exe_path}")

    print(f"  → 已生成: {exe_path} ({exe_path.stat().st_size / 1024 / 1024:.1f} MB)")

    return exe_path





def _ensure_frontend_built(base_dir: Path) -> None:
    """确保 web/frontend/dist/ 存在，不存在则构建。"""
    dist_dir = base_dir / "web" / "frontend" / "dist"
    if dist_dir.is_dir() and any(dist_dir.iterdir()):
        print("[前置] 前端 dist/ 已存在，跳过构建")
        return
    print("[前置] 构建前端...")
    frontend_dir = base_dir / "web" / "frontend"
    npm_cmd = "npm.cmd" if os.name == "nt" else "npm"
    subprocess.run([npm_cmd, "install"], cwd=str(frontend_dir), check=True)
    subprocess.run([npm_cmd, "run", "build"], cwd=str(frontend_dir), check=True)
    print("[前置] 前端构建完成")


def main() -> None:
    apply_platform_win32_patch()



    parser = argparse.ArgumentParser(description="终末地伤害计算器 — 打包脚本")

    parser.add_argument("--target", choices=["calculator", "designer", "pack-designer", "local-backend", "all"], default="all")
    parser.add_argument("--no-bump", action="store_true", help="不通过 please_read_me 带版本号打包")
    parser.add_argument("--no-frontend-build", action="store_true", help="local-backend 时跳过前端构建")
    args = parser.parse_args()

    base_dir = Path(__file__).resolve().parent
    dist_dir = base_dir / "dist"
    dist_dir.mkdir(parents=True, exist_ok=True)

    if args.target == "all":
        targets: list[BuildTarget] = ["calculator", "designer", "pack-designer"]
    else:
        targets: list[BuildTarget] = [args.target]

    # local-backend 需要前端构建产物
    if "local-backend" in targets and not args.no_frontend_build:
        _ensure_frontend_built(base_dir)



    if not args.no_bump:

        exe_version = get_exe_version()

        pkg_version = get_version()

        print(f"版本: exe={exe_version}, 包={pkg_version}")



    for target in targets:

        exe_path = _build_target(target, base_dir, dist_dir)

        release_root = exe_path.parent

        stage_release_folder(

            release_root,

            project_root=base_dir,

            repo_root=base_dir,

            target=target,

        )

        print(f"  发布目录: {release_root}")





if __name__ == "__main__":

    main()

