# SPDX-License-Identifier: AGPL-3.0
"""layout.json 加载与校验 — 单元测试。"""

import pytest

from calc_framework.ui.layout import (
    LayoutValidationError,
    Section,
    load_layout,
    load_layout_json,
)


class TestLoadLayout:
    def test_minimal_valid_with_one_input_section(self):
        data = {
            "schema_version": "ui-v1",
            "name": "测试",
            "sections": [
                {
                    "id": "sec1",
                    "type": "inputs",
                    "title": "输入",
                    "variables": ["character.基础攻击"],
                }
            ],
        }
        layout = load_layout(data)
        assert layout.name == "测试"
        assert layout.schema_version == "ui-v1"
        assert len(layout.sections) == 1
        assert isinstance(layout.sections[0], Section)
        assert layout.sections[0].variables == ["character.基础攻击"]

    def test_mixed_input_and_output_sections(self):
        data = {
            "schema_version": "ui-v1",
            "name": "测试",
            "sections": [
                {"id": "in", "type": "inputs", "title": "输入", "variables": ["character.力量"]},
                {"id": "out", "type": "outputs", "title": "输出", "outputs": ["最终攻击力"]},
            ],
        }
        layout = load_layout(data)
        assert len(layout.sections) == 2
        assert isinstance(layout.sections[1], Section)
        assert layout.sections[1].outputs == ["最终攻击力"]

    def test_columns_defaults_to_2_for_inputs(self):
        data = {
            "schema_version": "ui-v1",
            "name": "测试",
            "sections": [{"id": "s", "type": "inputs", "title": "输入", "variables": ["a"]}],
        }
        layout = load_layout(data)
        assert layout.sections[0].columns == 2

    def test_custom_columns(self):
        data = {
            "schema_version": "ui-v1",
            "name": "测试",
            "sections": [
                {"id": "s", "type": "inputs", "title": "输入", "variables": ["a"], "columns": 3}
            ],
        }
        assert load_layout(data).sections[0].columns == 3

    def test_missing_schema_version_raises(self):
        with pytest.raises(LayoutValidationError, match="schema_version"):
            load_layout({"name": "x", "sections": []})

    def test_wrong_schema_version_raises(self):
        with pytest.raises(LayoutValidationError, match="ui-v1"):
            load_layout({"schema_version": "v0", "name": "x", "sections": []})

    def test_missing_name_raises(self):
        with pytest.raises(LayoutValidationError, match="name"):
            load_layout({"schema_version": "ui-v1", "sections": []})

    def test_empty_sections_raises(self):
        with pytest.raises(LayoutValidationError, match="sections"):
            load_layout({"schema_version": "ui-v1", "name": "x", "sections": []})

    def test_unknown_section_type_raises(self):
        with pytest.raises(LayoutValidationError, match="type"):
            load_layout({
                "schema_version": "ui-v1",
                "name": "x",
                "sections": [{"id": "s", "type": "unknown", "title": "x"}],
            })

    def test_input_section_missing_variables_raises(self):
        with pytest.raises(LayoutValidationError, match="variables"):
            load_layout({
                "schema_version": "ui-v1",
                "name": "x",
                "sections": [{"id": "s", "type": "inputs", "title": "输入"}],
            })

    def test_output_section_missing_outputs_raises(self):
        with pytest.raises(LayoutValidationError, match="outputs"):
            load_layout({
                "schema_version": "ui-v1",
                "name": "x",
                "sections": [{"id": "s", "type": "outputs", "title": "输出"}],
            })

    def test_duplicate_section_ids_raises(self):
        with pytest.raises(LayoutValidationError, match="id"):
            load_layout({
                "schema_version": "ui-v1",
                "name": "x",
                "sections": [
                    {"id": "dup", "type": "inputs", "title": "A", "variables": ["a"]},
                    {"id": "dup", "type": "outputs", "title": "B", "outputs": ["b"]},
                ],
            })

    def test_section_missing_id_raises(self):
        with pytest.raises(LayoutValidationError, match="id"):
            load_layout({
                "schema_version": "ui-v1",
                "name": "x",
                "sections": [{"type": "inputs", "title": "输入", "variables": ["a"]}],
            })

    def test_section_missing_title_raises(self):
        with pytest.raises(LayoutValidationError, match="title"):
            load_layout({
                "schema_version": "ui-v1",
                "name": "x",
                "sections": [{"id": "s", "type": "outputs", "outputs": ["a"]}],
            })

    def test_all_standard_keys_preserved(self):
        data = {
            "schema_version": "ui-v1",
            "name": "完整测试",
            "description": "一个描述",
            "sections": [
                {"id": "s1", "type": "inputs", "title": "输入区", "variables": ["a", "b"], "columns": 1},
                {"id": "s2", "type": "outputs", "title": "输出区", "outputs": ["c", "d"]},
            ],
        }
        layout = load_layout(data)
        assert layout.name == "完整测试"
        assert layout.description == "一个描述"
        assert layout.sections[0].id == "s1"
        assert layout.sections[0].columns == 1
        assert layout.sections[1].title == "输出区"

    def test_load_from_json_string(self):
        import json

        s = json.dumps({
            "schema_version": "ui-v1",
            "name": "from str",
            "sections": [{"id": "s", "type": "inputs", "title": "T", "variables": ["x"]}],
        })
        layout = load_layout_json(s)
        assert layout.name == "from str"


class TestLayoutModel:
    def test_find_section_by_id(self):
        data = {
            "schema_version": "ui-v1",
            "name": "test",
            "sections": [
                {"id": "in", "type": "inputs", "title": "输入", "variables": ["a"]},
                {"id": "out", "type": "outputs", "title": "输出", "outputs": ["b"]},
            ],
        }
        layout = load_layout(data)
        s = layout.find_section("out")
        assert s is not None
        assert s.id == "out"

    def test_find_section_returns_none_for_missing(self):
        data = {
            "schema_version": "ui-v1",
            "name": "test",
            "sections": [{"id": "s", "type": "inputs", "title": "T", "variables": ["a"]}],
        }
        layout = load_layout(data)
        assert layout.find_section("nope") is None
