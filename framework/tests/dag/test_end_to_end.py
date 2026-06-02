#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""端到端验证：用真实伤害公式验证 GraphCompiler + DAGService 流水线。"""

import tempfile
from pathlib import Path

from calc_framework.graph_editor.compiler import (
    dag_service_from_graph_document,
    dag_service_from_graph_file,
)
from calc_framework.graph_editor.schema import (
    GraphDocument,
    GraphEdge,
    GraphLayout,
    GraphNode,
    NodeConfig,
    SectionDef,
)
from calc_framework.graph_editor.serializer import document_to_json


class TestEndToEndAttackChain:
    """最终攻击力链：完整流水线验证。

    公式: 最终攻击 = (角色基础 + 武器基础) × (1 + 攻击力+) + 能力值加成
    """

    def _build_attack_doc(self, char_base: float, weapon_base: float, atk_pct: float,
                          ability_bonus: float) -> GraphDocument:
        return GraphDocument(
            name="攻击力链验证",
            external_variables={
                "character.基础攻击": {"type": "float", "source": "character"},
                "weapon.基础攻击": {"type": "float", "source": "weapon"},
                "weapon.攻击力+": {"type": "float", "source": "weapon"},
                "computed.能力值加成": {"type": "float", "source": "computed"},
            },
            nodes=[
                # 输入节点
                GraphNode(id="char_atk", type="var", label="角色基础",
                          config=NodeConfig(path="character.基础攻击")),
                GraphNode(id="wp_atk", type="var", label="武器基础",
                          config=NodeConfig(path="weapon.基础攻击")),
                GraphNode(id="atk_pct", type="var", label="攻击力百分比",
                          config=NodeConfig(path="weapon.攻击力+")),
                GraphNode(id="abil", type="var", label="能力值加成",
                          config=NodeConfig(path="computed.能力值加成")),
                # 计算节点
                GraphNode(id="base_sum", type="binary", op="+", label="基础攻击和"),
                GraphNode(id="one", type="const", label="1",
                          config=NodeConfig(value=1.0)),
                GraphNode(id="one_plus_atkpct", type="binary", op="+", label="1+攻击力%"),
                GraphNode(id="base_times_mod", type="binary", op="*", label="基础×系数"),
                GraphNode(id="final_atk", type="binary", op="+", label="最终攻击"),
            ],
            edges=[
                # base_sum = char_base + weapon_base
                GraphEdge(from_node="char_atk", from_port=0, to_node="base_sum", to_port=0),
                GraphEdge(from_node="wp_atk", from_port=0, to_node="base_sum", to_port=1),
                # one_plus_atkpct = 1 + atk_pct
                GraphEdge(from_node="one", from_port=0, to_node="one_plus_atkpct", to_port=0),
                GraphEdge(from_node="atk_pct", from_port=0, to_node="one_plus_atkpct", to_port=1),
                # base_times_mod = base_sum * one_plus_atkpct
                GraphEdge(from_node="base_sum", from_port=0, to_node="base_times_mod", to_port=0),
                GraphEdge(from_node="one_plus_atkpct", from_port=0, to_node="base_times_mod", to_port=1),
                # final_atk = base_times_mod + ability_bonus
                GraphEdge(from_node="base_times_mod", from_port=0, to_node="final_atk", to_port=0),
                GraphEdge(from_node="abil", from_port=0, to_node="final_atk", to_port=1),
            ],
            # 输出标记
            layout=GraphLayout(sections=[SectionDef(id="r", title="最终攻击", output_nodes=["final_atk"])]),
        )

    def test_attack_chain_direct(self) -> None:
        doc = self._build_attack_doc(500, 300, 0.15, 50)
        svc = dag_service_from_graph_document(doc)
        res = svc.evaluate({
            "character": {"基础攻击": 500},
            "weapon": {"基础攻击": 300, "攻击力+": 0.15},
            "computed": {"能力值加成": 50},
        })
        # (500+300) * (1+0.15) + 50 = 800*1.15 + 50 = 920+50 = 970
        assert abs(res.outputs["final_atk"] - 970.0) < 1e-9

    def test_attack_chain_via_file(self) -> None:
        doc = self._build_attack_doc(1000, 200, 0.20, 100)
        json_str = document_to_json(doc)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
            f.write(json_str)
            f.flush()
            fname = Path(f.name)

        try:
            svc = dag_service_from_graph_file(fname)
            res = svc.evaluate({
                "character": {"基础攻击": 1000},
                "weapon": {"基础攻击": 200, "攻击力+": 0.20},
                "computed": {"能力值加成": 100},
            })
            # (1000+200) * (1+0.20) + 100 = 1200*1.2 + 100 = 1440+100 = 1540
            assert abs(res.outputs["final_atk"] - 1540.0) < 1e-9
        finally:
            if fname.exists():
                fname.unlink()

    def test_attack_chain_with_unary(self) -> None:
        """含取整操作：floor(最终攻击)"""
        doc = GraphDocument(
            name="取整测试",
            external_variables={"x": {"type": "float", "source": "computed"}},
            nodes=[
                GraphNode(id="v", type="var", config=NodeConfig(path="x")),
                GraphNode(id="floor", type="unary", op="floor", label="向下取整"),
            ],
            edges=[GraphEdge(from_node="v", from_port=0, to_node="floor", to_port=0)],
            layout=GraphLayout(sections=[SectionDef(id="r", title="结果", output_nodes=["floor"])]),
        )
        svc = dag_service_from_graph_document(doc)
        res = svc.evaluate({"x": 42.7})
        assert res.outputs["floor"] == 42.0


