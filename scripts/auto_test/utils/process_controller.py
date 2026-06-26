# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""
进程控制器

通过 Windows API 直接向进程的 stdin 写入，
无需焦点切换，更稳定可靠。
"""

from __future__ import annotations

import ctypes
import logging
import time

import win32con
import win32gui
import win32process

logger = logging.getLogger(__name__)

# Windows API 常量
INPUT_KEYBOARD = 1
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_UNICODE = 0x0004


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", ctypes.c_ushort),
        ("wScan", ctypes.c_ushort),
        ("dwFlags", ctypes.c_ulong),
        ("time", ctypes.c_ulong),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]


class INPUT(ctypes.Structure):
    class _InputUnion(ctypes.Union):
        _fields_ = [("ki", KEYBDINPUT)]

    _fields_ = [
        ("type", ctypes.c_ulong),
        ("union", _InputUnion),
    ]


def send_char_to_window(hwnd: int, char: str) -> bool:
    """向指定窗口发送单个字符。

    使用 PostMessage 直接发送，无需焦点。

    Args:
        hwnd: 窗口句柄
        char: 要发送的字符

    Returns:
        是否成功
    """
    try:
        # 发送 WM_CHAR 消息
        for c in char:
            win32gui.PostMessage(hwnd, win32con.WM_CHAR, ord(c), 0)
            time.sleep(0.01)
        return True
    except Exception as e:
        logger.error("发送字符失败: %s", e)
        return False


def send_enter_to_window(hwnd: int) -> bool:
    """向指定窗口发送回车键。

    Args:
        hwnd: 窗口句柄

    Returns:
        是否成功
    """
    try:
        # 发送 ENTER 键的 WM_KEYDOWN 和 WM_KEYUP
        win32gui.PostMessage(hwnd, win32con.WM_KEYDOWN, win32con.VK_RETURN, 0)
        time.sleep(0.05)
        win32gui.PostMessage(hwnd, win32con.WM_KEYUP, win32con.VK_RETURN, 0)
        return True
    except Exception as e:
        logger.error("发送回车失败: %s", e)
        return False


def send_tab_to_window(hwnd: int) -> bool:
    """向指定窗口发送 Tab 键。

    Args:
        hwnd: 窗口句柄

    Returns:
        是否成功
    """
    try:
        win32gui.PostMessage(hwnd, win32con.WM_KEYDOWN, win32con.VK_TAB, 0)
        time.sleep(0.05)
        win32gui.PostMessage(hwnd, win32con.WM_KEYUP, win32con.VK_TAB, 0)
        return True
    except Exception as e:
        logger.error("发送 Tab 失败: %s", e)
        return False


def send_string_to_window(hwnd: int, text: str) -> bool:
    """向指定窗口发送字符串。

    Args:
        hwnd: 窗口句柄
        text: 要发送的字符串

    Returns:
        是否成功
    """
    try:
        for char in text:
            if char == "\n":
                send_enter_to_window(hwnd)
            elif char == "\t":
                send_tab_to_window(hwnd)
            else:
                send_char_to_window(hwnd, char)
            time.sleep(0.02)
        return True
    except Exception as e:
        logger.error("发送字符串失败: %s", e)
        return False


def find_window_by_title(title_keyword: str) -> int | None:
    """通过标题关键词查找窗口。

    Args:
        title_keyword: 标题关键词

    Returns:
        窗口句柄，未找到返回 None
    """
    result = []

    def callback(hwnd, _):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if title_keyword.lower() in title.lower():
                result.append(hwnd)
        return True

    win32gui.EnumWindows(callback, None)

    if result:
        return result[0]
    return None


def get_window_pid(hwnd: int) -> int:
    """获取窗口的进程 ID。

    Args:
        hwnd: 窗口句柄

    Returns:
        进程 ID
    """
    _, pid = win32process.GetWindowThreadProcessId(hwnd)
    return pid


class ProcessController:
    """进程控制器。

    通过 Windows API 直接向进程的 stdin 写入，
    无需焦点切换。

    用法：
        ctrl = ProcessController()
        ctrl.connect("Claude Code")
        ctrl.send_command("读 .trae/plans/task.md")
        ctrl.press_enter()
    """

    def __init__(self) -> None:
        self._hwnd: int | None = None
        self._window_title: str = ""

    def connect(self, window_title: str) -> bool:
        """连接到指定窗口。

        Args:
            window_title: 窗口标题关键词

        Returns:
            是否连接成功
        """
        self._window_title = window_title
        self._hwnd = find_window_by_title(window_title)

        if self._hwnd:
            title = win32gui.GetWindowText(self._hwnd)
            logger.info("已连接到窗口: %s (hwnd=%d)", title, self._hwnd)
            return True

        logger.error("未找到窗口: %s", window_title)
        return False

    def list_windows(self) -> list[str]:
        """列出所有可见窗口。

        Returns:
            窗口标题列表
        """
        windows = []

        def callback(hwnd, _):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if title.strip():
                    windows.append(title)
            return True

        win32gui.EnumWindows(callback, None)
        return windows

    def send_command(
        self,
        command: str,
        *,
        press_enter: bool = True,
        wait: float = 0.5,
    ) -> bool:
        """发送命令到窗口。

        Args:
            command: 命令文本
            press_enter: 是否按回车
            wait: 发送后等待时间

        Returns:
            是否成功
        """
        if not self._hwnd:
            logger.error("未连接到窗口")
            return False

        # 发送字符串
        if not send_string_to_window(self._hwnd, command):
            return False

        # 按回车
        if press_enter:
            time.sleep(0.2)
            if not send_enter_to_window(self._hwnd):
                return False

        time.sleep(wait)
        return True

    def press_enter(self, *, count: int = 1) -> bool:
        """按回车键。

        Args:
            count: 按几次

        Returns:
            是否成功
        """
        if not self._hwnd:
            return False

        for _ in range(count):
            if not send_enter_to_window(self._hwnd):
                return False
            time.sleep(0.1)

        return True

    def press_tab(self, *, count: int = 1) -> bool:
        """按 Tab 键。

        Args:
            count: 按几次

        Returns:
            是否成功
        """
        if not self._hwnd:
            return False

        for _ in range(count):
            if not send_tab_to_window(self._hwnd):
                return False
            time.sleep(0.1)

        return True

    def type_text(self, text: str) -> bool:
        """输入文本（不按回车）。

        Args:
            text: 文本内容

        Returns:
            是否成功
        """
        return self.send_command(text, press_enter=False, wait=0.1)

    @property
    def is_connected(self) -> bool:
        """是否已连接。"""
        return self._hwnd is not None

    @property
    def window_title(self) -> str:
        """窗口标题。"""
        if self._hwnd:
            return win32gui.GetWindowText(self._hwnd)
        return ""
