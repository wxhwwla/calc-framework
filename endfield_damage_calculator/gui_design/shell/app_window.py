#!/usr/bin/env python3
"""高级页三列响应式 grid 与按钮文案。"""

from __future__ import annotations

from gui_design.layout.gui_layout import (
    CONTROL_INNER_COL_ACTIONS_MINSIZE,
    CONTROL_INNER_COL_COMPACT_MULTI_WEIGHT,
    CONTROL_INNER_COL_COMPACT_SEARCH_WEIGHT,
    CONTROL_INNER_COL_MULTI_WEIGHT,
    CONTROL_INNER_COL_SEARCH_WEIGHT,
    search_action_button_texts,
    should_use_compact_control_dock,
)


class AppWindowMixin:
    def _apply_control_dock_layout(self, window_width: int) -> None:
        """根据窗口宽度重排高级页三列，避免窄窗口下横向挤压。"""
        body = self._control_dock_body
        actions = self._control_col_actions
        search = self._control_col_search
        multi = self._control_col_multi
        if body is None or actions is None or search is None or multi is None:
            return

        compact = should_use_compact_control_dock(window_width)
        if compact:
            body.grid_columnconfigure(
                0,
                weight=CONTROL_INNER_COL_COMPACT_SEARCH_WEIGHT,
                minsize=220,
            )
            body.grid_columnconfigure(
                1,
                weight=CONTROL_INNER_COL_COMPACT_MULTI_WEIGHT,
                minsize=260,
            )
            body.grid_columnconfigure(2, weight=0, minsize=0)
            actions.grid(row=0, column=0, columnspan=2, padx=(4, 4), pady=(4, 2), sticky="new")
            search.grid(row=1, column=0, padx=(4, 6), pady=(2, 4), sticky="new")
            multi.grid(row=1, column=1, padx=(6, 4), pady=(2, 4), sticky="nsew")
            return

        body.grid_columnconfigure(0, weight=0, minsize=CONTROL_INNER_COL_ACTIONS_MINSIZE)
        body.grid_columnconfigure(1, weight=CONTROL_INNER_COL_SEARCH_WEIGHT, minsize=0)
        body.grid_columnconfigure(2, weight=CONTROL_INNER_COL_MULTI_WEIGHT, minsize=0)
        actions.grid(row=0, column=0, columnspan=1, padx=(4, 8), pady=4, sticky="new")
        search.grid(row=0, column=1, padx=8, pady=4, sticky="new")
        multi.grid(row=0, column=2, padx=(8, 4), pady=4, sticky="nsew")

    def _apply_adaptive_button_texts(self, window_width: int) -> None:
        """按窗口宽度调整按钮文案长度，降低窄屏文本挤压。"""
        compact = should_use_compact_control_dock(window_width)
        full_text, mvp_text = search_action_button_texts(compact=compact)
        if self.full_search_btn is not None:
            self.full_search_btn.configure(text=full_text)
        if self.mvp_search_btn is not None:
            self.mvp_search_btn.configure(text=mvp_text)