class TestEndToEndDamageFormula:
    """简化版最终伤害公式验证。

    伤害 = (攻击力 × 技能倍率) × (1 + 伤害加成) × (1 - 减免) × 防御减伤
    """

    def test_damage_pipeline(self) -> None:
        doc = GraphDocument(
            name="伤害公式流水线",
            external_variables={
                "computed.atk": {"type": "float", "source": "computed"},
                "computed.skill_mult": {"type": "float", "source": "computed"},
                "computed.dmg_bonus": {"type": "float", "source": "computed"},
                "computed.dmg_reduce": {"type": "float", "source": "computed"},
                "computed.def_mult": {"type": "float", "source": "computed"},
            },
            nodes=[
                GraphNode(id="atk_var", type="var", config=NodeConfig(path="computed.atk")),
                GraphNode(id="skill_var", type="var", config=NodeConfig(path="computed.skill_mult")),
                GraphNode(id="bonus_var", type="var", config=NodeConfig(path="computed.dmg_bonus")),
                GraphNode(id="reduce_var", type="var", config=NodeConfig(path="computed.dmg_reduce")),
                GraphNode(id="def_var", type="var", config=NodeConfig(path="computed.def_mult")),

                GraphNode(id="base_dmg", type="binary", op="*", label="基础伤害"),
                GraphNode(id="bonus_mult", type="binary", op="*", label="伤害加成乘区"),
                GraphNode(id="reduce_mult", type="binary", op="*", label="减免乘区"),
                GraphNode(id="final_dmg", type="binary", op="*", label="最终伤害"),

                GraphNode(id="one", type="const", config=NodeConfig(value=1.0)),
                GraphNode(id="bonus_sum", type="binary", op="+", label="1+加成"),
                GraphNode(id="reduce_neg", type="binary", op="-", label="1-减免"),
            ],
            edges=[
                # base_dmg = atk * skill_mult
                GraphEdge(from_node="atk_var", from_port=0, to_node="base_dmg", to_port=0),
                GraphEdge(from_node="skill_var", from_port=0, to_node="base_dmg", to_port=1),
                # bonus_sum = 1 + dmg_bonus
                GraphEdge(from_node="one", from_port=0, to_node="bonus_sum", to_port=0),
                GraphEdge(from_node="bonus_var", from_port=0, to_node="bonus_sum", to_port=1),
                # bonus_mult = base_dmg * bonus_sum
                GraphEdge(from_node="base_dmg", from_port=0, to_node="bonus_mult", to_port=0),
                GraphEdge(from_node="bonus_sum", from_port=0, to_node="bonus_mult", to_port=1),
                # reduce_neg = 1 - dmg_reduce
                GraphEdge(from_node="one", from_port=0, to_node="reduce_neg", to_port=0),
                GraphEdge(from_node="reduce_var", from_port=0, to_node="reduce_neg", to_port=1),
                # reduce_mult = bonus_mult * reduce_neg
                GraphEdge(from_node="bonus_mult", from_port=0, to_node="reduce_mult", to_port=0),
                GraphEdge(from_node="reduce_neg", from_port=0, to_node="reduce_mult", to_port=1),
                # final_dmg = reduce_mult * def_mult
                GraphEdge(from_node="reduce_mult", from_port=0, to_node="final_dmg", to_port=0),
                GraphEdge(from_node="def_var", from_port=0, to_node="final_dmg", to_port=1),
            ],
            layout=GraphLayout(sections=[SectionDef(id="r", title="最终伤害", output_nodes=["final_dmg"])]),
        )

        svc = dag_service_from_graph_document(doc)
        res = svc.evaluate({
            "computed": {
                "atk": 1500.0,
                "skill_mult": 2.5,
                "dmg_bonus": 0.3,
                "dmg_reduce": 0.1,
                "def_mult": 0.5,
            },
        })
        # 1500*2.5 = 3750
        # 3750 * (1+0.3) = 4875
        # 4875 * (1-0.1) = 4387.5
        # 4387.5 * 0.5 = 2193.75
        expected = ((1500.0 * 2.5) * (1 + 0.3)) * (1 - 0.1) * 0.5
        assert abs(res.outputs["final_dmg"] - expected) < 1e-9


