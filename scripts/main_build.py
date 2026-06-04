#!/usr/bin/env python3

# SPDX-License-Identifier: AGPL-3.0
"""

打包脚本 — 根入口

使用方法：

    python main_build.py                     # 同时打包启动器 + 工具箱
    python main_build.py --target launcher   # 仅打包启动器
    python main_build.py --target toolkit    # 仅打包工具箱

输出：

    dist/Game Calc Platform/     ← 游戏启动器（选择游戏 → 进入计算器）
    dist/开发者工具箱/           ← 开发者工具箱（数据/布局/图编辑等）

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

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS = _REPO_ROOT / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from _path_setup import ensure_root

ensure_root()

from calc_framework.logging import get_logger, setup_logging

_logger = get_logger(__name__)

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
    """读取整数环境变量，无效或为空时返回默认值。"""
    raw = os.getenv(name, "").strip()

    if not raw:
        return default

    try:
        value = int(raw)

    except ValueError:
        return default

    return value if value > 0 else default


def _terminate_process_tree(proc: subprocess.Popen[bytes]) -> None:
    """终止进程树（跨平台）。"""
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
    """在子进程中运行命令并监控超时。"""
    proc = subprocess.Popen(cmd, cwd=str(cwd))

    deadline = time.monotonic() + timeout_seconds

    while True:
        elapsed = time.monotonic()

        remaining = deadline - elapsed

        if remaining <= 0:
            _terminate_process_tree(proc)

            raise TimeoutError(f"打包超时 {timeout_seconds}s，已终止进程树 (PID={proc.pid})")

        ret = proc.poll()

        if ret is not None:
            return subprocess.CompletedProcess(cmd, ret)

        if int(elapsed) % heartbeat_seconds == 0:
            _logger.info("看门狗 — 运行中… (%ds 剩余)", int(remaining))

        time.sleep(1)


def _build_target(
    target: BuildTarget,
    base_dir: Path,
    dist_dir: Path,
    *,
    extra_args: list[str] | None = None,
) -> Path:
    """使用 PyInstaller 打包单个构建目标。"""
    app_name = target_app_name(target)

    release_root = release_dir_from_dist(dist_dir, target=target)

    entry = target_entry(target)

    _logger.info("=" * 60)
    _logger.info("  [%s] %s", target, app_name)
    _logger.info("  入口: %s", entry)
    _logger.info("  输出: %s", release_root)
    _logger.info("=" * 60)

    work_dir = tempfile.mkdtemp(prefix=f"build_{target}_", dir=base_dir)

    spec_dir = tempfile.mkdtemp(prefix=f"spec_{target}_", dir=base_dir)

    # 用临时 dist 目录避免 Windows Defender 锁定问题
    tmp_dist = Path(tempfile.mkdtemp(prefix=f"dist_{target}_", dir=base_dir))

    cmd: list[str] = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--onefile",
        "--windowed",
        f"--name={app_name}",
        f"--distpath={tmp_dist}",
        f"--workpath={work_dir}",
        f"--specpath={spec_dir}",
        "--noconfirm",
        "--clean",
    ]

    if extra_args:
        cmd.extend(extra_args)

    donation_data = f"{base_dir / 'resources' / 'donation'};resources/donation"
    cmd.extend(["--add-data", donation_data])

    # 目标特定配置
    if target == "toolkit":
        cmd.extend(
            [
                "--paths",
                str(base_dir / "framework" / "src"),
                "--paths",
                str(base_dir),
                "--paths",
                str(base_dir / "scripts"),
                "--paths",
                str(base_dir / "tools"),
                "--add-data",
                f"{base_dir / 'utils'};utils",
            ]
        )
    else:
        # launcher: 打包框架 + 所有游戏 + 所有工具 + 数据 + Web 后端
        cmd.extend(
            [
                "--paths",
                str(base_dir / "framework" / "src"),
                "--paths",
                str(base_dir / "games"),
                "--paths",
                str(base_dir / "games" / "endfield"),
                "--paths",
                str(base_dir / "games" / "arknights"),
                "--paths",
                str(base_dir / "tools"),
                "--paths",
                str(base_dir / "scripts"),
                "--paths",
                str(base_dir / "web" / "backend"),
                "--add-data",
                f"{base_dir / 'games' / 'endfield' / 'data'};games/endfield/data",
                "--add-data",
                f"{base_dir / 'games' / 'endfield' / 'data_loading'};games/endfield/data_loading",
                "--add-data",
                f"{base_dir / 'games' / 'endfield' / 'gui'};games/endfield/gui",
                "--add-data",
                f"{base_dir / 'games' / 'endfield' / 'calc'};games/endfield/calc",
                "--add-data",
                f"{base_dir / 'tools' / 'arknights_scout' / 'output' / 'parsed'};tools/arknights_scout/output/parsed",
                "--add-data",
                f"{base_dir / 'framework' / 'adapters'};framework/adapters",
                "--add-data",
                f"{base_dir / 'utils'};utils",
                "--add-data",
                f"{base_dir / 'web' / 'backend'};web/backend",
                "--add-data",
                f"{base_dir / 'web' / 'frontend' / 'dist'};web/frontend/dist",
                "--hidden-import",
                "uvicorn",
                "--hidden-import",
                "uvicorn.logging",
                "--hidden-import",
                "uvicorn.loops",
                "--hidden-import",
                "uvicorn.loops.auto",
                "--hidden-import",
                "uvicorn.protocols",
                "--hidden-import",
                "uvicorn.protocols.http",
                "--hidden-import",
                "uvicorn.protocols.http.auto",
                "--hidden-import",
                "uvicorn.protocols.websocket",
                "--hidden-import",
                "uvicorn.protocols.websocket.auto",
                "--hidden-import",
                "uvicorn.middleware",
                "--hidden-import",
                "uvicorn.middleware.asgi2",
                "--hidden-import",
                "uvicorn.middleware.wsgi",
                "--hidden-import",
                "uvicorn.supervisors",
                "--hidden-import",
                "uvicorn.supervisors.basereload",
                "--hidden-import",
                "uvicorn.supervisors.multiprocess",
                "--hidden-import",
                "uvicorn.supervisors.statreload",
                "--hidden-import",
                "uvicorn.supervisors.watchgodreload",
            ]
        )

    cmd.append(entry)

    timeout = _read_int_env("ENDFIELD_BUILD_TIMEOUT_SECONDS", DEFAULT_BUILD_TIMEOUT_SECONDS)

    heartbeat = _read_int_env("ENDFIELD_BUILD_HEARTBEAT_SECONDS", DEFAULT_HEARTBEAT_SECONDS)

    result = _run_with_watchdog(
        cmd,
        cwd=base_dir,
        timeout_seconds=timeout,
        heartbeat_seconds=heartbeat,
    )

    shutil.rmtree(work_dir, ignore_errors=True)

    shutil.rmtree(spec_dir, ignore_errors=True)

    if result.returncode != 0:
        shutil.rmtree(tmp_dist, ignore_errors=True)
        raise RuntimeError(f"PyInstaller 打包 [{target}] 失败 (exit={result.returncode})")

    # 从临时 dist 目录复制到正式发布目录
    tmp_exe = tmp_dist / f"{app_name}.exe"
    if not tmp_exe.exists():
        shutil.rmtree(tmp_dist, ignore_errors=True)
        raise FileNotFoundError(f"打包成功但未找到 exe: {tmp_exe}")

    release_root.mkdir(parents=True, exist_ok=True)
    dest_exe = release_root / f"{app_name}.exe"
    shutil.copy2(tmp_exe, dest_exe)
    shutil.rmtree(tmp_dist, ignore_errors=True)

    _logger.info("  → 已生成: %s (%.1f MB)", dest_exe, dest_exe.stat().st_size / 1024 / 1024)

    return dest_exe


def main() -> None:
    """CLI 入口。打包统一启动器和开发者工具箱。"""
    apply_platform_win32_patch()
    setup_logging(level="INFO")

    parser = argparse.ArgumentParser(description="Game Calc Platform — 打包脚本")

    parser.add_argument("--no-bump", action="store_true", help="不通过 please_read_me 带版本号打包")
    parser.add_argument(
        "--target",
        choices=["launcher", "toolkit", "all"],
        default="all",
        help="打包目标：launcher（启动器）/ toolkit（工具箱）/ all（全部）",
    )
    args = parser.parse_args()

    base_dir = _REPO_ROOT
    dist_dir = base_dir / "dist"
    dist_dir.mkdir(parents=True, exist_ok=True)

    if not args.no_bump:
        exe_version = get_exe_version()
        pkg_version = get_version()
        _logger.info("版本: exe=%s, 包=%s", exe_version, pkg_version)

    if args.target == "all":
        targets: list[BuildTarget] = ["launcher", "toolkit"]
    else:
        targets = [args.target]  # type: ignore[list-item]

    for target in targets:
        exe_path = _build_target(target, base_dir, dist_dir)

        release_root = exe_path.parent

        stage_release_folder(
            release_root,
            project_root=base_dir,
            repo_root=base_dir,
            target=target,
        )

        _logger.info("  发布目录: %s", release_root)


if __name__ == "__main__":
    main()
