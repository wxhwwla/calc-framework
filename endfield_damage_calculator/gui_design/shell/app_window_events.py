#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""窗口最小化/恢复/缩放防抖。"""

from __future__ import annotations

from gui_design.app.confirm_orchestrator import WINDOW_RESTORE_SETTLE_MS
from gui_design.layout.gui_layout import (
    control_dock_layout_needs_update,
    should_use_compact_control_dock,
)

class AppWindowEventsMixin:
    def _is_window_iconified(self) -> bool:
        """窗口是否处于最小化状态（最小化时跳过重绘，避免恢复后闪屏）。"""
        try:
            return str(self.app.state()) == "iconic"
        except Exception:
            return False

    def _apply_responsive_layout(self, window_width: int) -> None:
        """按窗口宽度更新高级页布局与按钮文案；未变化时跳过。"""
        width = int(window_width)
        if width <= 1:
            return
        if not control_dock_layout_needs_update(
            width,
            last_width=self._control_dock_last_width,
            last_compact=self._control_dock_last_compact,
        ):
            return
        compact = should_use_compact_control_dock(width)
        self._control_dock_last_width = width
        self._control_dock_last_compact = compact
        self._apply_control_dock_layout(width)
        self._apply_adaptive_button_texts(width)

    def _on_window_unmap(self, _event: object = None) -> None:
        """窗口被隐藏/最小化时取消待执行的恢复防抖。"""
        if self._restore_after_id is not None:
            try:
                self.app.after_cancel(self._restore_after_id)
            except Exception:
                pass
            self._restore_after_id = None

    def _on_window_map(self, _event: object = None) -> None:
        """窗口重新显示：首次映射立即布局，后续恢复走防抖。"""
        if self._is_window_iconified():
            return
        if not self._window_has_been_mapped:
            self._window_has_been_mapped = True
            self._apply_responsive_layout(int(self.app.winfo_width()))
            return
        self._begin_restore_settle()

    def _begin_restore_settle(self) -> None:
        """恢复显示后延迟一帧再重排，避免与 CTk remap 争抢导致黑屏。"""
        self._restore_settling = True
        if self._restore_after_id is not None:
            try:
                self.app.after_cancel(self._restore_after_id)
            except Exception:
                pass
        self._restore_after_id = self.app.after(
            WINDOW_RESTORE_SETTLE_MS,
            self._finish_restore_settle,
        )

    def _finish_restore_settle(self) -> None:
        """恢复防抖结束：若仍可见则补一次必要布局。"""
        self._restore_after_id = None
        self._restore_settling = False
        if self._is_window_iconified():
            return
        self._apply_responsive_layout(int(self.app.winfo_width()))

    def _on_window_resize(self, event) -> None:
        """
        窗口大小变化事件处理：仅根窗口、非最小化、非恢复防抖中且尺寸变化时重排。

        参数：
            event: Tkinter 事件对象（包含窗口大小等信息）
        """
        if getattr(event, "widget", None) is not self.app:
            return
        if self._is_window_iconified() or self._restore_settling:
            return
        width = getattr(event, "width", None)
        if width is None:
            width = self.app.winfo_width()
        self._apply_responsive_layout(int(width))

