#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""包管理器与复合节点功能测试。"""

import jsonfrom pathlib import Pathfrom calc_framework.graph_editor.package_manager import PackageManagerfrom calc_framework.graph_editor.registry import (    _composite_registry,    create_default_node,    register_composite_type,)_SAMPLE_GRAPH_JSON = json.dumps({
    "schema_version": "calc-graph-v1",
    "name": "子图测试",
    "nodes": [
        {"id": "in_a", "type": "user_input", "label": "输入A", "config": {"default": 0}},
        {"id": "in_b", "type": "user_input", "label": "输入B", "config": {"default": 0}},
        {"id": "op", "type": "binary", "op": "+", "label": "加法"},
        {"id": "out", "type": "output", "label": "结果"},
    ],
    "edges": [
        {"from_node": "in_a", "from_port": 0, "to_node": "op", "to_port": 0},
        {"from_node": "in_b", "from_port": 0, "to_node": "op", "to_port": 1},
        {"from_node": "op", "from_port": 0, "to_node": "out", "to_port": 0},
    ],
    "layout": {"sections": []},
})

_SAMPLE_GRAPH_JSON_INLINE = json.dumps({
    "schema_version": "calc-graph-v1",
    "name": "子图内联",
    "nodes": [
        {"id": "x", "type": "user_input", "label": "值"},
        {"id": "o", "type": "unary", "op": "abs", "label": "绝对值"},
        {"id": "ot", "type": "output", "label": "输出"},
    ],
    "edges": [
        {"from_node": "x", "from_port": 0, "to_node": "o", "to_port": 0},
        {"from_node": "o", "from_port": 0, "to_node": "ot", "to_port": 0},
    ],
    "layout": {"sections": [{"id": "s1", "title": "结果", "output_nodes": ["ot"], "columns": 1}]},
})


class TestPackageManager:
    def test_load_json_basic(self, tmp_path) -> None:
        f = tmp_path / "adder.json"
        f.write_text(_SAMPLE_GRAPH_JSON, encoding="utf-8")
        pm = PackageManager()
        tdef = pm.load_json(f)
        assert tdef.type_id == "@adder/adder"
        assert tdef.display_name == "[adder] adder"
        assert tdef.in_count == 2
        assert tdef.out_count == 1
        assert tdef.in_labels == ["输入A", "输入B"]
        assert tdef.out_labels == ["结果"]

    def test_load_json_inline(self, tmp_path) -> None:
        f = tmp_path / "abs_wrapper.json"
        f.write_text(_SAMPLE_GRAPH_JSON_INLINE, encoding="utf-8")
        pm = PackageManager()
        tdef = pm.load_json(f)
        assert tdef.in_count == 1
        assert tdef.out_count == 1
        assert tdef.in_labels == ["值"]
        assert tdef.out_labels == ["输出"]

    def test_load_zip(self, tmp_path) -> None:
        import zipfile
        zip_path = tmp_path / "mypackage.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("adder.json", _SAMPLE_GRAPH_JSON)
            zf.writestr("abs_wrapper.json", _SAMPLE_GRAPH_JSON_INLINE)
        pm = PackageManager()
        tdefs = pm.load_zip(zip_path)
        assert len(tdefs) == 2
        type_ids = [t.type_id for t in tdefs]
        assert "@mypackage/adder" in type_ids
        assert "@mypackage/abs_wrapper" in type_ids

    def test_package_manager_singleton(self) -> None:
        from calc_framework.graph_editor.registry import get_package_manager
        pm1 = get_package_manager()
        pm2 = get_package_manager()
        assert pm1 is pm2


class TestCompositeNodeCreation:
    def _clean_registry(self) -> None:
        _composite_registry.clear()

    def test_register_and_create_composite_node(self) -> None:
        self._clean_registry()
        from calc_framework.graph_editor.registry import get_package_manager as _gpm
        pm = _gpm()
        import os        import tempfile
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
            f.write(_SAMPLE_GRAPH_JSON)
            fpath = Path(f.name)
        try:
            tdef = pm.load_json(fpath)
            register_composite_type(tdef)
            node = create_default_node(tdef.type_id)
            assert node.type == "composite"
            assert node.op == tdef.type_id
            assert node.config.source_graph == _SAMPLE_GRAPH_JSON
            assert node.config.package_name == fpath.stem
        finally:
            os.unlink(str(fpath))

    def test_composite_node_has_correct_ports_via_item(self, qapp) -> None:
        """验证通过 NodeItem 创建的复合节点端口数正确。"""
        self._clean_registry()
        from calc_framework.graph_editor.registry import get_package_manager as _gpm
        pm = _gpm()
        import os        import tempfile
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
            f.write(_SAMPLE_GRAPH_JSON_INLINE)
            fpath = Path(f.name)
        try:
            tdef = pm.load_json(fpath)
            register_composite_type(tdef)
            node = create_default_node(tdef.type_id)

            from calc_framework.graph_editor.graph_editor_widget import GraphEditorWidget
            w = GraphEditorWidget()
            w.add_graph_node(node)
            ports = w.node_ports(node.id)
            from calc_framework.graph_editor.ports import PortDirection
            inputs = [p for p in ports if p.direction == PortDirection.INPUT]
            outputs = [p for p in ports if p.direction == PortDirection.OUTPUT]
            assert len(inputs) == 1
            assert len(outputs) == 1
            assert inputs[0].label == "值"
            assert outputs[0].label == "输出"
        finally:
            os.unlink(str(fpath))
