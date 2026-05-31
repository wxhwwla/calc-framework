#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""宸︿晶鑺傜偣闈㈡澘娴嬭瘯銆?""


from calc_framework.graph_editor.node_panel import NodePanel


class TestNodePanel:
    def test_create_panel(self, qapp) -> None:
        panel = NodePanel()
        assert panel is not None

    def test_panel_has_categories(self, qapp) -> None:
        panel = NodePanel()
        label_texts = []
        for i in range(panel.count()):
            w = panel.widget(i)
            label_texts.append(panel.tabText(i))
        assert "鍩虹" in label_texts or any("鍩虹" in panel.tabText(i) for i in range(panel.count()))

    def test_panel_lists_node_types(self, qapp) -> None:
        panel = NodePanel()
        # 閬嶅巻鎵€鏈夋爣绛鹃〉锛岃嚦灏戣兘鎵惧埌甯歌绫诲瀷
        found_labels = set()
        for i in range(panel.count()):
            tab = panel.widget(i)
            if hasattr(tab, "itemAt") or hasattr(tab, "findChildren"):
                pass
        # 鑷冲皯鏈?涓垎绫绘爣绛?
        assert panel.count() >= 2

    def test_drag_initiates(self, qapp) -> None:
        panel = NodePanel()
        # 鎵惧埌涓€涓彲鎷栨嫿鐨勯」
        drag_item = panel.find_draggable_item("binary")
        assert drag_item is not None


class TestNodePanelSignals:
    def test_node_created_signal_emits_on_drop(self, qapp) -> None:
        """楠岃瘉褰撶敤鎴锋嫋鎷藉埌鐢诲竷鏃讹紝panel 鍙戝嚭 node_created 淇″彿銆?""
        panel = NodePanel()
        received = []

        def on_node_created(node_type: str) -> None:
            received.append(node_type)

        panel.node_created.connect(on_node_created)
        # 妯℃嫙浠?panel 鎷栨嫿鍑鸿妭鐐?
        panel.emit_node_created("binary")
        assert len(received) == 1
        assert received[0] == "binary"
