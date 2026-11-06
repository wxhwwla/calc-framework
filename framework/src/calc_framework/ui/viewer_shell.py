# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""CalcPackViewer 共享外壳 Mixin — 顶部工具条 + 2×2 页 + 确认门控。

查看器不再使用菜单栏与三栏分割器，而是套用三个桌面计算器共用的
:class:`~calc_framework.ui.calculator_shell.CalculatorShell`：

- 顶部工具条：打开、信息、插件、主题、帮助、捐赠、退出。
- 中部：按 ``layout.sections[].tab`` 生成整页 2×2 区域。
- 底部：确认按钮 + 页签。
- 实体选择与输入变更只标记「待确认」，点击确认后才重新求值并刷新明细。
"""

from __future__ import annotations

from typing import Any

from PySide6.QtGui import QActionGroup
from PySide6.QtWidgets import (
    QLabel,
    QMenu,
    QMessageBox,
    QScrollArea,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from ..logging import get_logger
from .calculator_shell import CalculatorPage, CalculatorShell, ZoneCard
from .i18n import tr

logger = get_logger(__name__)

_ZONE_ORDER: tuple[str, ...] = ("top_left", "top_right", "bottom_left", "bottom_right")


def _scrollable(widget: QWidget) -> QScrollArea:
    """把区域内容包进可滚动容器，窄窗口下不撑破四区布局。"""
    area = QScrollArea()
    area.setWidgetResizable(True)
    area.setFrameShape(QScrollArea.Shape.NoFrame)
    area.setWidget(widget)
    return area


def _stacked(widgets: list[QWidget]) -> QWidget:
    """把多个分区控件纵向堆叠成一个容器。"""
    container = QWidget()
    layout = QVBoxLayout(container)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(6)
    for widget in widgets:
        layout.addWidget(widget)
    layout.addStretch()
    return container


def _chunk(sections: list[Any], count: int = 4) -> list[list[Any]]:
    """按阅读顺序把分区轮流分配到四个区域。"""
    chunks: list[list[Any]] = [[] for _ in range(count)]
    for index, section in enumerate(sections):
        chunks[index % count].append(section)
    return chunks


class CalcPackViewerShellMixin:
    """CalcPackViewer 的共享外壳与确认流程。"""

    # Mixin 属性占位 — 由 CalcPackViewer 提供（Pylance 类型识别）
    _shell: CalculatorShell
    _layout: Any
    _meta: dict[str, Any]
    _compute_sheet: Any
    _theme_manager: Any
    _theme_actions: dict[str, Any]
    _entity_group: QWidget
    _detail_scroll: QScrollArea
    _detail_container: QWidget
    _status_label: QLabel

    def _init_shell(self) -> None:
        """创建共享外壳并接好确认信号。"""
        self._shell = CalculatorShell()
        self.setCentralWidget(self._shell)
        self._status_label = self._shell.status_label
        self._build_viewer_toolbar()
        self._shell.confirmed.connect(self.confirm)

    def _build_viewer_toolbar(self) -> None:
        """把所有与计算无关的入口放进顶部工具条。"""
        shell = self._shell
        shell.add_tool_action(
            tr("desktop.viewer.menuOpenCalcpack"),
            self._open_file,
            shortcut="Ctrl+O",
        )
        shell.add_tool_action(tr("desktop.viewer.actionInfo"), self._show_info_dialog)
        shell.add_tool_action(tr("desktop.viewer.menuPluginManager"), self._show_plugin_manager_dialog)
        shell.add_tool_widget(self._build_theme_button())
        shell.add_tool_separator()
        shell.add_tool_action(tr("desktop.viewer.menuHelpUsage"), self._show_help, shortcut="F1")
        shell.add_tool_action(tr("desktop.viewer.actionDonate"), self._show_donation_dialog)
        shell.add_tool_separator()
        shell.add_tool_action(tr("desktop.viewer.menuExit"), self.close, shortcut="Ctrl+Q")

    def _build_theme_button(self) -> QToolButton:
        """主题下拉按钮（替代原「主题」菜单）。"""
        button = QToolButton()
        button.setText(tr("desktop.shell.theme"))
        button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        menu = QMenu(button)
        group = QActionGroup(button)
        group.setExclusive(True)
        group.triggered.connect(self._on_theme_switched)
        self._theme_actions = {}
        for key in self._theme_manager.theme_names:
            theme = self._theme_manager.get_theme(key)
            action = menu.addAction(theme.get("name", key) if theme else key)
            action.setCheckable(True)
            action.setData(key)
            if key == self._theme_manager.current_name:
                action.setChecked(True)
            group.addAction(action)
            self._theme_actions[key] = action
        button.setMenu(menu)
        return button

    def _show_donation_dialog(self) -> None:
        """打开共享捐赠弹窗。"""
        from utils.gui.donation import open_donation_dialog

        open_donation_dialog(self)  # type: ignore[arg-type]

    def _show_info_dialog(self) -> None:
        """显示计算包元数据与统计信息。"""
        meta = self._meta or {}
        dag_service = getattr(self, "_dag_service", None)
        variables = len(dag_service.dag.variables) if dag_service is not None else 0
        outputs = len(dag_service.dag.outputs) if dag_service is not None else 0
        lines = [
            f"{tr('desktop.viewer.labelName')} {meta.get('name', '—')}",
            f"{tr('desktop.viewer.labelGame')} {meta.get('game', '—')}",
            f"{tr('desktop.viewer.labelVersion')} {meta.get('version', '—')}",
            f"{tr('desktop.viewer.labelVariables')} {variables}",
            f"{tr('desktop.viewer.labelOutputs')} {outputs}",
            "",
            str(meta.get("description", "—")),
        ]
        QMessageBox.information(self, tr("desktop.viewer.packInfo"), "\n".join(lines))  # type: ignore[arg-type]

    # ── 页面构建 ───────────────────────────────

    def _layout_tabs(self) -> list[str]:
        """按布局中首次出现的顺序返回页签；无页签时返回「计算」。"""
        default_tab = tr("desktop.shell.pageCalc")
        tabs: list[str] = []
        if self._layout is None:
            return [default_tab]
        for section in self._layout.sections:
            tab = section.tab or default_tab
            if tab not in tabs:
                tabs.append(tab)
        return tabs or [default_tab]

    def _calc_tab(self, tabs: list[str]) -> str:
        """返回包含输入分区的页签；没有输入时使用第一页。"""
        if self._layout is not None:
            for tab in tabs:
                if any(section.type == "inputs" and (section.tab or tabs[0]) == tab for section in self._layout.sections):
                    return tab
        return tabs[0]

    def _sections_for_tab(self, tab: str, sections: list[Any]) -> list[Any]:
        """取属于指定页签的分区（无页签分区归入第一页）。"""
        first = self._layout_tabs()[0]
        return [section for section in sections if (section.tab or first) == tab]

    def _rebuild_shell(self) -> None:
        """按当前布局重建所有整页与四区内容。"""
        self._shell.clear_pages()
        if self._layout is None:
            return

        tabs = self._layout_tabs()
        calc_tab = self._calc_tab(tabs)
        sections = list(self._layout.sections)

        for tab in tabs:
            if tab == calc_tab:
                page = self._build_calc_page(tab, sections)
            else:
                page = self._build_detail_page(tab, self._sections_for_tab(tab, sections))
            self._shell.add_page(tab, page)

        self._shell.set_confirmed(tr("desktop.shell.confirmed"))
        self._shell.set_status(tr("desktop.shell.statusReady"))

    def _build_calc_page(self, tab: str, sections: list[Any]) -> CalculatorPage:
        """构建计算页：实体选择 / 输入参数 / 实体数据 / 计算结果。"""
        page = CalculatorPage(
            top_left_title=tr("desktop.viewer.selectEntity"),
            top_right_title=tr("desktop.viewer.inputParams"),
            bottom_left_title=tr("desktop.viewer.entityData"),
            bottom_right_title=tr("desktop.viewer.results"),
        )

        has_entities = bool(getattr(self, "_entity_selectors", {})) or getattr(self, "_level_spin", None) is not None
        if has_entities:
            page.zone("top_left").add_widget(self._entity_group)
        else:
            page.set_zone_visible("top_left", False)

        input_sections = [section for section in sections if section.type == "inputs"]
        self._fill_zone(page.zone("top_right"), input_sections)

        if self._meta.get("entity_detail"):
            page.zone("bottom_left").add_widget(self._detail_scroll)
        else:
            page.set_zone_visible("bottom_left", False)

        output_sections = [section for section in self._sections_for_tab(tab, sections) if section.type == "outputs"]
        self._fill_zone(page.zone("bottom_right"), output_sections)
        return page

    def _build_detail_page(self, tab: str, sections: list[Any]) -> CalculatorPage:
        """构建明细页：把该页签的输出分区轮流放进四个区域。"""
        page = CalculatorPage(
            top_left_title=tab,
            top_right_title=tab,
            bottom_left_title=tab,
            bottom_right_title=tab,
        )
        output_sections = [section for section in sections if section.type == "outputs"]
        chunks = _chunk(output_sections, len(_ZONE_ORDER))
        for key, chunk in zip(_ZONE_ORDER, chunks):
            if not chunk:
                page.set_zone_visible(key, False)
                continue
            page.zone(key).setTitle(chunk[0].title if len(chunk) == 1 else tab)
            self._fill_zone(page.zone(key), chunk)
        return page

    def _fill_zone(self, zone: ZoneCard, sections: list[Any]) -> None:
        """构建分区控件并放入区域；没有内容时隐藏该区域。"""
        widgets: list[QWidget] = []
        for section in sections:
            if section.type == "inputs" or section.type == "outputs":
                widget = self._compute_sheet.build_section_widget(section)
            elif section.type == "widget":
                # 捐赠等非计算组件统一由顶部工具条提供，不再占用计算区域。
                logger.debug("布局组件 %s 已由工具条替代", section.id)
                continue
            else:
                widget = None
            if widget is not None:
                widgets.append(widget)
        if widgets:
            zone.add_widget(_scrollable(_stacked(widgets)))
        else:
            zone.setVisible(False)

    # ── 确认门控 ───────────────────────────────

    def _mark_pending(self) -> None:
        """标记存在未确认的更改，不触发求值。"""
        if not hasattr(self, "_shell"):
            return
        self._shell.set_pending(tr("desktop.shell.pending"))
        self._shell.set_status(tr("desktop.shell.statusPending"))

    def _on_input_changed(self, _path: str, _value: object) -> None:
        """输入控件变化时标记待确认。"""
        self._mark_pending()

    def confirm(self) -> None:
        """应用当前选择与输入，重新求值并刷新明细与条件禁用。"""
        sheet = self._compute_sheet
        if sheet is None:
            return
        sheet._base_context = self._build_current_context()
        sheet.evaluate()
        self._rebuild_detail_panel()
        self._apply_entity_input_rules()
        self._shell.set_confirmed(tr("desktop.shell.confirmed"))
        self._shell.set_status(self._entity_status_text())

    def _entity_status_text(self) -> str:
        """构建「已确认 — weapon=…」状态文案。"""
        selected = self._selected_entity_names()
        names = ", ".join(f"{source}={name}" for source, name in selected.items() if name)
        level = self._level_spin.value() if getattr(self, "_level_spin", None) else None
        suffix = f" Lv.{level}" if level is not None else ""
        return f"{tr('desktop.shell.confirmed')} — {names or tr('desktop.shell.statusReady')}{suffix}"


__all__ = ["CalcPackViewerShellMixin"]
