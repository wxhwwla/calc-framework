# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""
PyInstaller 打包入口 — 本地后端服务器

双击 exe 即可启动完整的 Web 后端（含全量搜索），
浏览器自动打开 http://localhost:8180。

本文件仅在 PyInstaller 打包后的 exe 中使用。
"""

from __future__ import annotations

import os
import sys
import webbrowser
from pathlib import Path


def _setup_paths() -> None:
    """配置 PyInstaller 打包环境下的 Python 模块搜索路径。"""
    if getattr(sys, "frozen", False):
        _BASE = Path(sys._MEIPASS)
    else:
        _BASE = Path(__file__).resolve().parent.parent.parent

    for _p in [
        str(_BASE / "_internal" / "web" / "backend"),
        str(_BASE / "framework" / "src"),
        str(_BASE),
    ]:
        if _p not in sys.path and Path(_p).is_dir():
            sys.path.insert(0, str(_p))


_setup_paths()

import uvicorn

from web.backend.main import app

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8180"))
    host = os.getenv("HOST", "127.0.0.1")
    print(f"\n  >>> 本地服务器已启动: http://{host}:{port} <<<")
    print("  关闭此窗口即可停止服务器\n")
    webbrowser.open(f"http://{host}:{port}")
    uvicorn.run(app, host=host, port=port, log_level="info")
