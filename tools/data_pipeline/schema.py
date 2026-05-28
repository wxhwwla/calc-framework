#!/usr/bin/env python3
"""标准数据契约 — 四层数据模型的 TypedDict 定义。

层次结构（从外到内）：

1. 实体层（EntitySchema）：
   游戏内可独立选中的单位，如角色、武器、装备、坐骑。
   每个实体通过 ``名称`` 在游戏隔离空间内唯一标识。

2. 属性筛选层：
   实体层平铺的 key（如 ``星级``、``类型``、``属性``），
   **不由本 schema 规定**，开发者自由定义。框架只提醒"这里是筛选条件"。

3. 技能层（SkillSchema）：
   实体的各项技能。主动技能（战技/连携技）或被动加成（武器效果）共用此结构，
   通过 ``标签`` 区分。

4. 数值层（SegmentSchema）：
   技能的段——每段有独立的倍率数组和可选的伤害类型覆盖。
   倍率以**整数**存储，``百分比`` 标记告知解析器是否需 ÷100。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, TypedDict

# --- 实体类型常量 ---

STANDARD_ENTITY_TYPES = frozenset({"character", "weapon", "equipment", "mount", "other"})
"""框架建议的实体类型枚举。开发者可以自由扩展。"""

EntityType = str
"""实体类型，如 ``"character"``、``"weapon"``、``"mount"``。"""

# --- 核心数据结构 ---


class SegmentSchema(TypedDict, total=False):
    """第四层：数值层 — 技能的"段"。

    每段有独立的倍率数组和可选的伤害类型。
    倍率以**整数**存储，通过上层的 ``百分比`` 标记决定是否 ÷100。

    字段约定：
    - ``倍率``: 各等级的倍率值（整数列表），索引含义由适配器自解释
    - ``伤害类型``: （可选）覆盖技能级的类型；缺省继承技能级或适配器默认
    """

    倍率: List[int]
    伤害类型: str


class SkillSchema(TypedDict, total=False):
    """第三层：技能层 — 实体的一个技能。

    字段约定：
    - ``名称``: 技能展示名 + 筛选 key。如 ``战技``、``战技:1``、``主能力值+``
    - ``标签``: ``主动`` (倍率类) 或 ``被动`` (加成型)
    - ``百分比``: 倍率是否是百分比值（ture → ÷100，false → 直接使用）
    - ``技能类型``: （可选）技能级伤害类型，作为段级的默认值
    - ``段``: 该技能的各段数值
    """

    名称: str
    标签: str
    百分比: bool
    技能类型: str
    段: List[SegmentSchema]


class EntitySchema(TypedDict, total=False):
    """第一层+第二层：实体层 + 属性筛选层。

    字段约定（L1 — 标识）：
    - ``名称``: 实体在游戏内的唯一标识

    字段约定（L2 — 筛选，由开发者自由定义）：
    - ``星级``: 稀有度/星级（示例字段）
    - ``类型``: 职业/兵种（示例字段）
    - ``属性``: 元素属性（示例字段）
    - ``武器``: 适用武器类型（示例字段）
    - … 任何其他筛选字段均可

    字段约定（L3+L4 技能）：
    - ``技能``: 该实体的所有技能列表

    字段约定（其它）：
    - ``_entity_type``: （可选）实体类型标记，用于管道内部路由
    """

    名称: str
    技能: List[SkillSchema]
    _entity_type: str


# --- 管道中间类型 ---


RawRecord = Dict[str, Any]
"""读取阶段的「原始记录」，key-value 对应 CSV 列或旧 JSON 字段。"""


StandardEntityList = List[EntitySchema]
"""管道最终输出的标准实体列表。"""
