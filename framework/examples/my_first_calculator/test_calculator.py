#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试计算器功能。"""

import sys
from pathlib import Path

# 添加框架路径
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from calc_framework.dag import DAGService, dag_from_dict


def clamp(value: float, min_val: float, max_val: float) -> float:
    """将值钳制在 [min_val, max_val] 范围内。"""
    return max(min_val, min(value, max_val))


def test_calculator():
    """测试计算器的完整功能。"""
    print("=" * 60)
    print("测试：我的第一个计算器")
    print("=" * 60)

    # 1. 加载 DAG
    dag_path = Path(__file__).parent / "formula.dag.json"
    import json

    with open(dag_path, encoding="utf-8") as f:
        dag_data = json.load(f)

    dag = dag_from_dict(dag_data)
    service = DAGService(dag)

    # 注册自定义函数
    service.register_function("clamp", clamp)

    print("\n✓ DAG 加载成功")
    print(f"  - 变量数: {len(dag.variables)}")
    print(f"  - 节点数: {len(dag.nodes)}")
    print(f"  - 输出数: {len(dag.outputs)}")

    # 2. 测试场景 1：基础攻击
    print("\n" + "-" * 40)
    print("场景 1：基础攻击（无暴击）")
    context1 = {
        "character": {"ATK": 100, "crit_dmg": 0.5},
        "enemy": {"DEF": 50},
        "user_input": {"skill_mult": 1.0, "is_crit": False},
    }
    result1 = service.evaluate(context1)
    print("  输入: ATK=100, 技能倍率=100%, DEF=50, 无暴击")
    print(f"  输出: {result1.outputs}")
    expected1 = 100 * 1.0 - 50  # = 50
    assert abs(result1.outputs["最终伤害"] - expected1) < 0.001, f"期望 {expected1}"
    print(f"  ✓ 正确: 最终伤害 = {expected1}")

    # 3. 测试场景 2：暴击攻击
    print("\n" + "-" * 40)
    print("场景 2：暴击攻击")
    context2 = {
        "character": {"ATK": 100, "crit_dmg": 0.5},
        "enemy": {"DEF": 50},
        "user_input": {"skill_mult": 1.0, "is_crit": True},
    }
    result2 = service.evaluate(context2)
    print("  输入: ATK=100, 技能倍率=100%, DEF=50, 暴击")
    print(f"  输出: {result2.outputs}")
    expected2 = (100 * 1.0 - 50) * (1 + 0.5)  # = 75
    assert abs(result2.outputs["最终伤害"] - expected2) < 0.001, f"期望 {expected2}"
    print(f"  ✓ 正确: 最终伤害 = {expected2}")

    # 4. 测试场景 3：高倍率技能
    print("\n" + "-" * 40)
    print("场景 3：高倍率技能")
    context3 = {
        "character": {"ATK": 200, "crit_dmg": 1.0},
        "enemy": {"DEF": 100},
        "user_input": {"skill_mult": 3.0, "is_crit": True},
    }
    result3 = service.evaluate(context3)
    print("  输入: ATK=200, 技能倍率=300%, DEF=100, 暴击伤害=100%")
    print(f"  输出: {result3.outputs}")
    expected3 = (200 * 3.0 - 100) * (1 + 1.0)  # = 1000
    assert abs(result3.outputs["最终伤害"] - expected3) < 0.001, f"期望 {expected3}"
    print(f"  ✓ 正确: 最终伤害 = {expected3}")

    # 5. 测试场景 4：防御过高（伤害为 0）
    print("\n" + "-" * 40)
    print("场景 4：防御过高（伤害钳制为 0）")
    context4 = {
        "character": {"ATK": 50, "crit_dmg": 0.5},
        "enemy": {"DEF": 100},
        "user_input": {"skill_mult": 1.0, "is_crit": False},
    }
    result4 = service.evaluate(context4)
    print("  输入: ATK=50, 技能倍率=100%, DEF=100, 无暴击")
    print(f"  输出: {result4.outputs}")
    expected4 = 0  # 50 - 100 = -50 → clamp → 0
    assert abs(result4.outputs["最终伤害"] - expected4) < 0.001, f"期望 {expected4}"
    print(f"  ✓ 正确: 最终伤害 = {expected4}（钳制）")

    # 6. 测试增量求值
    print("\n" + "-" * 40)
    print("场景 5：增量求值（相同上下文）")
    result5 = service.evaluate(context1)
    assert result1.outputs == result5.outputs
    print("  ✓ 增量求值正常（缓存命中）")

    print("\n" + "=" * 60)
    print("✓ 所有测试通过！")
    print("=" * 60)

    return True


if __name__ == "__main__":
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

    try:
        success = test_calculator()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
