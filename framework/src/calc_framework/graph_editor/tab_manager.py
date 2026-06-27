# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""标签页管理器 — 支持多文件编辑。"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QMessageBox,
    QTabWidget,
    QWidget,
)

from calc_framework.ui.i18n import tr

from .file_actions import (
    collect_document,
    load_document,
    open_graph_file,
    save_graph_file,
)
from .graph_editor_widget import GraphEditorWidget
from .prop_panel import PropPanel


@dataclass
class TabState:
    """单个标签页的状态。"""

    file_path: Path | None = None
    is_modified: bool = False
    canvas: GraphEditorWidget = field(default_factory=GraphEditorWidget)
    prop_panel: PropPanel = field(default_factory=PropPanel)

    @property
    def display_name(self) -> str:
        """显示名称。"""
        if self.file_path:
            return self.file_path.stem
        return tr("desktop.graphEditor.untitled")

    @property
    def full_display_name(self) -> str:
        """完整显示名称（含修改标记）。"""
        name = self.display_name
        if self.is_modified:
            name += " *"
        return name


class TabManager(QTabWidget):
    """标签页管理器，支持多文件编辑。"""

    # 信号
    tab_content_changed = Signal()  # 内容变化信号
    current_tab_changed = Signal()  # 当前标签页变化信号

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._states: dict[int, TabState] = {}
        self._tab_counter = 0

        # 设置标签页属性
        self.setTabsClosable(True)
        self.setMovable(True)

        # 连接信号
        self.tabCloseRequested.connect(self._on_tab_close_requested)
        self.currentChanged.connect(self._on_current_changed)

    @property
    def current_state(self) -> TabState | None:
        """当前标签页状态。"""
        idx = self.currentIndex()
        return self._states.get(idx)

    @property
    def current_canvas(self) -> GraphEditorWidget | None:
        """当前画布。"""
        state = self.current_state
        return state.canvas if state else None

    @property
    def current_prop_panel(self) -> PropPanel | None:
        """当前属性面板。"""
        state = self.current_state
        return state.prop_panel if state else None

    def new_tab(self, file_path: Path | None = None) -> TabState:
        """创建新标签页。

        Args:
            file_path: 可选的文件路径，如果提供则加载文件

        Returns:
            新创建的 TabState
        """
        self._tab_counter += 1

        # 创建新状态
        state = TabState(file_path=file_path)

        # 如果提供了文件路径，加载文件
        if file_path and file_path.is_file():
            try:
                doc = open_graph_file(file_path)
                load_document(doc, state.canvas)
                state.is_modified = False
            except Exception as e:
                QMessageBox.warning(
                    self,
                    tr("desktop.graphEditor.loadFailed"),
                    str(e),
                )
                state.file_path = None

        # 创建标签页容器
        container = QWidget()
        self.addTab(container, state.full_display_name)

        # 保存状态
        idx = self.count() - 1
        self._states[idx] = state

        # 切换到新标签页
        self.setCurrentIndex(idx)

        return state

    def close_tab(self, index: int) -> bool:
        """关闭标签页。

        Args:
            index: 标签页索引

        Returns:
            是否成功关闭
        """
        state = self._states.get(index)
        if state is None:
            return True

        # 如果有未保存的修改，询问用户
        if state.is_modified:
            reply = QMessageBox.question(
                self,
                tr("desktop.graphEditor.saveConfirm"),
                tr("desktop.graphEditor.saveConfirmDetail", name=state.display_name),
                QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel,
            )

            if reply == QMessageBox.StandardButton.Save:
                if not self.save_tab(index):
                    return False
            elif reply == QMessageBox.StandardButton.Cancel:
                return False

        # 移除标签页
        self.removeTab(index)

        # 清理状态
        del self._states[index]

        # 更新索引映射
        new_states: dict[int, TabState] = {}
        for i, (_, state) in enumerate(sorted(self._states.items())):
            new_states[i] = state
        self._states = new_states

        return True

    def save_tab(self, index: int) -> bool:
        """保存标签页。

        Args:
            index: 标签页索引

        Returns:
            是否成功保存
        """
        state = self._states.get(index)
        if state is None:
            return False

        # 如果没有文件路径，需要另存为
        if state.file_path is None:
            return self.save_tab_as(index)

        # 收集文档并保存
        doc = collect_document(state.canvas)
        try:
            save_graph_file(doc, state.file_path)
            state.is_modified = False
            self.setTabText(index, state.full_display_name)
            return True
        except Exception as e:
            QMessageBox.critical(
                self,
                tr("desktop.graphEditor.saveFailed"),
                str(e),
            )
            return False

    def save_tab_as(self, index: int) -> bool:
        """另存为标签页。

        Args:
            index: 标签页索引

        Returns:
            是否成功保存
        """
        state = self._states.get(index)
        if state is None:
            return False

        # 获取保存路径
        path_str, _ = QFileDialog.getSaveFileName(
            self,
            tr("desktop.graphEditor.saveGraph"),
            "",
            tr("desktop.graphEditor.graphFileFilter"),
        )

        if not path_str:
            return False

        state.file_path = Path(path_str)

        return self.save_tab(index)

    def mark_modified(self, index: int) -> None:
        """标记标签页为已修改。

        Args:
            index: 标签页索引
        """
        state = self._states.get(index)
        if state and not state.is_modified:
            state.is_modified = True
            self.setTabText(index, state.full_display_name)

    def _on_tab_close_requested(self, index: int) -> None:
        """标签页关闭请求处理。"""
        self.close_tab(index)

    def _on_current_changed(self, index: int) -> None:
        """当前标签页变化处理。"""
        self.current_tab_changed.emit()
