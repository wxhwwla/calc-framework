#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""高级页操作/搜索/多技能三列控件组装。"""

from __future__ import annotations

import customtkinter as ctk

from gui_design.calc_mode_labels import CALC_MODE_LABELS
from gui_design.confirm_orchestrator import handle_confirm
from gui_design.controls.enhancement_controls import place_enhancement_section
from gui_design.controls.multi_skill_controls import place_multi_skill_section
from gui_design.controls.search_controls import place_search_section
from gui_design.gui_layout import (
    PRIMARY_ACTION_BUTTON_HEIGHT,
    SECONDARY_ACTION_BUTTON_HEIGHT,
)
from gui_design.label_layout import bind_wrapped_label
from gui_design.loadout_pending import mark_loadout_pending
from legal.attribution import open_attribution_dialog

class AppControlDockMixin:
    def _on_attribution(self) -> None:
        """打开数据来源与许可说明窗口。"""
        open_attribution_dialog(
            self.app,
            font=self.big_font,
            small_font=self.small_font,
        )

    def _wrap_control_label(self, label: ctk.CTkLabel, container: ctk.CTkBaseClass) -> None:
        """底栏内长文案：以整个 control_frame 宽度为换行参考。"""
        bind_wrapped_label(label, container, viewport=self.control_frame, padding=12)

    def _build_control_panel(self) -> None:
        """底栏三列：操作/模式 | 全量搜索 | 多技能次数。"""
        assert (
            self._control_col_actions is not None
            and self._control_col_search is not None
            and self._control_col_multi is not None
        )
        actions = self._control_col_actions
        search = self._control_col_search
        multi = self._control_col_multi
        for col in (actions, search, multi):
            col.grid_columnconfigure(0, weight=1)

        def _section(parent: ctk.CTkFrame, title: str, row: int) -> int:
            ctk.CTkLabel(
                parent,
                text=title,
                font=self.big_font,
                text_color="#FF6B6B",
            ).grid(row=row, column=0, padx=4, pady=(6, 2), sticky="w")
            return row + 1

        def _place(parent: ctk.CTkFrame, row: int, widget, *, pady: tuple[int, int] = (0, 4)) -> int:
            widget.grid(row=row, column=0, padx=4, pady=pady, sticky="ew")
            return row + 1

        ar = 0
        ar = _section(actions, "操作", ar)
        self.back_to_main_btn = ctk.CTkButton(
            actions,
            text="返回计算页",
            font=self.small_font,
            height=SECONDARY_ACTION_BUTTON_HEIGHT,
            fg_color="transparent",
            border_width=1,
            command=self._show_main_page,
        )
        ar = _place(actions, ar, self.back_to_main_btn, pady=(0, 6))
        self.confirm_btn = ctk.CTkButton(
            actions,
            text="确认选择",
            font=self.big_font,
            height=PRIMARY_ACTION_BUTTON_HEIGHT,
            command=lambda: handle_confirm(self, force=True),
        )
        ar = _place(actions, ar, self.confirm_btn, pady=(0, 6))
        self.attribution_btn = ctk.CTkButton(
            actions,
            text="数据来源与许可",
            font=self.small_font,
            height=SECONDARY_ACTION_BUTTON_HEIGHT,
            fg_color="transparent",
            border_width=1,
            command=self._on_attribution,
        )
        ar = _place(actions, ar, self.attribution_btn, pady=(0, 8))
        ar = _section(actions, "乘区展示", ar)
        ar = _place(
            actions,
            ar,
            ctk.CTkLabel(actions, text="计算模式", font=self.small_font, text_color="#CCCCCC"),
            pady=(0, 2),
        )
        self.calc_mode_menu = ctk.CTkOptionMenu(
            actions,
            values=list(CALC_MODE_LABELS),
            variable=self.calc_mode_var,
            font=self.small_font,
            command=lambda _v: mark_loadout_pending(self),
        )
        ar = _place(actions, ar, self.calc_mode_menu, pady=(0, 4))
        ar = place_enhancement_section(
            self, actions, start_row=ar, place_fn=_place
        )

        place_search_section(
            self,
            search,
            wrap_label=self._wrap_control_label,
        )

        place_multi_skill_section(
            self,
            multi,
            wrap_label=self._wrap_control_label,
            schedule_confirm=lambda **_kw: mark_loadout_pending(self),
        )

