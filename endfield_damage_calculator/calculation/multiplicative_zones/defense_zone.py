#!/usr/bin/env python3
"""
防御减伤区模块

实现敌方默认防御乘区的计算逻辑。

计算公式：100 / (防御 + 100)

参数：
    defense: 敌方防御值（默认 100，≥ 0）
"""

from .base_zone import BaseZone


class DefenseReductionZone(BaseZone):
    """
    敌方默认防御减伤区

    计算敌方防御对伤害的减伤倍率。

    公式：100 / (防御 + 100)

    属性：
        default_defense: 默认防御值（100）
    """

    DEFAULT_DEFENSE = 100  # 默认防御值

    def __init__(self):
        """
        初始化防御减伤区

        默认防御值为 100。
        """
        super().__init__(name="敌方防御减伤区", description="敌方防御对伤害的减伤倍率，公式：100 / (防御 + 100)")
        # 设置默认参数
        self.set_params(defense=self.DEFAULT_DEFENSE)

    def calculate(self) -> float:
        """
        计算防御减伤乘数

        返回：
            减伤乘数值（float），范围 (0, 1]

        公式：
            100 / (防御 + 100)

        防御值限制：
            如果防御 < 0，视为 0
        """
        defense = self._params.get("defense", self.DEFAULT_DEFENSE)

        # 防御值不能小于 0
        if defense < 0:
            defense = 0

        # 计算减伤倍率
        return 100.0 / (defense + 100.0)

    def get_defense(self) -> int:
        """
        获取当前防御值

        返回：
            当前防御值（int）
        """
        return self._params.get("defense", self.DEFAULT_DEFENSE)

    def set_defense(self, defense: int) -> None:
        """
        设置防御值

        参数：
            defense: 敌方防御值（≥ 0）

        注意：
            如果传入负数，实际会被视为 0
        """
        self.set_params(defense=defense)

    def __str__(self) -> str:
        """返回乘区的可读字符串表示"""
        return f"{self.name}: 防御={self.get_defense()}, 减伤倍率={self.calculate():.4f}"
