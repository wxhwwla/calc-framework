#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""全量搜索：按部位固定装备（0–4 件）控件与解析。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Optional

from utils.platform_win32_patch import apply_platform_win32_patch

apply_platform_win32_patch()
import customtkinter as ctk

from calculation.loadout_slot_search import FixedLoadoutSelection
from data.equipment_filters import (
    SET_FILTER_ALL,
    equipment_names_from_rows,
    filter_rows_by_set_label,
    list_set_filter_options,
)

# catalog 键 → 界面标签
SLOT_SPECS: tuple[tuple[str, str, str], ...] = (
    ("chest", "chest", "护甲"),
    ("gloves", "gloves", "护手"),
    ("accessory_a", "accessories", "配件 A"),
    ("accessory_b", "accessories", "配件 B"),
)


@dataclass
class FixedSlotWidgets:
    """单格固定装备 UI 绑定。"""

    slot_key: str
    catalog_key: str
    enabled_var: ctk.BooleanVar
    set_filter_var: ctk.StringVar
    equipment_var: ctk.StringVar
    set_menu: ctk.CTkOptionMenu
    equip_menu: ctk.CTkOptionMenu


def resolve_fixed_loadout_selection(
    catalog: dict[str, list[dict[str, Any]]],
    slots: dict[str, FixedSlotWidgets],
) -> FixedLoadoutSelection:
    """从 GUI 状态解析固定配装；未勾选固定的部位为 None（遍历）。"""

    def _pick(slot_key: str, catalog_key: str) -> Optional[dict]:
        binding = slots[slot_key]
        if not binding.enabled_var.get():
            return None
        name = (binding.equipment_var.get() or "").strip()
        for row in catalog.get(catalog_key) or []:
            if str(row.get("名称") or "") == name:
                return row
        return None

    return FixedLoadoutSelection(
        chest=_pick("chest", "chest"),
        gloves=_pick("gloves", "gloves"),
        accessory_a=_pick("accessory_a", "accessories"),
        accessory_b=_pick("accessory_b", "accessories"),
    )


def refresh_slot_equipment_menu(
    binding: FixedSlotWidgets,
    catalog: dict[str, list[dict[str, Any]]],
) -> None:
    """按当前套装筛选刷新装备下拉。"""
    rows = list(catalog.get(binding.catalog_key) or [])
    filtered = filter_rows_by_set_label(rows, binding.set_filter_var.get())
    names = equipment_names_from_rows(filtered)
    if not names:
        binding.equip_menu.configure(values=["（无候选）"], state="disabled")
        binding.equipment_var.set("（无候选）")
        return
    binding.equip_menu.configure(values=names, state="normal")
    current = (binding.equipment_var.get() or "").strip()
    if current not in names:
        binding.equipment_var.set(names[0])


def refresh_all_fixed_slot_menus(
    catalog: dict[str, list[dict[str, Any]]],
    slots: dict[str, FixedSlotWidgets],
) -> None:
    for binding in slots.values():
        rows = list(catalog.get(binding.catalog_key) or [])
        set_options = list_set_filter_options(rows)
        binding.set_menu.configure(values=set_options)
        if binding.set_filter_var.get() not in set_options:
            binding.set_filter_var.set(SET_FILTER_ALL)
        refresh_slot_equipment_menu(binding, catalog)
        enabled = bool(binding.enabled_var.get())
        binding.set_menu.configure(state="normal" if enabled else "disabled")
        binding.equip_menu.configure(state="normal" if enabled else "disabled")


def create_fixed_loadout_controls(
    parent: ctk.CTkBaseClass,
    *,
    small_font: ctk.CTkFont,
    on_change: Callable[[], None],
) -> dict[str, FixedSlotWidgets]:
    """在 parent 内创建四行「固定此部位 + 套装 + 装备」控件。"""
    slots: dict[str, FixedSlotWidgets] = {}
    parent.grid_columnconfigure(1, weight=0, minsize=88)
    parent.grid_columnconfigure(2, weight=1)

    for row_idx, (slot_key, catalog_key, label) in enumerate(SLOT_SPECS):
        enabled_var = ctk.BooleanVar(value=False)
        set_filter_var = ctk.StringVar(value=SET_FILTER_ALL)
        equipment_var = ctk.StringVar(value="")

        ctk.CTkCheckBox(
            parent,
            text=f"固定{label}",
            variable=enabled_var,
            font=small_font,
            command=on_change,
        ).grid(row=row_idx, column=0, padx=(4, 8), pady=2, sticky="w")

        set_menu = ctk.CTkOptionMenu(
            parent,
            values=[SET_FILTER_ALL],
            variable=set_filter_var,
            font=small_font,
            width=100,
            state="disabled",
        )
        set_menu.grid(row=row_idx, column=1, padx=(0, 4), pady=2, sticky="ew")

        equip_menu = ctk.CTkOptionMenu(
            parent,
            values=["—"],
            variable=equipment_var,
            font=small_font,
            state="disabled",
        )
        equip_menu.grid(row=row_idx, column=2, padx=(0, 4), pady=2, sticky="ew")

        binding = FixedSlotWidgets(
            slot_key=slot_key,
            catalog_key=catalog_key,
            enabled_var=enabled_var,
            set_filter_var=set_filter_var,
            equipment_var=equipment_var,
            set_menu=set_menu,
            equip_menu=equip_menu,
        )
        slots[slot_key] = binding

        def _on_set_change(_v: str = "", *, b: FixedSlotWidgets = binding) -> None:
            on_change()

        def _on_enable(*_args: object, b: FixedSlotWidgets = binding) -> None:
            on_change()

        enabled_var.trace_add("write", lambda *_a, b=binding: _on_enable())
        set_menu.configure(command=_on_set_change)
        equip_menu.configure(command=lambda _v: on_change())

    return slots
