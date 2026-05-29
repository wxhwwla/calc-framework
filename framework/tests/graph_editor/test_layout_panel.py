#!/usr/bin/env python3
"""排版管理面板测试。"""

import pytest
from PySide6.QtWidgets import QListWidget, QPushButton, QComboBox

from calc_framework.graph_editor.schema import SectionDef
from calc_framework.graph_editor.layout_panel import LayoutPanel


class TestLayoutPanel:
    def test_create_panel(self, qapp) -> None:
        panel = LayoutPanel()
        assert panel is not None

    def test_initial_section_count(self, qapp) -> None:
        panel = LayoutPanel()
        assert len(panel.sections()) == 0

    def test_add_section(self, qapp) -> None:
        panel = LayoutPanel()
        panel.add_section("计算结果", ["out_1"])
        secs = panel.sections()
        assert len(secs) == 1
        assert secs[0].title == "计算结果"
        assert secs[0].output_nodes == ["out_1"]

    def test_add_multiple_sections(self, qapp) -> None:
        panel = LayoutPanel()
        panel.add_section("攻击力链", ["n1"])
        panel.add_section("最终伤害", ["n5"])
        assert len(panel.sections()) == 2

    def test_remove_section(self, qapp) -> None:
        panel = LayoutPanel()
        panel.add_section("A", [])
        panel.add_section("B", [])
        assert len(panel.sections()) == 2
        panel.remove_section(0)
        secs = panel.sections()
        assert len(secs) == 1
        assert secs[0].title == "B"

    def test_clear_all_sections(self, qapp) -> None:
        panel = LayoutPanel()
        panel.add_section("A", [])
        panel.add_section("B", [])
        panel.clear_all()
        assert len(panel.sections()) == 0

    def test_section_title_editable(self, qapp) -> None:
        panel = LayoutPanel()
        panel.add_section("旧标题", [])
        panel.set_section_title(0, "新标题")
        assert panel.sections()[0].title == "新标题"

    def test_section_columns_editable(self, qapp) -> None:
        panel = LayoutPanel()
        panel.add_section("测试", [])
        panel.set_section_columns(0, 2)
        assert panel.sections()[0].columns == 2

    def test_get_output_nodes_list(self, qapp) -> None:
        panel = LayoutPanel()
        panel.add_section("结果", ["out1", "out2", "out3"])
        assert panel.section_output_nodes(0) == ["out1", "out2", "out3"]

    def test_add_output_to_section(self, qapp) -> None:
        panel = LayoutPanel()
        panel.add_section("结果", ["out1"])
        panel.add_output_to_section(0, "out2")
        assert "out2" in panel.section_output_nodes(0)

    def test_remove_output_from_section(self, qapp) -> None:
        panel = LayoutPanel()
        panel.add_section("结果", ["out1", "out2", "out3"])
        panel.remove_output_from_section(0, "out2")
        assert panel.section_output_nodes(0) == ["out1", "out3"]

    def test_set_sections_from_model(self, qapp) -> None:
        panel = LayoutPanel()
        sections = [
            SectionDef(id="s1", title="攻击力", output_nodes=["n1", "n2"], columns=1),
            SectionDef(id="s2", title="伤害", output_nodes=["n5"], columns=2),
        ]
        panel.set_sections(sections)
        assert len(panel.sections()) == 2
        assert panel.sections()[0].title == "攻击力"
        assert panel.sections()[1].columns == 2
