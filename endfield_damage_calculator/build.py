#!/usr/bin/env python3
"""
打包脚本 — 支持双目标构建

使用方法：
    python build.py                     # 默认构建计算器（终末地伤害计算器）
    python build.py --target calculator # 同上
    python build.py --target designer   # 构建设计器（终末地数据设计器）

输出：
  dist/终末地伤害计算器/  ── 伤害计算器（默认）
  dist/终末地数据设计器/  ── 数据设计器（--target designer）

看门狗（可选环境变量）：
  ENDFIELD_BUILD_TIMEOUT_SECONDS  默认 1200（20 分钟），超时自动终止 PyInstaller
  ENDFIELD_BUILD_HEARTBEAT_SECONDS  默认 15，打印进度心跳
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

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
    args: list[str],
    *,
    cwd: Path,
    timeout_seconds: int,
    heartbeat_seconds: int,
) -> None:
    proc = subprocess.Popen(args, cwd=cwd)
    start = time.monotonic()
    last_heartbeat = start
    while True:
        rc = proc.poll()
        now = time.monotonic()
        elapsed = int(now - start)
        if rc is not None:
            if rc != 0:
                raise subprocess.CalledProcessError(rc, args)
            return
        if now - last_heartbeat >= heartbeat_seconds:
            print(f"[build] 仍在执行中... 已用时 {elapsed}s", flush=True)
            last_heartbeat = now
        if elapsed >= timeout_seconds:
            _terminate_process_tree(proc)
            raise TimeoutError(
                f"PyInstaller 超时（>{timeout_seconds}s）并已终止。"
                "可设置环境变量 ENDFIELD_BUILD_TIMEOUT_SECONDS 延长超时。"
            )
        time.sleep(1)


def check_build_dependencies(target: BuildTarget) -> bool:
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

    if target == "calculator":
        from utils.optional_deps import is_matplotlib_available

        if not is_matplotlib_available():
            print("缺少运行时依赖 matplotlib。请在 [包] 目录执行：")
            print("  pip install -e .")
            return False
        print("matplotlib 已安装（将打入发布包）", flush=True)
    return True


def build_release(target: BuildTarget) -> Path:
    project_root = Path(__file__).parent
    repo_root = project_root.parent
    timeout_seconds = _read_int_env("ENDFIELD_BUILD_TIMEOUT_SECONDS", DEFAULT_BUILD_TIMEOUT_SECONDS)
    heartbeat_seconds = _read_int_env("ENDFIELD_BUILD_HEARTBEAT_SECONDS", DEFAULT_HEARTBEAT_SECONDS)

    app_name = target_app_name(target)
    entry = target_entry(target)

    if target == "calculator":
        excludes = [
            "tests",
            "scripts",
            "release_bundle",
            "designer",
            "add_character",
            "add_weapon",
            "test_",
        ]
        collect_args = [
            "--collect-all",
            "matplotlib",
            "--hidden-import",
            "matplotlib.backends.backend_tkagg",
        ]
    else:
        excludes = [
            "tests",
            "scripts",
            "release_bundle",
            "gui_design",
            "legal",
            "search_output",
            "add_character",
            "add_weapon",
            "test_",
        ]
        collect_args = []

    exclude_args: list[str] = []
    for item in excludes:
        exclude_args.extend(["--exclude-module", item])

    args = [
        sys.executable,
        "-m",
        "release_bundle.pyinstaller_entry",
        "--onedir",
        "--windowed",
        "--noconfirm",
        f"--name={app_name}",
        "--clean",
        *collect_args,
        *exclude_args,
        str(project_root / entry),
    ]

    print("=" * 60)
    print(f"开始打包 {app_name}（onedir，游戏数据不写入 exe）...")
    print("（PyInstaller 分析依赖可能需数分钟，请耐心等待下方日志）")
    print(
        f"（已启用看门狗：超时 {timeout_seconds}s，心跳 {heartbeat_seconds}s）",
        flush=True,
    )
    print("=" * 60)

    _run_with_watchdog(
        args,
        cwd=project_root,
        timeout_seconds=timeout_seconds,
        heartbeat_seconds=heartbeat_seconds,
    )

    dist_dir = project_root / "dist"
    release_root = release_dir_from_dist(dist_dir, target=target)
    exe_path = release_root / f"{app_name}.exe"
    if not exe_path.is_file():
        raise FileNotFoundError(f"未找到打包产物: {exe_path}")

    stage_release_folder(
        release_root,
        project_root=project_root,
        repo_root=repo_root,
        target=target,
    )
    return release_root


def main() -> None:
    apply_platform_win32_patch()

    parser = argparse.ArgumentParser(description="终末地双目标打包工具")
    parser.add_argument(
        "--target",
        choices=["calculator", "designer"],
        default="calculator",
        help="打包目标：calculator（计算器，默认）| designer（设计器）",
    )
    args = parser.parse_args()
    target: BuildTarget = args.target

    app_name = target_app_name(target)
    print("=" * 60)
    print(f"{app_name} — 打包工具（源码包 v{get_version()}，目标 EXE v{get_exe_version()}）")
    print("=" * 60)

    if not check_build_dependencies(target):
        sys.exit(1)

    try:
        release_root = build_release(target)
    except (subprocess.CalledProcessError, FileNotFoundError, TimeoutError) as exc:
        print(f"\n打包失败: {exc}")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("打包完成！")
    print(f"  EXE 版本（窗口标题）: v{get_exe_version()}")
    print(f"  源码包版本:         v{get_version()}")
    print(f"发布文件夹: {release_root}")
    print("请将整个文件夹分发给用户（勿只发 exe，否则无法加载角色/武器数据）。")
    print("=" * 60)


if __name__ == "__main__":
    main()
