# SPDX-License-Identifier: AGPL-3.0
"""明日方舟 DAG 适配器类型定义。"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SkillSelection:
    """技能选择参数。

    Attributes:
        skill_index: 技能序号（0 开始），默认取第一个
        level: 技能等级（1-10），其中 1-7 = 技能等级1-7，8=专精1，9=专精2，10=专精3
    """

    skill_index: int = 0
    level: int = 7


@dataclass
class SnapshotResult:
    """DAG 求值结果。

    Attributes:
        outputs: 所有输出变量名→值的字典
        execution_order: 节点执行顺序
    """

    outputs: dict[str, float]
    execution_order: list[str]
