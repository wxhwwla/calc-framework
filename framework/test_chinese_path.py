#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试中文变量路径支持。"""

import sys

sys.path.insert(0, "src")

from calc_framework.dag import (
    BinaryNode,
    DAGGraph,
    DAGOutput,
    DAGService,
    DAGVariable,
    VarNode,
)

print("=" * 60)
print("测试中文变量路径支持")
print("=" * 60)

# 创建使用中文路径的 DAG
graph = DAGGraph(
    schema_version="dag-v1",
    name="中文路径测试",
    variables={
        "character.攻击力": DAGVariable(type="float", source="character", default=500.0),
        "character.暴击伤害": DAGVariable(type="float", source="character", default=0.5),
        "enemy.防御力": DAGVariable(type="float", source="enemy", default=100.0),
        "user_input.技能倍率": DAGVariable(type="float", source="user_input", default=2.0),
    },
    nodes={
        "atk": VarNode(path="character.攻击力", label="攻击力"),
        "crit": VarNode(path="character.暴击伤害", label="暴击伤害"),
        "def": VarNode(path="enemy.防御力", label="防御力"),
        "mult": VarNode(path="user_input.技能倍率", label="技能倍率"),
        "dmg": BinaryNode(op="*", lhs="atk", rhs="mult", label="攻击力×倍率"),
        "final": BinaryNode(op="-", lhs="dmg", rhs="def", label="最终伤害"),
    },
    outputs={
        "最终伤害": DAGOutput(node="final", label="最终伤害", is_primary=True),
    },
)

# 创建服务
service = DAGService(graph)

# 测试 1：使用中文键的上下文
print("\n测试 1：使用中文键的上下文")
context1 = {
    "character": {"攻击力": 800, "暴击伤害": 0.8},
    "enemy": {"防御力": 200},
    "user_input": {"技能倍率": 3.0},
}
result1 = service.evaluate(context1)
print("  输入: 攻击力=800, 技能倍率=3.0, 防御力=200")
print(f"  输出: {result1.outputs}")
expected1 = 800 * 3.0 - 200  # = 2200
assert abs(result1.outputs["最终伤害"] - expected1) < 0.001
print(f"  ✓ 正确: 最终伤害 = {expected1}")

# 测试 2：使用英文键的上下文（应该使用默认值）
print("\n测试 2：使用英文键的上下文（使用默认值）")
context2 = {
    "character": {"ATK": 999},  # 这个键不匹配，会使用默认值
    "enemy": {"DEF": 999},
    "user_input": {"skill_mult": 999},
}
result2 = service.evaluate(context2)
print("  输入: 使用英文键（不匹配中文路径）")
print(f"  输出: {result2.outputs}")
# 应该使用默认值: 500 * 2.0 - 100 = 900
expected2 = 500 * 2.0 - 100
assert abs(result2.outputs["最终伤害"] - expected2) < 0.001
print(f"  ✓ 正确: 使用默认值，最终伤害 = {expected2}")

# 测试 3：混合中英文
print("\n测试 3：混合中英文键")
context3 = {
    "character": {"攻击力": 1000},  # 中文键
    "enemy": {"防御力": 300},  # 中文键
    "user_input": {"技能倍率": 1.5},  # 中文键
}
result3 = service.evaluate(context3)
print("  输入: 攻击力=1000, 技能倍率=1.5, 防御力=300")
print(f"  输出: {result3.outputs}")
expected3 = 1000 * 1.5 - 300  # = 1200
assert abs(result3.outputs["最终伤害"] - expected3) < 0.001
print(f"  ✓ 正确: 最终伤害 = {expected3}")

print("\n" + "=" * 60)
print("✓ 所有中文路径测试通过！")
print("=" * 60)
print("\n结论：")
print("  - 变量路径支持中文：character.攻击力 ✅")
print("  - 上下文键支持中文：{'character': {'攻击力': 800}} ✅")
print("  - 节点标签支持中文：'label': '攻击力×倍率' ✅")
print("  - 输出标签支持中文：'最终伤害' ✅")
