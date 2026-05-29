#!/usr/bin/env python3
"""在规避 WMI 卡死后启动 PyInstaller（供 ``build.py`` 子进程调用）。"""

from __future__ import annotations

from utils.platform_win32_patch import apply_platform_win32_patch

apply_platform_win32_patch()

from PyInstaller.__main__ import run

if __name__ == "__main__":
    run()
