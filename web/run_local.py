# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""
终末地伤害计算器 — 本地后端启动脚本

在本地启动完整的 Web 后端（含搜索 API）， Web 页面通过浏览器访问。
全量搜索使用本地 GPU/CPU 计算，速度与 Desktop GUI 一致。

使用方法:
  python web/run_local.py             默认模式（端口 8180）
  python web/run_local.py --port 8000 指定端口
  python web/run_local.py --no-build  跳过前端构建检查
  python web/run_local.py --workers 8 指定搜索线程数

访问:
  http://localhost:8180  — 完整 Web 界面（含全量搜索）
  http://localhost:8180/api/docs  — API 文档（Swagger）
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent
_FRONTEND_DIR = _REPO_ROOT / "frontend"
_DIST_DIR = _FRONTEND_DIR / "dist"


def _run_npm(args: list[str], cwd: Path) -> None:
    cmd = [*("npm.cmd" if sys.platform == "win32" else "npm"), *args]
    print(f"  $ {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, encoding="utf-8", errors="replace")
    if result.returncode != 0:
        print(result.stdout[-2000:] if len(result.stdout) > 2000 else result.stdout)
        print(result.stderr[-2000:] if len(result.stderr) > 2000 else result.stderr)
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="终末地伤害计算器 — 本地后端启动",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--port", type=int, default=8180, help="端口号（默认 8180）")
    parser.add_argument("--no-build", action="store_true", help="跳过前端构建检查")
    parser.add_argument("--workers", type=int, default=0, help="搜索线程数（默认 0 = 自动使用所有逻辑核）")
    parser.add_argument("--host", default="127.0.0.1", help="监听地址（默认 127.0.0.1）")
    args = parser.parse_args()

    # 1. 检查 / 构建前端
    if not args.no_build:
        if not _DIST_DIR.exists() or not list(_DIST_DIR.iterdir()):
            print("[1/3] 构建前端...")
            _run_npm(["install"], _FRONTEND_DIR)
            _run_npm(["run", "build"], _FRONTEND_DIR)
            print("  [OK] 构建完成")
        else:
            print("[1/3] 前端已构建，跳过")
    else:
        print("[1/3] 跳过构建检查")

    # 2. 设置环境变量
    env = os.environ.copy()
    env.setdefault("PYTHONUNBUFFERED", "1")
    if args.workers > 0:
        env["SEARCH_MAX_WORKERS"] = str(args.workers)

    # 3. 启动后端
    print(f"\n[2/3] 启动本地后端 → http://{args.host}:{args.port}")
    backend_dir = _REPO_ROOT / "backend"
    uvicorn_cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "main:app",
        "--host",
        args.host,
        "--port",
        str(args.port),
        "--reload",
    ]

    print(f"  $ {' '.join(uvicorn_cmd)}")
    print("\n[3/3] 在浏览器中打开...")
    time.sleep(1)
    webbrowser.open(f"http://{args.host}:{args.port}")

    subprocess.run(uvicorn_cmd, cwd=str(backend_dir), env=env)


if __name__ == "__main__":
    main()
