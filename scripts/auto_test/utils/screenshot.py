# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""
截图工具

支持全屏截图、窗口截图、区域截图。
"""

from __future__ import annotations

import time
from pathlib import Path

import mss
from PIL import Image


def take_screenshot(
    output_path: Path | str,
    *,
    region: tuple[int, int, int, int] | None = None,
    window_title: str | None = None,
) -> Path:
    """截图并保存到指定路径。

    Args:
        output_path: 输出文件路径
        region: 截图区域 (x, y, width, height)，None 表示全屏
        window_title: 窗口标题，用于截取特定窗口

    Returns:
        截图文件路径
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with mss.mss() as sct:
        if region:
            monitor = {
                "left": region[0],
                "top": region[1],
                "width": region[2],
                "height": region[3],
            }
        elif window_title:
            # 尝试通过窗口标题找到窗口
            try:
                import pygetwindow as gw

                windows = gw.getWindowsWithTitle(window_title)
                if windows:
                    win = windows[0]
                    monitor = {
                        "left": win.left,
                        "top": win.top,
                        "width": win.width,
                        "height": win.height,
                    }
                else:
                    # 找不到窗口，截全屏
                    monitor = sct.monitors[0]
            except Exception:
                monitor = sct.monitors[0]
        else:
            monitor = sct.monitors[0]

        screenshot = sct.grab(monitor)

    # 用 Pillow 保存（支持更多格式）
    img = Image.frombytes("RGB", screenshot.size, screenshot.rgb)
    img.save(str(output_path))

    return output_path


def take_window_screenshot(
    output_path: Path | str,
    window_title: str,
) -> Path:
    """截取指定窗口的截图。

    Args:
        output_path: 输出文件路径
        window_title: 窗口标题

    Returns:
        截图文件路径
    """
    return take_screenshot(output_path, window_title=window_title)


def take_fullscreen_screenshot(output_path: Path | str) -> Path:
    """截取全屏。

    Args:
        output_path: 输出文件路径

    Returns:
        截图文件路径
    """
    return take_screenshot(output_path)


def wait_and_screenshot(
    output_path: Path | str,
    window_title: str | None = None,
    delay: float = 1.0,
) -> Path:
    """等待后截图。

    Args:
        output_path: 输出文件路径
        window_title: 窗口标题
        delay: 等待时间（秒）

    Returns:
        截图文件路径
    """
    time.sleep(delay)
    if window_title:
        return take_window_screenshot(output_path, window_title)
    return take_fullscreen_screenshot(output_path)
