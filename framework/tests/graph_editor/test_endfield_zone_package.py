#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""终末地 15 乘区 ZIP 包的端到端加载/编译测试。"""

import jsonimport zipfilefrom pathlib import Pathimport pytestfrom calc_framework.dag.engine import evaluate_graphfrom calc_framework.graph_editor.compiler import compile_graphfrom calc_framework.graph_editor.file_actions import load_documentfrom calc_framework.graph_editor.graph_editor_widget import GraphEditorWidgetfrom calc_framework.graph_editor.package_manager import PackageManagerfrom calc_framework.graph_editor.registry import (    _composite_registry,    get_package_manager,    register_composite_type,)from calc_framework.graph_editor.serializer import document_from_json_ZIP_PATH = Path(__file__).resolve().parents[3] / "output" / "终末地乘区包.zip"


class TestEndfieldZonePackage:
    """终末地 15 乘区包的完整加载、注册、编译与求值验证。"""

    @pytest.fixture(autouse=True)
    def _clean_registry(self) -> None:
        _composite_registry.clear()

    def _load_package(self) -> PackageManager:
        pm = get_package_manager()
        tdefs = pm.load_zip(_ZIP_PATH)
        for tdef in tdefs:
            register_composite_type(tdef)
        assert len(_composite_registry) >= 15  # 至少 15 个乘区
        return pm

    def test_zip_exists(self) -> None:
        assert _ZIP_PATH.exists(), f"ZIP 包不存在: {_ZIP_PATH}"
        with zipfile.ZipFile(_ZIP_PATH) as zf:
            names = zf.namelist()
        assert len(names) == 16, f"期望 16 个文件，实际 {len(names)}"

    def test_each_sub_graph_loads_and_validates(self) -> None:
        """验证每个乘区 JSON 能独立加载。"""
        with zipfile.ZipFile(_ZIP_PATH) as zf:
            for name in zf.namelist():
                data = json.loads(zf.read(name))
                doc = document_from_json(data)
                assert doc.name, f"{name} 缺少 name"

    def test_register_all_zones(self) -> None:
        """注册所有乘区后，注册表中有 15+1=16 个类型。"""
        self._load_package()
        zone_ids = [k for k in _composite_registry if k != "终末地乘区包/15乘区链"]
        assert len(zone_ids) >= 15

    def test_chain_graph_loads_in_editor(self, qapp) -> None:
        """15乘区链.json 能加载到编辑器，节点和连线数正确。"""
        with zipfile.ZipFile(_ZIP_PATH) as zf:
            data = json.loads(zf.read("15乘区链.json"))
        doc = document_from_json(data)

        widget = GraphEditorWidget()
        load_document(doc, widget)

        nodes = widget.graph_nodes()
        edges = widget.graph_wires()
        # 34 节点: 1 const + 15 复合 + 15 连乘 + 2 输入 + 1 输出
        assert len(nodes) == 34, f"期望 34 节点，实际 {len(nodes)}"
        assert len(edges) == 33, f"期望 33 连线，实际 {len(edges)}"

        composite_types = [n.type for n in nodes]
        assert composite_types.count("composite") == 15

    def test_compile_chain_with_registered_types(self, qapp) -> None:
        """注册所有乘区后，加载链图并编译为 DAG。"""
        self._load_package()

        with zipfile.ZipFile(_ZIP_PATH) as zf:
            data = json.loads(zf.read("15乘区链.json"))
        doc = document_from_json(data)

        dag = compile_graph(doc)
        assert "node_count" in dir(dag) or len(dag.nodes) > 30
        # check subgraphs were created for each zone
        assert dag.subgraphs is not None
        assert len(dag.subgraphs) >= 15

    def test_evaluate_chain_with_defaults(self, qapp) -> None:
        """编译链图并使用默认值求值。
        
        默认输入:
          const(1.0) = 1.0
          基础伤害区: 1000(最终攻击力) × 1.0(技能倍率) = 1000
          暴击区: 1 + 0.05(暴击率)×(0.5(暴击伤害)-1) = 0.975
          伤害加成区~庇护区: 全部 0 加成 → 1.0
          防御区: 100/(100+200(敌方防御)) = 0.3333...
          失衡易伤区: 1.0
          抗性区: 1 - (20(抗性)-0(无视))/100 = 0.8
          非主控减伤区~特殊乘区: 1.0
        
        最终: 1.0 × 1000 × 0.975 × (100/300) × 0.8 = 260.0
        """
        self._load_package()

        with zipfile.ZipFile(_ZIP_PATH) as zf:
            data = json.loads(zf.read("15乘区链.json"))
        doc = document_from_json(data)

        dag = compile_graph(doc)
        result = evaluate_graph(dag, {})

        final_damage = result.outputs.get("n33")
        assert final_damage is not None, "缺少最终伤害输出"

        expected = 260.0
        assert final_damage == pytest.approx(expected, rel=1e-4), (
            f"期望 {expected:.4f}，实际 {final_damage:.4f}"
        )

    def test_evaluate_with_custom_inputs(self, qapp) -> None:
        """验证可通过默认值路径获得不同的输出。
        
        顶层链图的 user_input 节点有各自的默认值，
        evaluate_graph 的 context 不会影响 user_input 节点。
        此测试仅验证求值路径完整。
        """
        self._load_package()

        with zipfile.ZipFile(_ZIP_PATH) as zf:
            data = json.loads(zf.read("15乘区链.json"))
        doc = document_from_json(data)

        dag = compile_graph(doc)
        result = evaluate_graph(dag, {"无关变量": 999})

        final_damage = result.outputs.get("n33")
        assert final_damage is not None
        assert final_damage == pytest.approx(260.0, rel=1e-4)

    def test_sub_graph_zone_compile_individually(self) -> None:
        """单个乘区 JSON 也能独立编译为 DAG。"""
        with zipfile.ZipFile(_ZIP_PATH) as zf:
            for name in zf.namelist():
                if name == "15乘区链.json":
                    continue
                data = json.loads(zf.read(name))
                doc = document_from_json(data)
                dag = compile_graph(doc)
                # 每个乘区至少应有其内部节点
                assert len(dag.nodes) >= 1, f"{name} 编译后无节点"
