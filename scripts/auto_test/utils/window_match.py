# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""顶层窗口标题匹配。

不依赖 pywinauto / Windows API，便于在任意平台做单元测试。
"""

from __future__ import annotations

from collections.abc import Iterable

__all__ = ["WindowEntry", "match_window"]

WindowEntry = tuple[int, str, str]


def match_window(
    windows: Iterable[WindowEntry],
    title: str,
    *,
    class_name: str | None = None,
) -> WindowEntry | None:
    """返回第一个标题包含 ``title`` 的窗口条目。

    Args:
        windows: ``(hwnd, 标题, 类名)`` 的可迭代对象。
        title: 标题子串。
        class_name: 可选的精确类名过滤。

    Returns:
        匹配的窗口条目；未找到时返回 ``None``。
    """
    for hwnd, window_title, window_class in windows:
        if title not in window_title:
            continue
        if class_name is not None and window_class != class_name:
            continue
        return hwnd, window_title, window_class
    return None
