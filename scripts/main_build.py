#!/usr/bin/env python3

# SPDX-License-Identifier: AGPL-3.0
"""

打包脚本 — 根入口



使用方法：

    python main_build.py                     # 默认打包全部

    python main_build.py --target calculator # 仅打包计算器

    python main_build.py --target designer   # 仅打包数据设计器

    python main_build.py --target pack-designer   # 仅打包配置包设计器

    python main_build.py --target arknights       # 仅打包明日方舟计算器

    python main_build.py --target local-backend   # 仅打包本地搜索服务器（会先构建 Web 前端）



输出（各目标独立目录，可 `--target all` 一次顺序打齐）：

  dist/终末地伤害计算器/      ── 伤害计算器

  dist/数据设计器/            ── 数据设计器

  dist/配置包设计器/          ── 配置包设计器

  dist/明日方舟伤害计算器/    ── 明日方舟计算器

  dist/终末地本地搜索服务器/  ── Web 全量搜索本地后端

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

    cmd: list[str] = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--onefile",
        "--console",
        f"--name={app_name}",
        f"--distpath={release_root}",
        f"--workpath={work_dir}",
        f"--specpath={spec_dir}",
        "--noconfirm",
        "--clean",
    ]

    if extra_args:
        cmd.extend(extra_args)

    donation_data = f"{base_dir / 'resources' / 'donation'};resources/donation"
    cmd.extend(["--add-data", donation_data])

    # 启动器模式：打包框架 + 所有游戏 + 所有工具 + 数据
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
            # 内嵌所有游戏数据
            "--add-data",
            f"{base_dir / 'games' / 'endfield' / 'data'};games/endfield/data",
            "--add-data",
            f"{base_dir / 'games' / 'endfield' / 'data_loading'};games/endfield/data_loading",
            "--add-data",
            f"{base_dir / 'games' / 'endfield' / 'gui'};games/endfield/gui",
            "--add-data",
            f"{base_dir / 'games' / 'endfield' / 'calc'};games/endfield/calc",
            # 明日方舟解析数据
            "--add-data",
            f"{base_dir / 'tools' / 'arknights_scout' / 'output' / 'parsed'};tools/arknights_scout/output/parsed",
            # 框架适配器
            "--add-data",
            f"{base_dir / 'framework' / 'adapters'};framework/adapters",
            # 工具包
            "--add-data",
            f"{base_dir / 'utils'};utils",
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
        raise RuntimeError(f"PyInstaller 打包 [{target}] 失败 (exit={result.returncode})")

    exe_path = release_root / f"{app_name}.exe"

    if not exe_path.exists():
        raise FileNotFoundError(f"打包成功但未找到 exe: {exe_path}")

    _logger.info("  → 已生成: %s (%.1f MB)", exe_path, exe_path.stat().st_size / 1024 / 1024)

    return exe_path


def main() -> None:
    """CLI 入口。打包统一启动器。"""
    apply_platform_win32_patch()
    setup_logging(level="INFO")

    parser = argparse.ArgumentParser(description="Game Calc Platform — 打包脚本")

    parser.add_argument("--no-bump", action="store_true", help="不通过 please_read_me 带版本号打包")
    args = parser.parse_args()

    base_dir = _REPO_ROOT
    dist_dir = base_dir / "dist"
    dist_dir.mkdir(parents=True, exist_ok=True)

    if not args.no_bump:
        exe_version = get_exe_version()
        pkg_version = get_version()
        _logger.info("版本: exe=%s, 包=%s", exe_version, pkg_version)

    target: BuildTarget = "launcher"
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
