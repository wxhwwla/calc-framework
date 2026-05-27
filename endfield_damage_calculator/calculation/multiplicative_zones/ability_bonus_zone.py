#!/usr/bin/env python3
"""能力值加成乘区：Zone 类定义。"""

from .base_zone import BaseZone


class AbilityBonusZone(BaseZone):
    """
    能力值加成乘区

    根据角色的主能力和副能力计算额外的攻击力加成。
    """

    def __init__(self):
        super().__init__(name="能力值加成", description="主能力×0.005 + 副能力×0.002")

    def calculate(self) -> float:
        """
        计算能力值加成

        公式：main_value×(1+main_pct/100)×0.005 + sub_value×(1+sub_pct/100)×0.002

        返回：
            能力值加成值（float）
        """
        main_value = self._params.get("main_value", 0.0)
        sub_value = self._params.get("sub_value", 0.0)
        main_pct = self._params.get("main_pct", 0.0)
        sub_pct = self._params.get("sub_pct", 0.0)
        return (
            main_value * (1.0 + main_pct / 100.0) * 0.005
            + sub_value * (1.0 + sub_pct / 100.0) * 0.002
        )
