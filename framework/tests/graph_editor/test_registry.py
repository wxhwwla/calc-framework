#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""节点类型注册表测试。"""

from calc_framework.graph_editor.registry import (    create_default_node,    get_category,    get_display_name,    get_node_type_ids,    get_registry,)class TestRegistryData:
    def test_get_registry_returns_populated(self) -> None:
        reg = get_registry()
        assert len(reg) >= 7  # const, var, user_input, unary, binary, condition, output

    def test_const_has_correct_type(self) -> None:
        entry = get_registry()["const"]
        assert entry.type_id == "const"
        assert entry.display_name
        assert entry.category

    def test_binary_has_ops(self) -> None:
        entry = get_registry()["binary"]
        assert len(entry.ops) >= 8  # + - * / ^ mod min max

    def test_unary_has_ops(self) -> None:
        entry = get_registry()["unary"]
        assert len(entry.ops) >= 5  # neg floor ceil abs sqrt

    def test_unary_has_extended_ops(self) -> None:
        entry = get_registry()["unary"]
        op_ids = [op_id for op_id, _ in entry.ops]
        assert "ln" in op_ids
        assert "log10" in op_ids
        assert "sin" in op_ids
        assert "cos" in op_ids
        assert "tan" in op_ids

    def test_all_registered_types(self) -> None:
        ids = get_node_type_ids()
        assert "const" in ids
        assert "var" in ids
        assert "user_input" in ids
        assert "unary" in ids
        assert "binary" in ids
        assert "condition" in ids
        assert "output" in ids

    def test_display_name_chinese(self) -> None:
        assert get_display_name("const") == "常量"
        assert get_display_name("binary") == "二元运算"
        assert get_display_name("output") == "输出标记"

    def test_categories_are_defined(self) -> None:
        assert get_category("const") == "基础"
        assert get_category("var") == "输入"
        assert get_category("output") == "输出"

    def test_const_entry_has_no_input_ports(self) -> None:
        entry = get_registry()["const"]
        assert entry.in_count == 0

    def test_binary_entry_has_two_inputs(self) -> None:
        entry = get_registry()["binary"]
        assert entry.in_count == 2
        assert len(entry.in_labels) == 2

    def test_condition_has_three_inputs(self) -> None:
        entry = get_registry()["condition"]
        assert entry.in_count == 3
        assert entry.in_labels == ["条件", "真值", "假值"]

    def test_entry_holds_default_config(self) -> None:
        from calc_framework.graph_editor.schema import NodeConfig
        entry = get_registry()["const"]
        assert isinstance(entry.default_config, NodeConfig)


class TestCreateDefaultNode:
    def test_create_const_default(self) -> None:
        node = create_default_node("const")
        assert node.type == "const"
        assert node.id.startswith("node_")

    def test_create_unary_default_has_op(self) -> None:
        node = create_default_node("unary")
        assert node.type == "unary"
        assert node.op is not None  # 默认 op

    def test_create_binary_default_has_op(self) -> None:
        node = create_default_node("binary")
        assert node.type == "binary"
        assert node.op == "+"

    def test_create_var_has_path(self) -> None:
        node = create_default_node("var")
        assert node.type == "var"
        assert node.config.path == ""

    def test_create_with_custom_id(self) -> None:
        node = create_default_node("const", node_id="my_const")
        assert node.id == "my_const"


class TestRegistryCategories:
    def test_get_nodes_by_category(self) -> None:
        from calc_framework.graph_editor.registry import get_nodes_by_category
        cats = get_nodes_by_category()
        assert "基础" in cats
        assert "输入" in cats
        assert "输出" in cats
        # 基础类应该包含 const, unary, binary, condition
        assert any(e.type_id == "const" for e in cats["基础"])
        assert any(e.type_id == "binary" for e in cats["基础"])
        assert any(e.type_id == "unary" for e in cats["基础"])
        assert any(e.type_id == "condition" for e in cats["基础"])
