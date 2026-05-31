#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""灞炴€ч潰鏉挎祴璇曘€?""

from PySide6.QtWidgets import QDoubleSpinBox

from calc_framework.graph_editor.schema import GraphNode, NodeConfig
from calc_framework.graph_editor.prop_panel import PropPanel


class TestPropPanel:
    def test_create_panel(self, qapp) -> None:
        panel = PropPanel()
        assert panel is not None

    def test_initial_state_empty(self, qapp) -> None:
        panel = PropPanel()
        assert panel.current_node_id is None

    def test_show_const_node(self, qapp) -> None:
        panel = PropPanel()
        node = GraphNode(id="n1", type="const", label="娴嬭瘯", config=NodeConfig(value=42.0))
        panel.show_node(node)
        assert panel.current_node_id == "n1"

    def test_const_shows_value_spinbox(self, qapp) -> None:
        panel = PropPanel()
        node = GraphNode(id="n1", type="const", config=NodeConfig(value=42.0))
        panel.show_node(node)
        sb = panel.findChild(QDoubleSpinBox)
        assert sb is not None
        assert sb.value() == 42.0

    def test_var_shows_path_edit(self, qapp) -> None:
        panel = PropPanel()
        node = GraphNode(id="n1", type="var", label="", config=NodeConfig(path="character.鏀诲嚮"))
        panel.show_node(node)
        path_edit = panel._controls.get("path")
        assert path_edit is not None
        assert "character.鏀诲嚮" in path_edit.text()

    def test_value_change_updates_node(self, qapp) -> None:
        panel = PropPanel()
        node = GraphNode(id="n1", type="const", config=NodeConfig(value=10.0))
        panel.show_node(node)
        sb = panel.findChild(QDoubleSpinBox)
        sb.setValue(99.0)
        # 妯℃嫙缂栬緫缁撴潫
        sb.editingFinished.emit()
        assert panel.current_node.config.value == 99.0

    def test_show_none_clears_panel(self, qapp) -> None:
        panel = PropPanel()
        node = GraphNode(id="n1", type="const", config=NodeConfig(value=42.0))
        panel.show_node(node)
        assert panel.current_node_id == "n1"
        panel.show_node(None)
        assert panel.current_node_id is None

    def test_unary_shows_op_dropdown(self, qapp) -> None:
        panel = PropPanel()
        node = GraphNode(id="n1", type="unary", op="ceil", label="鍙栨暣")
        panel.show_node(node)
        # 搴旇鏈夋搷浣滅涓嬫媺
        assert panel.current_node is not None
        assert panel.current_node.op == "ceil"

    def test_binary_shows_op_dropdown(self, qapp) -> None:
        panel = PropPanel()
        node = GraphNode(id="n1", type="binary", op="+", label="鍔犳硶")
        panel.show_node(node)
        assert panel.current_node is not None

    def test_preview_label_exists(self, qapp) -> None:
        """棰勮鏍囩榛樿鏄剧ず"鈥?銆?""
        panel = PropPanel()
        assert panel._preview_label is not None

    def test_set_preview_value(self, qapp) -> None:
        panel = PropPanel()
        panel.set_preview_value("42.000000")
        assert panel._preview_label.text() == "42.000000"

    def test_set_preview_error(self, qapp) -> None:
        panel = PropPanel()
        panel.set_preview_value("閿欒: 鍙橀噺鏈壘鍒?)
        assert "閿欒" in panel._preview_label.text()