class TestEndToEndEdgeCases:
    def test_floor_after_division(self) -> None:
        """ceil、floor、neg、abs、sqrt 等一元运算"""
        doc = GraphDocument(
            name="一元运算全测",
            nodes=[
                GraphNode(id="input", type="const", config=NodeConfig(value=-4.7)),
                GraphNode(id="neg", type="unary", op="neg", label="取反"),
                GraphNode(id="abs", type="unary", op="abs", label="绝对值"),
                GraphNode(id="floor", type="unary", op="floor", label="向下"),
                GraphNode(id="ceil", type="unary", op="ceil", label="向上"),
                GraphNode(id="sqrt_n", type="unary", op="sqrt", label="平方根"),
            ],
            edges=[
                GraphEdge(from_node="input", from_port=0, to_node="neg", to_port=0),
                GraphEdge(from_node="neg", from_port=0, to_node="abs", to_port=0),
                GraphEdge(from_node="abs", from_port=0, to_node="floor", to_port=0),
                GraphEdge(from_node="floor", from_port=0, to_node="ceil", to_port=0),
                GraphEdge(from_node="ceil", from_port=0, to_node="sqrt_n", to_port=0),
            ],
            layout=GraphLayout(sections=[SectionDef(id="r", title="平方根", output_nodes=["sqrt_n"])]),
        )
        svc = dag_service_from_graph_document(doc)
        res = svc.evaluate({})
        # -(-4.7) = 4.7 → abs = 4.7 → floor = 4 → ceil = 4 → sqrt = 2
        assert res.outputs["sqrt_n"] == 2.0

    def test_mod_operation(self) -> None:
        doc = GraphDocument(
            name="取模",
            nodes=[
                GraphNode(id="a", type="const", config=NodeConfig(value=17)),
                GraphNode(id="b", type="const", config=NodeConfig(value=5)),
                GraphNode(id="mod", type="binary", op="mod", label="取模"),
            ],
            edges=[
                GraphEdge(from_node="a", from_port=0, to_node="mod", to_port=0),
                GraphEdge(from_node="b", from_port=0, to_node="mod", to_port=1),
            ],
            layout=GraphLayout(sections=[SectionDef(id="r", title="结果", output_nodes=["mod"])]),
        )
        svc = dag_service_from_graph_document(doc)
        res = svc.evaluate({})
        assert res.outputs["mod"] == 2.0  # 17 % 5 = 2

    def test_condition_selects_true(self) -> None:
        doc = GraphDocument(
            name="条件真值",
            nodes=[
                GraphNode(id="flag", type="const", config=NodeConfig(value=1)),
                GraphNode(id="t", type="const", config=NodeConfig(value=999)),
                GraphNode(id="f", type="const", config=NodeConfig(value=-1)),
                GraphNode(id="cond", type="condition", label="条件"),
            ],
            edges=[
                GraphEdge(from_node="flag", from_port=0, to_node="cond", to_port=0),
                GraphEdge(from_node="t", from_port=0, to_node="cond", to_port=1),
                GraphEdge(from_node="f", from_port=0, to_node="cond", to_port=2),
            ],
            layout=GraphLayout(sections=[SectionDef(id="r", title="结果", output_nodes=["cond"])]),
        )
        svc = dag_service_from_graph_document(doc)
        res = svc.evaluate({})
        assert res.outputs["cond"] == 999.0

    def test_chain_with_output_marker(self) -> None:
        """output 标记节点在中间位置也能正确回溯。"""
        doc = GraphDocument(
            name="输出标记链",
            nodes=[
                GraphNode(id="a", type="const", config=NodeConfig(value=10)),
                GraphNode(id="b", type="const", config=NodeConfig(value=20)),
                GraphNode(id="add", type="binary", op="+", label="加法"),
                GraphNode(id="out", type="output", label="输出"),
            ],
            edges=[
                GraphEdge(from_node="a", from_port=0, to_node="add", to_port=0),
                GraphEdge(from_node="b", from_port=0, to_node="add", to_port=1),
                GraphEdge(from_node="add", from_port=0, to_node="out", to_port=0),
            ],
            layout=GraphLayout(sections=[SectionDef(id="r", title="和", output_nodes=["out"])]),
        )
        svc = dag_service_from_graph_document(doc)
        res = svc.evaluate({})
        assert res.outputs["add"] == 30.0


