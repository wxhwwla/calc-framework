#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# SPDX-License-Identifier: AGPL-3.0
"""

乘区管理器模块



负责管理所有乘区的注册、计算和组合。

"""

from .base_zone import BaseZone


class ZoneManager:
    """

    乘区管理器



    管理多个乘区实例，提供统一的计算接口。



    功能：

        1. 注册乘区

        2. 启用/禁用乘区

        3. 计算所有乘区的总乘数

        4. 获取单个乘区的计算结果

        5. 清空所有乘区



    使用示例：

        manager = ZoneManager()

        manager.add_zone(AttackMultiplierZone())

        manager.add_zone(DamageBonusZone())



        total = manager.calculate_total()

        print(f"总乘数: {total}")

    """

    def __init__(self):
        """初始化乘区管理器"""

        self._zones: list[BaseZone] = []

    def add_zone(self, zone: BaseZone) -> None:
        """

        添加一个乘区



        参数：

            zone: BaseZone 子类实例

        """

        self._zones.append(zone)

    def remove_zone(self, zone_name: str) -> bool:
        """

        根据名称移除一个乘区



        参数：

            zone_name: 乘区名称



        返回：

            是否成功移除（True/False）

        """

        original_count = len(self._zones)

        self._zones = [z for z in self._zones if z.name != zone_name]

        return len(self._zones) < original_count

    def get_zone(self, zone_name: str) -> BaseZone | None:
        """

        根据名称获取乘区



        参数：

            zone_name: 乘区名称



        返回：

            乘区实例（如果找到），否则返回 None

        """

        for zone in self._zones:
            if zone.name == zone_name:
                return zone

        return None

    def get_all_zones(self) -> list[BaseZone]:
        """获取所有注册的乘区"""

        return self._zones.copy()

    def calculate_total(self) -> float:
        """

        计算所有启用乘区的总乘数



        返回：

            所有乘区乘数的乘积



        逻辑：

            1. 遍历所有注册的乘区

            2. 对于启用的乘区，调用其 calculate 方法

            3. 将所有结果相乘得到总乘数

            4. 如果没有启用的乘区，返回 1.0

        """

        total = 1.0

        for zone in self._zones:
            if zone.is_enabled():
                multiplier = zone.calculate()

                total *= multiplier

        return total

    def calculate_zone(self, zone_name: str) -> float | None:
        """

        计算单个乘区的乘数



        参数：

            zone_name: 乘区名称



        返回：

            乘数值（如果找到且启用），否则返回 None

        """

        zone = self.get_zone(zone_name)

        if zone and zone.is_enabled():
            return zone.calculate()

        return None

    def calculate_all(self) -> dict[str, float]:
        """

        计算所有乘区的乘数（包括禁用的）



        返回：

            字典，键为乘区名称，值为乘数值（禁用的乘区返回 1.0）

        """

        results = {}

        for zone in self._zones:
            if zone.is_enabled():
                results[zone.name] = zone.calculate()

            else:
                results[zone.name] = 1.0

        return results

    def enable_zone(self, zone_name: str) -> bool:
        """

        启用指定乘区



        参数：

            zone_name: 乘区名称



        返回：

            是否成功启用（True/False）

        """

        zone = self.get_zone(zone_name)

        if zone:
            zone.enable()

            return True

        return False

    def disable_zone(self, zone_name: str) -> bool:
        """

        禁用指定乘区



        参数：

            zone_name: 乘区名称



        返回：

            是否成功禁用（True/False）

        """

        zone = self.get_zone(zone_name)

        if zone:
            zone.disable()

            return True

        return False

    def enable_all(self) -> None:
        """启用所有乘区"""

        for zone in self._zones:
            zone.enable()

    def disable_all(self) -> None:
        """禁用所有乘区"""

        for zone in self._zones:
            zone.disable()

    def clear(self) -> None:
        """清空所有乘区"""

        self._zones.clear()

    def __len__(self) -> int:
        """返回注册的乘区数量"""

        return len(self._zones)

    def __repr__(self) -> str:
        """返回管理器的字符串表示"""

        enabled_count = sum(1 for z in self._zones if z.is_enabled())

        return f"<ZoneManager: {len(self._zones)} zones ({enabled_count} enabled)>"
