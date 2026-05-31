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
    if getattr(sys, "frozen", False):
        _BASE = Path(sys._MEIPASS)
    else:
        _BASE = Path(__file__).resolve().parent.parent.parent

    for _p in [str(_BASE / "framework" / "src"), str(_BASE)]:
        if _p not in sys.path:
            sys.path.insert(0, _p)


_setup_paths()

import uvicorn

import web.backend.main


app = web.backend.main.app

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8180"))
    host = os.getenv("HOST", "127.0.0.1")
    print(f"\n  >>> 本地服务器已启动: http://{host}:{port} <<<")
    print("  关闭此窗口即可停止服务器\n")
    webbrowser.open(f"http://{host}:{port}")
    uvicorn.run(app, host=host, port=port, log_level="info")