class TestExtendedOps:
    """Phase 5: 扩展操作符（三角函数、对数）端到端测试。"""

    def test_ln_log10(self) -> None:
        """ln(e) = 1, log10(100) = 2"""
        doc = GraphDocument(
            name="对数",
            nodes=[
                GraphNode(id="val_e", type="const", config=NodeConfig(value=2.718281828)),
                GraphNode(id="ln_op", type="unary", op="ln", label="自然对数"),
                GraphNode(id="val_100", type="const", config=NodeConfig(value=100)),
                GraphNode(id="log10_op", type="unary", op="log10", label="常用对数"),
            ],
            edges=[
                GraphEdge(from_node="val_e", from_port=0, to_node="ln_op", to_port=0),
                GraphEdge(from_node="val_100", from_port=0, to_node="log10_op", to_port=0),
            ],
            layout=GraphLayout(sections=[
                SectionDef(id="r1", title="ln", output_nodes=["ln_op"]),
                SectionDef(id="r2", title="log10", output_nodes=["log10_op"]),
            ]),
        )
        svc = dag_service_from_graph_document(doc)
        res = svc.evaluate({})
        assert abs(res.outputs["ln_op"] - 1.0) < 1e-4
        assert abs(res.outputs["log10_op"] - 2.0) < 1e-9

    def test_sin_cos_tan(self) -> None:
        """sin(0)=0, cos(0)=1, tan(π/4)=1"""
        import math
        doc = GraphDocument(
            name="三角函数",
            nodes=[
                GraphNode(id="val_0", type="const", config=NodeConfig(value=0)),
                GraphNode(id="sin_op", type="unary", op="sin", label="正弦"),
                GraphNode(id="cos_op", type="unary", op="cos", label="余弦"),
                GraphNode(id="val_pi4", type="const", config=NodeConfig(value=math.pi / 4)),
                GraphNode(id="tan_op", type="unary", op="tan", label="正切"),
            ],
            edges=[
                GraphEdge(from_node="val_0", from_port=0, to_node="sin_op", to_port=0),
                GraphEdge(from_node="val_0", from_port=0, to_node="cos_op", to_port=0),
                GraphEdge(from_node="val_pi4", from_port=0, to_node="tan_op", to_port=0),
            ],
            layout=GraphLayout(sections=[
                SectionDef(id="r1", title="sin", output_nodes=["sin_op"]),
                SectionDef(id="r2", title="cos", output_nodes=["cos_op"]),
                SectionDef(id="r3", title="tan", output_nodes=["tan_op"]),
            ]),
        )
        svc = dag_service_from_graph_document(doc)
        res = svc.evaluate({})
        assert abs(res.outputs["sin_op"]) < 1e-9
        assert abs(res.outputs["cos_op"] - 1.0) < 1e-9
        assert abs(res.outputs["tan_op"] - 1.0) < 1e-9

    def test_extended_ops_chain(self) -> None:
        """链式：ln(10) + sin(π/2) * cos(0)"""
        import math
        doc = GraphDocument(
            name="扩展链式",
            nodes=[
                GraphNode(id="val_10", type="const", config=NodeConfig(value=10)),
                GraphNode(id="ln_op", type="unary", op="ln", label="ln"),
                GraphNode(id="val_pi2", type="const", config=NodeConfig(value=math.pi / 2)),
                GraphNode(id="sin_op", type="unary", op="sin", label="sin"),
                GraphNode(id="val_0", type="const", config=NodeConfig(value=0)),
                GraphNode(id="cos_op", type="unary", op="cos", label="cos"),
                GraphNode(id="mul", type="binary", op="*", label="乘法"),
                GraphNode(id="add", type="binary", op="+", label="求和"),
            ],
            edges=[
                GraphEdge(from_node="val_10", from_port=0, to_node="ln_op", to_port=0),
                GraphEdge(from_node="val_pi2", from_port=0, to_node="sin_op", to_port=0),
                GraphEdge(from_node="val_0", from_port=0, to_node="cos_op", to_port=0),
                GraphEdge(from_node="sin_op", from_port=0, to_node="mul", to_port=0),
                GraphEdge(from_node="cos_op", from_port=0, to_node="mul", to_port=1),
                GraphEdge(from_node="ln_op", from_port=0, to_node="add", to_port=0),
                GraphEdge(from_node="mul", from_port=0, to_node="add", to_port=1),
            ],
            layout=GraphLayout(sections=[SectionDef(id="r", title="求和", output_nodes=["add"])]),
        )
        svc = dag_service_from_graph_document(doc)
        res = svc.evaluate({})
        # ln(10) + sin(π/2)*cos(0) = ln(10) + 1*1 = ln(10) + 1
        assert abs(res.outputs["add"] - (math.log(10) + 1.0)) < 1e-9

    def test_asin_acos_atan(self) -> None:
        """asin(0)=0, acos(1)=0, atan(1)=π/4"""
        import math
        doc = GraphDocument(
            name="反三角",
            nodes=[
                GraphNode(id="v0", type="const", config=NodeConfig(value=0)),
                GraphNode(id="v1", type="const", config=NodeConfig(value=1)),
                GraphNode(id="asin_op", type="unary", op="asin"),
                GraphNode(id="acos_op", type="unary", op="acos"),
                GraphNode(id="atan_op", type="unary", op="atan"),
            ],
            edges=[
                GraphEdge(from_node="v0", to_node="asin_op"),
                GraphEdge(from_node="v1", to_node="acos_op"),
                GraphEdge(from_node="v1", to_node="atan_op"),
            ],
            layout=GraphLayout(sections=[
                SectionDef(id="r1", title="asin", output_nodes=["asin_op"]),
                SectionDef(id="r2", title="acos", output_nodes=["acos_op"]),
                SectionDef(id="r3", title="atan", output_nodes=["atan_op"]),
            ]),
        )
        svc = dag_service_from_graph_document(doc)
        res = svc.evaluate({})
        assert abs(res.outputs["asin_op"]) < 1e-9
        assert abs(res.outputs["acos_op"]) < 1e-9
        assert abs(res.outputs["atan_op"] - math.pi / 4) < 1e-9


