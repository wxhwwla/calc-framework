# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""
Qt 控件检查器

使用 pywinauto 的 UIA 后端检查和操作 Qt/PySide6 控件。
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any

from pywinauto import Application
from pywinauto.controls.uiawrapper import UIAWrapper

logger = logging.getLogger(__name__)


@dataclass
class ControlInfo:
    """控件信息。"""

    control_type: str
    class_name: str
    automation_id: str
    name: str
    text: str
    rect: tuple[int, int, int, int]  # (left, top, right, bottom)
    is_enabled: bool
    is_visible: bool
    children: list[ControlInfo] = field(default_factory=list)


class QtInspector:
    """Qt 应用检查器。

    使用 pywinauto 的 UIA 后端连接到 Qt 应用，
    提供控件查找、点击、输入、截图等操作。

    用法：
        inspector = QtInspector()
        inspector.connect("终末地伤害计算器")

        # 查找控件
        btn = inspector.find_control(name="确认选择")
        if btn:
            inspector.click(btn)

        # 截图
        inspector.screenshot("output.png")

        # 获取所有控件树
        tree = inspector.get_control_tree()
    """

    def __init__(self) -> None:
        self._app: Application | None = None
        self._main_window: UIAWrapper | None = None
        self._window_title: str = ""

    def connect(
        self,
        window_title: str,
        *,
        timeout: float = 30.0,
        class_name: str | None = None,
    ) -> bool:
        """连接到指定窗口。

        Args:
            window_title: 窗口标题（支持部分匹配）
            timeout: 超时时间（秒）
            class_name: 窗口类名（可选，用于精确匹配）

        Returns:
            是否连接成功
        """
        self._window_title = window_title
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                # 使用 UIA 后端连接
                self._app = Application(backend="uia").connect(
                    title_re=f".*{window_title}.*",
                    timeout=5,
                )
                self._main_window = self._app.window(title_re=f".*{window_title}.*")

                if self._main_window.exists():
                    logger.info("已连接到窗口: %s", window_title)
                    return True
            except Exception as e:
                logger.debug("等待窗口出现... (%s)", e)
                time.sleep(1)

        logger.error("超时：未找到窗口 '%s'", window_title)
        return False

    def connect_by_pid(self, pid: int) -> bool:
        """通过进程 ID 连接。

        Args:
            pid: 进程 ID

        Returns:
            是否连接成功
        """
        try:
            self._app = Application(backend="uia").connect(process=pid)
            self._main_window = self._app.top_window()
            logger.info("已连接到进程 PID=%d", pid)
            return True
        except Exception as e:
            logger.error("连接进程失败: %s", e)
            return False

    @property
    def main_window(self) -> UIAWrapper | None:
        """主窗口。"""
        return self._main_window

    def find_control(
        self,
        *,
        control_type: str | None = None,
        name: str | None = None,
        automation_id: str | None = None,
        class_name: str | None = None,
        text: str | None = None,
        found_index: int = 0,
    ) -> UIAWrapper | None:
        """查找控件。

        Args:
            control_type: 控件类型（Button, Edit, ComboBox 等）
            name: 控件名称
            automation_id: 自动化 ID
            class_name: 类名
            text: 文本内容
            found_index: 匹配多个时取第几个

        Returns:
            找到的控件，未找到返回 None
        """
        if not self._main_window:
            logger.error("未连接到窗口")
            return None

        criteria: dict[str, Any] = {}
        if control_type:
            criteria["control_type"] = control_type
        if name:
            criteria["title"] = name
        if automation_id:
            criteria["auto_id"] = automation_id
        if class_name:
            criteria["class_name"] = class_name

        try:
            if not criteria:
                return None

            controls = self._main_window.descendants(**criteria)
            if controls and found_index < len(controls):
                return controls[found_index]
            return None
        except Exception as e:
            logger.debug("查找控件失败: %s", e)
            return None

    def find_controls(
        self,
        *,
        control_type: str | None = None,
        name: str | None = None,
        class_name: str | None = None,
    ) -> list[UIAWrapper]:
        """查找所有匹配的控件。

        Args:
            control_type: 控件类型
            name: 控件名称
            class_name: 类名

        Returns:
            匹配的控件列表
        """
        if not self._main_window:
            return []

        criteria: dict[str, Any] = {}
        if control_type:
            criteria["control_type"] = control_type
        if name:
            criteria["title"] = name
        if class_name:
            criteria["class_name"] = class_name

        try:
            return self._main_window.descendants(**criteria)
        except Exception:
            return []

    def click(
        self,
        control: UIAWrapper,
        *,
        wait: float = 0.5,
    ) -> bool:
        """点击控件。

        Args:
            control: 目标控件
            wait: 点击后等待时间（秒）

        Returns:
            是否成功
        """
        try:
            control.click_input()
            time.sleep(wait)
            return True
        except Exception as e:
            logger.error("点击失败: %s", e)
            return False

    def click_by_name(
        self,
        name: str,
        *,
        control_type: str | None = None,
        wait: float = 0.5,
    ) -> bool:
        """通过名称点击控件。

        Args:
            name: 控件名称
            control_type: 控件类型
            wait: 点击后等待时间

        Returns:
            是否成功
        """
        control = self.find_control(name=name, control_type=control_type)
        if control:
            return self.click(control, wait=wait)
        logger.warning("未找到控件: %s", name)
        return False

    def type_text(
        self,
        control: UIAWrapper,
        text: str,
        *,
        clear_first: bool = True,
        wait: float = 0.5,
    ) -> bool:
        """在控件中输入文本。

        Args:
            control: 目标控件
            text: 要输入的文本
            clear_first: 是否先清空
            wait: 输入后等待时间

        Returns:
            是否成功
        """
        try:
            if clear_first:
                control.set_edit_text("")
            control.type_keys(text, with_spaces=True)
            time.sleep(wait)
            return True
        except Exception as e:
            logger.error("输入失败: %s", e)
            return False

    def select_combobox(
        self,
        combobox: UIAWrapper,
        item_text: str,
        *,
        wait: float = 0.5,
    ) -> bool:
        """选择下拉框选项。

        Args:
            combobox: 下拉框控件
            item_text: 选项文本
            wait: 选择后等待时间

        Returns:
            是否成功
        """
        try:
            combobox.select(item_text)  # type: ignore[reportCallIssue]
            time.sleep(wait)
            return True
        except Exception as e:
            logger.warning("下拉框选择失败，尝试点击方式: %s", e)
            try:
                combobox.click_input()
                time.sleep(0.3)
                # 查找弹出的列表项
                item = self.find_control(name=item_text)
                if item:
                    item.click_input()
                    time.sleep(wait)
                    return True
            except Exception as e2:
                logger.error("下拉框选择失败: %s", e2)
            return False

    def get_text(self, control: UIAWrapper) -> str:
        """获取控件文本。

        Args:
            control: 目标控件

        Returns:
            控件文本
        """
        try:
            return control.window_text()
        except Exception:
            return ""

    def get_control_info(self, control: UIAWrapper) -> ControlInfo:
        """获取控件详细信息。

        Args:
            control: 目标控件

        Returns:
            控件信息
        """
        try:
            rect = control.rectangle()
            return ControlInfo(
                control_type=control.element_info.control_type or "",
                class_name=control.element_info.class_name or "",
                automation_id=control.element_info.automation_id or "",
                name=control.element_info.name or "",
                text=control.window_text() or "",
                rect=(rect.left, rect.top, rect.right, rect.bottom),
                is_enabled=control.is_enabled(),
                is_visible=control.is_visible(),
            )
        except Exception as e:
            logger.warning("获取控件信息失败: %s", e)
            return ControlInfo(
                control_type="Unknown",
                class_name="",
                automation_id="",
                name="",
                text="",
                rect=(0, 0, 0, 0),
                is_enabled=False,
                is_visible=False,
            )

    def get_control_tree(
        self,
        max_depth: int = 3,
    ) -> list[dict[str, Any]]:
        """获取控件树。

        Args:
            max_depth: 最大深度

        Returns:
            控件树结构
        """
        if not self._main_window:
            return []

        def _build_tree(control: UIAWrapper, depth: int) -> dict[str, Any]:
            info = self.get_control_info(control)
            result: dict[str, Any] = {
                "type": info.control_type,
                "name": info.name,
                "text": info.text,
                "class": info.class_name,
                "auto_id": info.automation_id,
                "rect": info.rect,
                "enabled": info.is_enabled,
                "children": [],
            }

            if depth < max_depth:
                try:
                    for child in control.children():
                        result["children"].append(_build_tree(child, depth + 1))
                except Exception:
                    pass

            return result

        tree = []
        try:
            for child in self._main_window.children():
                tree.append(_build_tree(child, 0))
        except Exception as e:
            logger.error("获取控件树失败: %s", e)

        return tree

    def dump_control_tree(self, max_depth: int = 3) -> str:
        """输出控件树的可读文本。

        Args:
            max_depth: 最大深度

        Returns:
            可读的控件树文本
        """
        tree = self.get_control_tree(max_depth)

        def _format_node(node: dict[str, Any], indent: int = 0) -> str:
            prefix = "  " * indent
            text = f"{prefix}[{node['type']}] name='{node['name']}' text='{node['text']}' auto_id='{node['auto_id']}'"
            lines = [text]
            for child in node.get("children", []):
                lines.append(_format_node(child, indent + 1))
            return "\n".join(lines)

        return "\n".join(_format_node(node) for node in tree)

    def screenshot(self, output_path: str) -> str:
        """截取当前窗口截图。

        Args:
            output_path: 输出路径

        Returns:
            截图文件路径
        """
        from .screenshot import take_window_screenshot

        return str(take_window_screenshot(output_path, self._window_title))

    def wait_for_control(
        self,
        *,
        name: str | None = None,
        control_type: str | None = None,
        timeout: float = 10.0,
    ) -> UIAWrapper | None:
        """等待控件出现。

        Args:
            name: 控件名称
            control_type: 控件类型
            timeout: 超时时间

        Returns:
            找到的控件
        """
        start = time.time()
        while time.time() - start < timeout:
            control = self.find_control(name=name, control_type=control_type)
            if control and control.is_visible():
                return control
            time.sleep(0.5)
        return None
