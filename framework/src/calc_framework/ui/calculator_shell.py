# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""计算器共享布局骨架 — 顶部工具条 + 2×2 页 + 底部确认/页签。

三个桌面计算器（终末地、明日方舟、拉格朗日）以及 MCP 生成的计算器都使用
同一套视觉结构：

- 顶部：与计算无关的入口（帮助、捐赠、设置、日志等）。
- 中部：每个页签一整页，页内固定四区（左上/右上/左下/右下）。
- 底部：左侧确认按钮，右侧页签切换。

本模块只负责布局与状态文案，不包含任何计算逻辑。
"""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QSplitter,
    QStackedWidget,
    QTabBar,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from .i18n import tr

ZONE_KEYS: tuple[str, ...] = ("top_left", "top_right", "bottom_left", "bottom_right")

_ZONE_LAYOUTS: dict[str, str] = {
    "top_left": "top",
    "top_right": "top",
    "bottom_left": "bottom",
    "bottom_right": "bottom",
}


class ZoneCard(QGroupBox):
    """2×2 页中的一个区域卡片。

    区域标题由页面声明，内容由调用方通过 :meth:`add_widget` 放入。
    """

    def __init__(self, title: str, parent: QWidget | None = None) -> None:
        super().__init__(title, parent)
        self._content = QVBoxLayout(self)
        self._content.setContentsMargins(8, 14, 8, 8)
        self._content.setSpacing(4)

    def add_widget(self, widget: QWidget, stretch: int = 1) -> None:
        """把控件加入区域（自动重设父控件）。"""
        widget.setParent(self)
        self._content.addWidget(widget, stretch)

    def add_layout(self, layout) -> None:
        """把子布局加入区域。"""
        self._content.addLayout(layout)

    def content_layout(self) -> QVBoxLayout:
        """返回区域内部布局，供调用方追加间距或弹簧。"""
        return self._content


class CalculatorPage(QWidget):
    """固定 2×2 区域的整页容器。

    四区由两个水平分割器组成，外层再套一个垂直分割器，窗口缩放时四个
    区域都能获得可调空间。页签切换的是整页，而不是页内某个面板。
    """

    def __init__(
        self,
        *,
        top_left_title: str,
        top_right_title: str,
        bottom_left_title: str,
        bottom_right_title: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._zones: dict[str, ZoneCard] = {
            "top_left": ZoneCard(top_left_title, self),
            "top_right": ZoneCard(top_right_title, self),
            "bottom_left": ZoneCard(bottom_left_title, self),
            "bottom_right": ZoneCard(bottom_right_title, self),
        }

        self._top_splitter = self._make_row_splitter(
            self._zones["top_left"],
            self._zones["top_right"],
        )
        self._bottom_splitter = self._make_row_splitter(
            self._zones["bottom_left"],
            self._zones["bottom_right"],
        )

        outer = QSplitter(Qt.Orientation.Vertical, self)
        outer.setChildrenCollapsible(False)
        outer.addWidget(self._top_splitter)
        outer.addWidget(self._bottom_splitter)
        outer.setSizes([420, 360])

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)
        layout.addWidget(outer)

    @staticmethod
    def _make_row_splitter(left: QWidget, right: QWidget) -> QSplitter:
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.addWidget(left)
        splitter.addWidget(right)
        splitter.setSizes([500, 500])
        return splitter

    def zone(self, key: str) -> ZoneCard:
        """按 ``top_left`` / ``top_right`` / ``bottom_left`` / ``bottom_right`` 取区域。"""
        try:
            return self._zones[key]
        except KeyError as exc:
            raise KeyError(f"未知区域: {key}") from exc

    def set_zone_visible(self, key: str, visible: bool) -> None:
        """隐藏/显示区域，并让同一行的另一区占满宽度。"""
        zone = self.zone(key)
        zone.setVisible(visible)
        splitter = self._top_splitter if _ZONE_LAYOUTS[key] == "top" else self._bottom_splitter
        if visible:
            splitter.setSizes([1, 1])
        elif key.endswith("_left"):
            splitter.setSizes([0, 1])
        else:
            splitter.setSizes([1, 0])


class CalculatorShell(QWidget):
    """计算器共享外壳：顶部工具条、页面栈、底部确认按钮与页签。"""

    confirmed = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("calculatorShell")

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self.toolbar = QToolBar(self)
        self.toolbar.setObjectName("calculatorToolbar")
        self.toolbar.setMovable(False)
        self.toolbar.setFloatable(False)
        self.toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
        outer.addWidget(self.toolbar)

        self.page_stack = QStackedWidget(self)
        outer.addWidget(self.page_stack, 1)

        bottom = QWidget(self)
        bottom.setObjectName("calculatorBottomBar")
        bottom_layout = QHBoxLayout(bottom)
        bottom_layout.setContentsMargins(8, 6, 8, 6)
        bottom_layout.setSpacing(8)

        self._confirm = QPushButton(tr("desktop.shell.confirm"), bottom)
        self._confirm.setObjectName("calculatorConfirmButton")
        self._confirm.setMinimumHeight(38)
        self._confirm.setMinimumWidth(220)
        self._confirm.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self._confirm.clicked.connect(self.confirmed.emit)
        bottom_layout.addWidget(self._confirm)

        self._status = QLabel("", bottom)
        self._status.setObjectName("calculatorStatusLabel")
        self._status.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        bottom_layout.addWidget(self._status, 1)

        self._tabs = QTabBar(bottom)
        self._tabs.setObjectName("calculatorPageTabs")
        self._tabs.setExpanding(False)
        self._tabs.setDrawBase(False)
        self._tabs.currentChanged.connect(self.page_stack.setCurrentIndex)
        bottom_layout.addWidget(self._tabs)

        outer.addWidget(bottom)

    # ── 顶部工具条 ─────────────────────────────

    def add_tool_action(
        self,
        text: str,
        slot: Callable[[], None],
        *,
        shortcut: str | None = None,
    ) -> QAction:
        """向顶部工具条添加一个文本按钮，返回其 QAction。"""
        action = QAction(text, self)
        if shortcut:
            action.setShortcut(QKeySequence(shortcut))
        action.triggered.connect(lambda: slot())
        self.toolbar.addAction(action)
        return action

    def add_tool_widget(self, widget: QWidget) -> None:
        """向顶部工具条添加自定义控件（如主题下拉按钮）。"""
        self.toolbar.addWidget(widget)

    def add_tool_separator(self) -> None:
        """在工具条中插入分隔线。"""
        self.toolbar.addSeparator()

    # ── 页面与页签 ─────────────────────────────

    def add_page(self, title: str, page: QWidget) -> int:
        """添加一整页，并在底部页签加入同名标签。"""
        index = self.page_stack.addWidget(page)
        tab_index = self._tabs.addTab(title)
        if tab_index == 0:
            self.page_stack.setCurrentIndex(0)
        return index

    def clear_pages(self) -> None:
        """清空所有页面与页签（用于重新加载计算包）。"""
        while self._tabs.count():
            self._tabs.removeTab(0)
        while self.page_stack.count():
            widget = self.page_stack.widget(0)
            if widget is None:
                break
            self.page_stack.removeWidget(widget)
            widget.deleteLater()

    @property
    def page_count(self) -> int:
        """当前页数。"""
        return self.page_stack.count()

    @property
    def current_page(self) -> int:
        """当前页索引。"""
        return self.page_stack.currentIndex()

    def set_current_page(self, index: int) -> None:
        """切换整页（同时同步底部页签）。"""
        if 0 <= index < self.page_stack.count():
            self._tabs.setCurrentIndex(index)

    def tab_texts(self) -> list[str]:
        """底部页签文案列表。"""
        return [self._tabs.tabText(index) for index in range(self._tabs.count())]

    # ── 底部确认与状态 ─────────────────────────

    @property
    def confirm_button(self) -> QPushButton:
        """底部确认按钮。"""
        return self._confirm

    def set_confirm_text(self, text: str) -> None:
        """设置确认按钮文案。"""
        self._confirm.setText(text)

    def set_confirm_enabled(self, enabled: bool) -> None:
        """启用/禁用确认按钮。"""
        self._confirm.setEnabled(enabled)

    def set_pending(self, text: str) -> None:
        """标记为待确认状态。"""
        self.set_confirm_enabled(True)
        self._confirm.setText(text)

    def set_confirmed(self, text: str) -> None:
        """标记为已确认状态。"""
        self.set_confirm_enabled(True)
        self._confirm.setText(text)

    @property
    def status_label(self) -> QLabel:
        """底部状态标签（供既有调用方复用 ``setText``）。"""
        return self._status

    def set_status(self, text: str) -> None:
        """设置底部状态文字。"""
        self._status.setText(text)

    def status_text(self) -> str:
        """当前底部状态文字。"""
        return self._status.text()


__all__ = ["ZONE_KEYS", "CalculatorPage", "CalculatorShell", "ZoneCard"]
