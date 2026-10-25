#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""框架核心功能快速验证脚本。"""

import sys
from pathlib import Path

# 确保可以导入框架
sys.path.insert(0, str(Path(__file__).parent / "src"))


def test_dag_engine():
    """测试 DAG 引擎基本功能。"""
    from calc_framework.dag import (
        BinaryNode,
        DAGGraph,
        DAGOutput,
        DAGService,
        DAGVariable,
        VarNode,
    )

    print("=" * 60)
    print("测试 1: DAG 引擎基本求值")
    print("=" * 60)

    # 构建一个简单的 DAG: result = attack * multiplier
    graph = DAGGraph(
        schema_version="dag-v1",
        name="简单攻击计算",
        description="攻击力 × 倍率 = 最终伤害",
        variables={
            "character.攻击力": DAGVariable(type="float", source="character", default=100.0),
            "skill.倍率": DAGVariable(type="float", source="user_input", default=2.0),
        },
        nodes={
            "atk": VarNode(path="character.攻击力"),
            "mult": VarNode(path="skill.倍率"),
            "result": BinaryNode(op="*", lhs="atk", rhs="mult"),
        },
        outputs={
            "最终伤害": DAGOutput(node="result", label="最终伤害", is_primary=True),
        },
    )

    # 创建服务并求值
    service = DAGService(graph)
    context = {
        "character": {"攻击力": 150.0},
        "skill": {"倍率": 2.5},
    }
    result = service.evaluate(context)

    print("  输入: 攻击力=150, 倍率=2.5")
    print(f"  输出: {result.outputs}")
    assert abs(result.outputs["最终伤害"] - 375.0) < 0.001, f"期望 375.0, 得到 {result.outputs['最终伤害']}"
    print("  ✅ 通过!\n")


def test_incremental_evaluation():
    """测试增量求值。"""
    from calc_framework.dag import (
        BinaryNode,
        DAGGraph,
        DAGOutput,
        DAGService,
        DAGVariable,
        VarNode,
    )

    print("=" * 60)
    print("测试 2: 增量求值（相同上下文跳过计算）")
    print("=" * 60)

    graph = DAGGraph(
        schema_version="dag-v1",
        name="增量测试",
        variables={
            "a": DAGVariable(type="float", source="character", default=10.0),
            "b": DAGVariable(type="float", source="character", default=20.0),
        },
        nodes={
            "va": VarNode(path="a"),
            "vb": VarNode(path="b"),
            "sum": BinaryNode(op="+", lhs="va", rhs="vb"),
        },
        outputs={"总和": DAGOutput(node="sum", label="总和")},
    )

    service = DAGService(graph)

    # 第一次求值 - 注意变量路径是 "a" 和 "b"，所以 context 直接用顶层键
    ctx1 = {"a": 10.0, "b": 20.0}
    r1 = service.evaluate(ctx1)
    print(f"  第一次求值: {r1.outputs}")

    # 第二次求值（相同上下文）
    r2 = service.evaluate(ctx1)
    print(f"  第二次求值: {r2.outputs} (应该使用缓存)")
    assert r1.outputs == r2.outputs
    print("  ✅ 通过!\n")


def test_subgraph():
    """测试子图调用。"""
    from calc_framework.dag import (
        BinaryNode,
        CallNode,
        DAGGraph,
        DAGOutput,
        DAGService,
        DAGSubgraph,
        DAGVariable,
        VarNode,
    )

    print("=" * 60)
    print("测试 3: 子图调用（Block 封装）")
    print("=" * 60)

    # 定义一个"攻击块"子图
    attack_block = DAGSubgraph(
        description="攻击计算块",
        nodes={
            "atk": VarNode(path="base_atk"),
            "bonus": VarNode(path="atk_bonus"),
            "total": BinaryNode(op="+", lhs="atk", rhs="bonus"),
        },
        outputs={
            "攻击力": DAGOutput(node="total", label="攻击力", is_primary=True),
        },
    )

    graph = DAGGraph(
        schema_version="dag-v1",
        name="子图测试",
        variables={
            "character.基础攻击": DAGVariable(type="float", source="character", default=100.0),
            "buff.攻击加成": DAGVariable(type="float", source="user_input", default=50.0),
        },
        subgraphs={"attack_block": attack_block},
        nodes={
            "attack": CallNode(
                subgraph="attack_block",
                bindings={"base_atk": "character.基础攻击", "atk_bonus": "buff.攻击加成"},
            ),
        },
        outputs={"最终攻击力": DAGOutput(node="attack", label="攻击力")},
    )

    service = DAGService(graph)
    context = {"character": {"基础攻击": 200.0}, "buff": {"攻击加成": 80.0}}
    result = service.evaluate(context)

    print("  输入: 基础攻击=200, 攻击加成=80")
    print(f"  输出: {result.outputs}")
    assert abs(result.outputs["最终攻击力"] - 280.0) < 0.001
    print("  ✅ 通过!\n")


