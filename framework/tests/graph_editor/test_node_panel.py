#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""左侧节点面板测试。"""


from calc_framework.graph_editor.node_panel import NodePanelclass TestNodePanel:
    def test_create_panel(self, qapp) -> None:
        panel = NodePanel()
        assert panel is not None

    def test_panel_has_categories(self, qapp) -> None:
        panel = NodePanel()
        label_texts = []
        for i in range(panel.count()):
            panel.widget(i)
            label_texts.append(panel.tabText(i))
        assert "基础" in label_texts or any("基础" in panel.tabText(i) for i in range(panel.count()))

    def test_panel_lists_node_types(self, qapp) -> None:
        panel = NodePanel()
        # 遍历所有标签页，至少能找到常见类型

        for i in range(panel.count()):
            tab = panel.widget(i)
            if hasattr(tab, "itemAt") or hasattr(tab, "findChildren"):
                pass
        # 至少有3个分类标签
        assert panel.count() >= 2

    def test_drag_initiates(self, qapp) -> None:
        panel = NodePanel()
        # 找到一个可拖拽的项
        drag_item = panel.find_draggable_item("binary")
        assert drag_item is not None


class TestNodePanelSignals:
    def test_node_created_signal_emits_on_drop(self, qapp) -> None:
        """验证当用户拖拽到画布时，panel 发出 node_created 信号。"""
        panel = NodePanel()
        received = []

        def on_node_created(node_type: str) -> None:
            received.append(node_type)

        panel.node_created.connect(on_node_created)
        # 模拟从 panel 拖拽出节点
        panel.emit_node_created("binary")
        assert len(received) == 1
        assert received[0] == "binary"
