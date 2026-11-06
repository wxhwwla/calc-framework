#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""终末地 15 乘区 ZIP 包的端到端加载/编译测试。

ZIP 在测试内用 ``tools.generate_endfield_zone_package.build_package`` 现场生成，
不依赖仓库中可能过期或被 Git 忽略的 ``output/终末地乘区包.zip``。
"""

import json
import sys
import zipfile
from pathlib import Path

import pytest

from calc_framework.dag.engine import evaluate_graph
from calc_framework.graph_editor.compiler import compile_graph
from calc_framework.graph_editor.file_actions import load_document
from calc_framework.graph_editor.graph_editor_widget import GraphEditorWidget
from calc_framework.graph_editor.package_manager import PackageManager
from calc_framework.graph_editor.registry import (
    _composite_registry,
    get_package_manager,
    register_composite_type,
)
from calc_framework.graph_editor.serializer import document_from_json

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

_CHAIN_FILENAME = "15乘区链.json"


@pytest.fixture(scope="module")
def zone_zip(tmp_path_factory) -> Path:
    """现场生成乘区包 ZIP，避免读取仓库内过期产物。"""
    from tools.generate_endfield_zone_package import build_package

    return build_package(tmp_path_factory.mktemp("endfield_zone_package") / "终末地乘区包.zip")


def _chain_document(zone_zip: Path):
    with zipfile.ZipFile(zone_zip) as zf:
        data = json.loads(zf.read(_CHAIN_FILENAME))
    return document_from_json(data)


def _single_output(result) -> float:
    assert len(result.outputs) == 1, f"链图应只有一个输出，实际 {result.outputs}"
    return next(iter(result.outputs.values()))


class TestEndfieldZonePackage:
    """终末地 15 乘区包的完整加载、注册、编译与求值验证。"""

    @pytest.fixture(autouse=True)
    def _clean_registry(self) -> None:
        _composite_registry.clear()

    def _load_package(self, zone_zip: Path) -> PackageManager:
        pm = get_package_manager()
        tdefs = pm.load_zip(zone_zip)
        for tdef in tdefs:
            register_composite_type(tdef)
        assert len(_composite_registry) >= 15  # 至少 15 个乘区
        return pm

    def test_zip_exists(self, zone_zip: Path) -> None:
        assert zone_zip.exists(), f"ZIP 包不存在: {zone_zip}"
        with zipfile.ZipFile(zone_zip) as zf:
            names = zf.namelist()
        assert len(names) == 16, f"期望 16 个文件，实际 {len(names)}"

    def test_each_sub_graph_loads_and_validates(self, zone_zip: Path) -> None:
        """验证每个乘区 JSON 能独立加载。"""
        with zipfile.ZipFile(zone_zip) as zf:
            for name in zf.namelist():
                data = json.loads(zf.read(name))
                doc = document_from_json(data)
                assert doc.name, f"{name} 缺少 name"

    def test_register_all_zones(self, zone_zip: Path) -> None:
        """注册所有乘区后，注册表中有 15+1=16 个类型。"""
        self._load_package(zone_zip)
        zone_ids = [k for k in _composite_registry if k != "终末地乘区包/15乘区链"]
        assert len(zone_ids) >= 15

    def test_chain_graph_loads_in_editor(self, zone_zip: Path, qapp) -> None:
        """15乘区链.json 能加载到编辑器，节点和连线数正确。"""
        doc = _chain_document(zone_zip)

        widget = GraphEditorWidget()
        load_document(doc, widget)

        nodes = widget.graph_nodes()
        edges = widget.graph_wires()
        # 34 节点: 1 const + 15 复合 + 15 连乘 + 2 输入 + 1 输出
        assert len(nodes) == 34, f"期望 34 节点，实际 {len(nodes)}"
        assert len(edges) == 33, f"期望 33 连线，实际 {len(edges)}"

        composite_types = [n.type for n in nodes]
        assert composite_types.count("composite") == 15

    def test_compile_chain_with_registered_types(self, zone_zip: Path, qapp) -> None:
        """注册所有乘区后，加载链图并编译为 DAG。"""
        self._load_package(zone_zip)

        doc = _chain_document(zone_zip)

        dag = compile_graph(doc)
        assert "node_count" in dir(dag) or len(dag.nodes) > 30
        # check subgraphs were created for each zone
        assert dag.subgraphs is not None
        assert len(dag.subgraphs) >= 15

    def test_evaluate_chain_with_defaults(self, zone_zip: Path, qapp) -> None:
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
        self._load_package(zone_zip)

        doc = _chain_document(zone_zip)

        dag = compile_graph(doc)
        result = evaluate_graph(dag, {})

        final_damage = _single_output(result)

        expected = 260.0
        assert final_damage == pytest.approx(expected, rel=1e-4), f"期望 {expected:.4f}，实际 {final_damage:.4f}"

    def test_evaluate_with_custom_inputs(self, zone_zip: Path, qapp) -> None:
        """修改链图顶层输入默认值后，求值结果随输入变化。"""
        self._load_package(zone_zip)

        doc = _chain_document(zone_zip)

        atk_node = next(n for n in doc.nodes if n.type == "user_input" and n.label == "最终攻击力")
        atk_node.config.default = 2000.0

        dag = compile_graph(doc)
        result = evaluate_graph(dag, {})

        final_damage = _single_output(result)
        assert final_damage == pytest.approx(520.0, rel=1e-4)

    def test_sub_graph_zone_compile_individually(self, zone_zip: Path) -> None:
        """单个乘区 JSON 也能独立编译为 DAG。"""
        with zipfile.ZipFile(zone_zip) as zf:
            for name in zf.namelist():
                if name == _CHAIN_FILENAME:
                    continue
                data = json.loads(zf.read(name))
                doc = document_from_json(data)
                dag = compile_graph(doc)
                # 每个乘区至少应有其内部节点
                assert len(dag.nodes) >= 1, f"{name} 编译后无节点"