class TestSandboxFunctions:
    """Phase 5: 沙箱注册函数（sum/avg/count/integral）通过 expr 节点求值。"""

    def test_sum_avg_count(self) -> None:
        from calc_framework.dag.engine import evaluate_graph
        from calc_framework.dag.schema import validate_graph

        dag = validate_graph({
            "schema_version": "dag-v1",
            "name": "统计测试",
            "nodes": {
                "r_sum": {"type": "expr", "expr": "sum(1, 2, 3, 4, 5)", "inputs": {}},
                "r_avg": {"type": "expr", "expr": "avg(10, 20, 30)", "inputs": {}},
                "r_cnt": {"type": "expr", "expr": "count(1, 2, 3)", "inputs": {}},
            },
            "outputs": {
                "o_sum": {"node": "r_sum", "label": "和"},
                "o_avg": {"node": "r_avg", "label": "平均"},
                "o_cnt": {"node": "r_cnt", "label": "数量"},
            },
        })
        res = evaluate_graph(dag, {})
        assert res.outputs["o_sum"] == 15.0
        assert res.outputs["o_avg"] == 20.0
        assert res.outputs["o_cnt"] == 3.0

    def test_integral_registered_function(self) -> None:
        """通过 register_function 注册平方函数，积分 ∫₀¹ x² dx = 1/3"""
        from calc_framework.dag.engine import evaluate_graph
        from calc_framework.dag.sandbox import clear_functions, register_function
        from calc_framework.dag.schema import validate_graph

        clear_functions()
        register_function("square", lambda x: x * x)

        dag = validate_graph({
            "schema_version": "dag-v1",
            "name": "积分测试",
            "nodes": {
                "r": {"type": "expr", "expr": "integral(\"square\", 0, 1, 100)", "inputs": {}},
            },
            "outputs": {
                "o": {"node": "r", "label": "积分"},
            },
        })
        res = evaluate_graph(dag, {})
        # ∫₀¹ x² dx = [x³/3]₀¹ = 1/3
        assert abs(res.outputs["o"] - 1.0 / 3.0) < 1e-4