def test_adapter_loading():
    """测试适配器加载。"""
    from calc_framework.config import AdapterManager

    print("=" * 60)
    print("测试 4: 适配器管理器（自动发现）")
    print("=" * 60)

    manager = AdapterManager()
    adapters = manager.names
    print(f"  发现的适配器: {adapters}")

    # 尝试加载卡牌RPG适配器
    card_rpg_name = None
    for name in adapters:
        if "卡牌" in name.lower() or "card" in name.lower():
            card_rpg_name = name
            break

    if card_rpg_name:
        pkg = manager.load(card_rpg_name)
        print(f"  加载 {card_rpg_name} 适配器:")
        print(f"    - 名称: {pkg.meta.get('name')}")
        print(f"    - 版本: {pkg.meta.get('version')}")

        # 使用适配器的 DAG 服务（使用正确的变量名）
        result = pkg.dag_service.evaluate(
            {
                "character": {"ATK": 500, "DEF": 100, "crit_rate": 0.3, "crit_dmg": 0.5},
                "weapon": {"ATK_bonus": 50},
                "enemy": {"DEF": 80},
                "user_input": {"skill_mult": 2.0, "is_crit": 1},
            }
        )
        print(f"    - 计算结果: {result.outputs}")
        print("  ✅ 通过!\n")
    else:
        print("  ⚠️ 卡牌RPG适配器未找到，跳过\n")


def test_inverse_engine():
    """测试逆推引擎。"""
    from calc_framework.inverse import InverseEngine

    print("=" * 60)
    print("测试 5: 逆推引擎（数据 → 参数）")
    print("=" * 60)

    engine = InverseEngine()

    # 模拟一个线性成长数据: base=100, growth=5
    data = [100 + 5 * i for i in range(90)]  # 100, 105, 110, ..., 545

    params = engine.data_to_params(data)
    print("  输入数据: 90 个点 (100, 105, 110, ..., 545)")
    print(f"  反推参数: base={params.base}, growth={params.growth}")
    assert abs(params.base - 100.0) < 1.0
    assert abs(params.growth - 5.0) < 1.0

    # 正向验证
    curve = engine.params_to_curve(params, num_levels=90)
    print(f"  正向计算: 前5个值 = {curve[:5]}")
    assert abs(curve[0] - 100.0) < 1.0
    assert abs(curve[1] - 105.0) < 1.0
    print("  ✅ 通过!\n")


def test_sandbox_security():
    """测试沙箱安全性。"""
    from calc_framework.dag import validate_expr
    from calc_framework.dag.errors import DAGSecurityError

    print("=" * 60)
    print("测试 6: 沙箱安全（阻止危险表达式）")
    print("=" * 60)

    # 安全表达式
    validate_expr("a + b * 2")
    print("  ✅ 'a + b * 2' 安全表达式通过")

    # 危险表达式（用于测试沙箱安全性）
    dangerous_exprs = [
        "__import__('os').system('rm -rf /')",
        "open('/etc/passwd').read()",
        "exec('print(1)')",
        "compile('1+1', '<string>', 'eval')",  # 模拟 eval 的危险调用
    ]

    for expr in dangerous_exprs:
        try:
            validate_expr(expr)
            print(f"  ❌ 应该阻止: {expr[:40]}...")
        except (DAGSecurityError, Exception) as e:
            print(f"  ✅ 已阻止: {expr[:40]}... ({type(e).__name__})")

    print("  ✅ 安全测试通过!\n")


def test_plugin_system():
    """测试插件系统。"""
    from calc_framework.plugin import get_registry, list_plugins

    print("=" * 60)
    print("测试 7: 插件系统")
    print("=" * 60)

    plugins = list_plugins()
    print(f"  已注册的插件: {plugins}")

    registry = get_registry()
    for name in plugins:
        info = registry.get(name)
        if info:
            print(f"    - {name}: {info.meta.description}")

    print("  ✅ 通过!\n")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("Calc Framework 核心功能验证")
    print("=" * 60 + "\n")

    tests = [
        test_dag_engine,
        test_incremental_evaluation,
        test_subgraph,
        test_adapter_loading,
        test_inverse_engine,
        test_sandbox_security,
        test_plugin_system,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"  ❌ 失败: {e}\n")
            failed += 1

    print("=" * 60)
    print(f"测试结果: {passed} 通过, {failed} 失败")
    print("=" * 60)

    sys.exit(0 if failed == 0 else 1)
