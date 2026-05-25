#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""固定配装与搜索预估桥接。"""

from __future__ import annotations

from gui_design.controls.fixed_loadout import (
    refresh_all_fixed_slot_menus,
    resolve_fixed_loadout_selection,
)
from gui_design.controls.search import refresh_search_estimate

class AppLoadoutBridgeMixin:
    def _build_fixed_loadout_selection(self):
        """从底栏勾选状态解析固定/遍历配装。"""
        from calculation.loadout.slot_search import FixedLoadoutSelection

        if not self._fixed_loadout_slots:
            return FixedLoadoutSelection()
        catalog = self._single_skill_preview_equipment_catalog()
        return resolve_fixed_loadout_selection(catalog, self._fixed_loadout_slots)

    def _refresh_fixed_loadout_menus(self) -> None:
        """装备范围变化后刷新各部位套装/装备下拉。"""
        if not self._fixed_loadout_slots:
            return
        catalog = self._single_skill_preview_equipment_catalog()
        refresh_all_fixed_slot_menus(catalog, self._fixed_loadout_slots)

    def _refresh_search_estimate(self) -> None:
        """刷新「预计组合数/耗时」标签（委托 search_controls）。"""
        refresh_search_estimate(self)

