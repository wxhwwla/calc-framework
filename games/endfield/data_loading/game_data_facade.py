#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# SPDX-License-Identifier: AGPL-3.0
"""

应用级游戏数据门面：角色、武器、装备行与按范围 catalog 统一入口。



GUI / 多方案对比 / 搜索预估共用同一实例，避免 ``get_equipments()`` 与

``get_equipment_catalog()`` 多处懒加载时机不一致。

"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from games.endfield.data_loading.equipment_catalog import (
    catalog_full_search_error,
    catalog_preview_status_lines,
    catalog_status_message,
    get_equipment_catalog,
)
from games.endfield.data_loading.loader import DataLoadError, get_characters, get_equipments, get_weapons


@dataclass
class GameDataFacade:
    """一次加载后的角色/武器/装备快照（装备 catalog 按范围派生）。"""

    characters: list[dict[str, Any]]

    weapons: list[dict[str, Any]]

    equipment_rows: list[dict[str, Any]]

    load_error: DataLoadError | None = None

    equipment_load_error: DataLoadError | None = None

    @classmethod
    def create(cls, *, preload_equipment: bool = True) -> GameDataFacade:
        """

        从统一加载层构建门面；角色/武器失败不抛异常，记入 ``load_error``。

        """

        load_error: DataLoadError | None = None

        equipment_load_error: DataLoadError | None = None

        try:
            characters = get_characters()

        except DataLoadError as exc:
            load_error = exc

            characters = []

        try:
            weapons = get_weapons()

        except DataLoadError as exc:
            if load_error is None:
                load_error = exc

            weapons = []

        equipment_rows: list[dict[str, Any]] = []

        if preload_equipment:
            try:
                equipment_rows = get_equipments()

            except DataLoadError as exc:
                equipment_load_error = exc

                equipment_rows = []

        return cls(
            characters=characters,
            weapons=weapons,
            equipment_rows=equipment_rows,
            load_error=load_error,
            equipment_load_error=equipment_load_error,
        )

    def equipment_catalog(
        self,
        scope_label: str = "全部装备",
    ) -> dict[str, list[dict[str, Any]]]:
        """按 GUI 装备范围文案返回三部位 catalog（使用已缓存装备行）。"""

        return get_equipment_catalog(
            scope_label=scope_label,
            equipment_rows=self.equipment_rows,
        )

    def catalog_search_error(self, scope_label: str = "全部装备") -> str | None:
        """全量遍历不可用时的错误文案；可用时返回 None。"""

        return catalog_full_search_error(self.equipment_catalog(scope_label))

    def catalog_status(self, scope_label: str = "全部装备") -> str | None:
        """装备 catalog 状态说明；可用时返回 None。"""

        return catalog_status_message(self.equipment_catalog(scope_label))

    def preview_blocked_lines(
        self,
        scope_label: str,
        *,
        mode_label: str,
    ) -> list[str] | None:
        """快速预览不可用时的说明行；可用时返回 None。"""

        return catalog_preview_status_lines(
            self.equipment_catalog(scope_label),
            mode_label=mode_label,
        )

    def reload_equipment_rows(self) -> None:
        """清除 loader 装备缓存并重新读入（录入/sync 后可选调用）。"""

        from games.endfield.data_loading.loader import reload_equipments

        reload_equipments()

        try:
            self.equipment_rows = get_equipments()

            self.equipment_load_error = None

        except DataLoadError as exc:
            self.equipment_rows = []

            self.equipment_load_error = exc
