# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""
终端控制器

用于向另一个 PowerShell 窗口发送按键和命令。
使用 pywinauto 的 UIA 后端识别和操作终端窗口。
"""

from __future__ import annotations

import logging
import time

from pywinauto import Desktop
from pywinauto.keyboard import send_keys

logger = logging.getLogger(__name__)


class TerminalController:
    """终端控制器。

    用于向另一个 PowerShell/Claude Code 窗口发送按键和命令。

    用法：
        ctrl = TerminalController()
        ctrl.connect("Claude Code")  # 连接到窗口
        ctrl.send_command("读 .trae/plans/task.md 并执行")  # 发送命令
        ctrl.press_enter()  # 按回车
    """

    def __init__(self) -> None:
        self._window = None
        self._window_title: str = ""

    def connect(
        self,
        window_title: str,
        *,
        timeout: float = 10.0,
    ) -> bool:
        """连接到指定窗口。

        Args:
            window_title: 窗口标题（支持部分匹配）
            timeout: 超时时间

        Returns:
            是否连接成功
        """
        self._window_title = window_title
        start = time.time()

        while time.time() - start < timeout:
            try:
                desktop = Desktop(backend="uia")
                windows = desktop.windows()

                for win in windows:
                    if window_title.lower() in win.window_text().lower():
                        self._window = win
                        logger.info("已连接到窗口: %s", win.window_text())
                        return True
            except Exception as e:
                logger.debug("查找窗口失败: %s", e)

            time.sleep(1)

        logger.error("未找到窗口: %s", window_title)
        return False

    def list_windows(self) -> list[str]:
        """列出所有可见窗口。

        Returns:
            窗口标题列表
        """
        try:
            desktop = Desktop(backend="uia")
            return [w.window_text() for w in desktop.windows() if w.window_text()]
        except Exception:
            return []

    def focus(self) -> bool:
        """聚焦窗口。

        Returns:
            是否成功
        """
        if not self._window:
            return False

        try:
            self._window.set_focus()
            time.sleep(0.3)
            return True
        except Exception as e:
            logger.error("聚焦失败: %s", e)
            return False

    def send_keys(
        self,
        keys: str,
        *,
        pause: float = 0.05,
    ) -> bool:
        """发送按键。

        Args:
            keys: 按键内容（pywinauto 格式）
            pause: 按键间隔

        Returns:
            是否成功
        """
        if not self._window:
            return False

        try:
            self.focus()
            send_keys(keys, pause=pause)
            return True
        except Exception as e:
            logger.error("发送按键失败: %s", e)
            return False

    def send_command(
        self,
        command: str,
        *,
        press_enter: bool = True,
        wait: float = 0.5,
    ) -> bool:
        """发送命令到终端。

        Args:
            command: 命令文本
            press_enter: 是否按回车
            wait: 发送后等待时间

        Returns:
            是否成功
        """
        if not self._window:
            return False

        try:
            self.focus()
            time.sleep(0.2)

            # 输入命令
            send_keys(command, pause=0.02)
            time.sleep(0.2)

            # 按回车
            if press_enter:
                send_keys("{ENTER}")

            time.sleep(wait)
            return True
        except Exception as e:
            logger.error("发送命令失败: %s", e)
            return False

    def press_enter(self, *, count: int = 1) -> bool:
        """按回车键。

        Args:
            count: 按几次

        Returns:
            是否成功
        """
        if not self._window:
            return False

        try:
            self.focus()
            for _ in range(count):
                send_keys("{ENTER}")
                time.sleep(0.1)
            return True
        except Exception as e:
            logger.error("按回车失败: %s", e)
            return False

    def press_tab(self, *, count: int = 1) -> bool:
        """按 Tab 键。

        Args:
            count: 按几次

        Returns:
            是否成功
        """
        if not self._window:
            return False

        try:
            self.focus()
            for _ in range(count):
                send_keys("{TAB}")
                time.sleep(0.1)
            return True
        except Exception as e:
            logger.error("按 Tab 失败: %s", e)
            return False

    def type_text(self, text: str) -> bool:
        """输入文本（不按回车）。

        Args:
            text: 文本内容

        Returns:
            是否成功
        """
        return self.send_command(text, press_enter=False, wait=0.1)

    def clear_line(self) -> bool:
        """清除当前行。

        Returns:
            是否成功
        """
        return self.send_keys("{HOME}+{END}{DELETE}")
