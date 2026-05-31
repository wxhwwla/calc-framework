#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""
乘区基础类模块

定义所有乘区的基类和相关类型提示。
"""

from abc import ABC, abstractmethodfrom typing import Anyclass BaseZone(ABC):
    """
    乘区基类（抽象类）

    所有具体乘区都需要继承此类并实现 calculate 方法。

    属性：
        name: 乘区名称（用于标识和调试）
        description: 乘区描述（用于文档说明）
        enabled: 是否启用该乘区（默认启用）

    方法：
        calculate: 计算该乘区的乘数（抽象方法，子类必须实现）
        get_params: 获取当前参数配置
        set_params: 设置参数配置
    """

    def __init__(self, name: str, description: str = ""):
        """
        初始化乘区

        参数：
            name: 乘区名称
            description: 乘区描述（可选）
        """
        self.name: str = name
        self.description: str = description
        self.enabled: bool = True
        self._params: dict[str, Any] = {}

    @abstractmethod
    def calculate(self) -> float:
        """
        计算该乘区的乘数

        返回：
            乘数值（float），用于最终伤害计算的乘法因子

        子类必须实现此方法。
        """
        pass

    def get_params(self) -> dict[str, Any]:
        """
        获取当前参数配置

        返回：
            参数字典
        """
        return self._params.copy()

    def set_params(self, **kwargs) -> None:
        """
        设置参数配置

        参数：
            **kwargs: 关键字参数，用于配置乘区计算所需的参数

        示例：
            zone.set_params(attack_power=1000, skill_level=5)
        """
        self._params.update(kwargs)

    def enable(self) -> None:
        """启用该乘区"""
        self.enabled = True

    def disable(self) -> None:
        """禁用该乘区（计算时返回 1.0）"""
        self.enabled = False

    def is_enabled(self) -> bool:
        """检查乘区是否启用"""
        return self.enabled

    def __repr__(self) -> str:
        """返回乘区的字符串表示"""
        status = "enabled" if self.enabled else "disabled"
        return f"<{self.__class__.__name__}: {self.name} ({status})>"

    def __str__(self) -> str:
        """返回乘区的可读字符串表示"""
        return f"{self.name}: {self.description}"


class DefenseReductionZone(BaseZone):
    """敌方默认防御减伤区。

    计算敌方防御对伤害的减伤倍率。
    公式：100 / (防御 + 100)
    """

    DEFAULT_DEFENSE = 100

    def __init__(self):
        super().__init__(
            name="敌方防御减伤区",
            description="敌方防御对伤害的减伤倍率，公式：100 / (防御 + 100)",
        )
        self.set_params(defense=self.DEFAULT_DEFENSE)

    def calculate(self) -> float:
        defense = self._params.get("defense", self.DEFAULT_DEFENSE)
        if defense < 0:
            defense = 0
        return 100.0 / (defense + 100.0)

    def get_defense(self) -> int:
        return self._params.get("defense", self.DEFAULT_DEFENSE)

    def set_defense(self, defense: int) -> None:
        self.set_params(defense=defense)

    def __str__(self) -> str:
        return f"{self.name}: 防御={self.get_defense()}, 减伤倍率={self.calculate():.4f}"
