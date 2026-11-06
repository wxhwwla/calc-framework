# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""MCP 规格归一化 — 单元测试。"""

from __future__ import annotations

import pytest
from tools.calc_mcp.spec import SpecError, normalize_spec


def _base(**overrides):
    data = {
        "variables": [
            {"name": "atk", "type": "float", "source": "input", "default": 100, "description": "攻击"},
            {"name": "def", "type": "percent", "source": "enemy", "default": 10},
        ],
        "formula_steps": [{"id": "damage", "op": "mul", "lhs": "atk", "rhs": "2"}],
        "outputs": [{"name": "damage", "node": "damage"}],
    }
    data.update(overrides)
    return data


def test_normalize_aliases() -> None:
    spec = normalize_spec(**_base())

    assert spec.variables[0].source == "user_input"
    assert spec.variables[1].type == "float"
    assert spec.steps[0].op == "*"
    assert spec.variables[0].to_generator_dict()["source"] == "user_input"
    assert isinstance(spec.warnings, list)


def test_normalize_filters_unknown_fields() -> None:
    data = _base()
    data["variables"][0]["color"] = "red"

    spec = normalize_spec(**data)

    assert spec.variables[0].name == "atk"
    assert any("color" in warning for warning in spec.warnings)


def test_duplicate_variable_path_rejected() -> None:
    data = _base()
    data["variables"].append({"name": "atk", "source": "user_input"})

    with pytest.raises(SpecError, match="重复"):
        normalize_spec(**data)


def test_node_id_collision_rejected() -> None:
    data = _base()
    data["variables"] = [
        {"name": "ATK", "source": "user_input"},
        {"name": "atk", "source": "enemy"},
    ]
    data["formula_steps"] = [{"id": "damage", "op": "+", "lhs": "ATK", "rhs": "atk"}]
    data["outputs"] = [{"name": "damage", "node": "damage"}]

    with pytest.raises(SpecError, match="节点 id"):
        normalize_spec(**data)


def test_step_id_collides_with_variable_node_id() -> None:
    data = _base()
    data["variables"] = [{"name": "damage", "source": "user_input"}]

    with pytest.raises(SpecError, match="步骤 id"):
        normalize_spec(**data)


def test_dangling_reference_rejected() -> None:
    data = _base()
    data["formula_steps"] = [{"id": "damage", "op": "-", "lhs": "atk", "rhs": "missing"}]

    with pytest.raises(SpecError, match="missing"):
        normalize_spec(**data)


def test_numeric_literal_reference_allowed() -> None:
    data = _base()
    data["formula_steps"] = [{"id": "damage", "op": "-", "lhs": "atk", "rhs": "10.5"}]

    spec = normalize_spec(**data)
    assert spec.steps[0].rhs == "10.5"


def test_unknown_operator_rejected() -> None:
    data = _base()
    data["formula_steps"] = [{"id": "damage", "op": "pow", "lhs": "atk", "rhs": "2"}]

    with pytest.raises(SpecError, match="op"):
        normalize_spec(**data)


def test_output_reference_rejected() -> None:
    data = _base()
    data["outputs"] = [{"name": "result", "node": "missing"}]

    with pytest.raises(SpecError, match="missing"):
        normalize_spec(**data)


def test_long_expression_rejected() -> None:
    data = _base()
    data["formula_steps"] = [
        {"id": "damage", "op": "expr", "expr": "x" * 5000, "input_map": {"x": "atk"}},
    ]
    data["outputs"] = [{"name": "damage", "node": "damage"}]

    with pytest.raises(SpecError, match="表达式"):
        normalize_spec(**data)


def test_invalid_source_and_type_rejected() -> None:
    data = _base()
    data["variables"] = [{"name": "atk", "source": "magic"}]
    with pytest.raises(SpecError, match="source"):
        normalize_spec(**data)

    data = _base()
    data["variables"] = [{"name": "atk", "type": "vector"}]
    with pytest.raises(SpecError, match="type"):
        normalize_spec(**data)


def test_empty_steps_rejected() -> None:
    data = _base(formula_steps=[])

    with pytest.raises(SpecError, match="公式步骤"):
        normalize_spec(**data)


def test_data_files_normalized_and_warn_on_binding() -> None:
    data = _base(data_files={"enemy": [{"名称": "Boss", "def": 10}]})

    spec = normalize_spec(**data)

    assert spec.data_files == {"enemy": [{"名称": "Boss", "def": 10}]}
    assert any("已绑定" in warning for warning in spec.warnings)


def test_unbound_source_produces_remap_warning() -> None:
    spec = normalize_spec(**_base())

    assert any("改写为 user_input" in warning for warning in spec.warnings)


def test_invalid_data_files_source_rejected() -> None:
    data = _base(data_files={"user_input": []})

    with pytest.raises(SpecError, match="data_files"):
        normalize_spec(**data)


def test_data_files_record_without_name_rejected() -> None:
    data = _base(data_files={"enemy": [{"def": 1}]})

    with pytest.raises(SpecError, match="名称"):
        normalize_spec(**data)


def test_variable_ui_metadata_normalized() -> None:
    data = _base()
    data["variables"][0].update({"min": 0, "max": 100, "ui_control": {"suffix": "%", "step": 1}})

    spec = normalize_spec(**data)

    var = spec.variables[0]
    assert var.min_value == 0
    assert var.max_value == 100
    assert var.ui_control == {"suffix": "%", "step": 1}
    payload = var.to_generator_dict()
    assert payload["min"] == 0
    assert payload["max"] == 100
    assert payload["ui_control"] == {"suffix": "%", "step": 1}


def test_ui_control_options_imply_dropdown() -> None:
    data = _base()
    data["variables"][0]["ui_control"] = {"options": ["甲", "乙"]}

    spec = normalize_spec(**data)

    assert spec.variables[0].ui_control == {"options": ["甲", "乙"], "widget": "dropdown"}


@pytest.mark.parametrize(
    ("field", "value", "match"),
    [
        ("min", "zero", "min"),
        ("max", float("nan"), "max"),
        ("ui_control", "x", "ui_control"),
        ("ui_control", {"step": 0}, "step"),
        ("ui_control", {"step": -1}, "step"),
        ("ui_control", {"widget": "knob"}, "widget"),
        ("ui_control", {"options": []}, "options"),
        ("ui_control", {"options": [1]}, "options"),
        ("ui_control", {"suffix": 1}, "suffix"),
    ],
)
def test_invalid_variable_ui_rejected(field: str, value: object, match: str) -> None:
    data = _base()
    data["variables"][0][field] = value

    with pytest.raises(SpecError, match=match):
        normalize_spec(**data)


def test_variable_min_greater_than_max_rejected() -> None:
    data = _base()
    data["variables"][0].update({"min": 10, "max": 1})

    with pytest.raises(SpecError, match="min"):
        normalize_spec(**data)


def test_ui_control_unknown_key_warns() -> None:
    data = _base()
    data["variables"][0]["ui_control"] = {"suffix": "%", "color": "red"}

    spec = normalize_spec(**data)

    assert spec.variables[0].ui_control == {"suffix": "%"}
    assert any("color" in warning for warning in spec.warnings)


def test_ui_control_on_non_user_input_warns() -> None:
    data = _base()
    data["variables"][1]["ui_control"] = {"suffix": "%"}

    spec = normalize_spec(**data)

    assert any("仅对 user_input" in warning for warning in spec.warnings)


def test_min_max_on_non_numeric_warns() -> None:
    data = _base()
    data["variables"].append({"name": "label", "type": "str", "source": "user_input", "min": 0})

    spec = normalize_spec(**data)

    assert any("min/max" in warning for warning in spec.warnings)


def test_entity_detail_and_input_rules_normalized() -> None:
    data = _base(
        variables=[
            {"name": "atk", "type": "float", "source": "weapon", "default": 100},
            {"name": "armor", "type": "float", "source": "user_input", "default": 0},
        ],
        data_files={"weapon": [{"名称": "剑", "atk": 65, "is_energy": 0}]},
        entity_detail={
            "source": "weapon",
            "title": "武器数据",
            "sections": [{"fields": [{"field": "atk", "label": "攻击"}]}],
        },
        entity_input_rules=[
            {
                "source": "weapon",
                "field": "is_energy",
                "equals": 0,
                "disable": ["user_input.armor"],
            }
        ],
    )

    spec = normalize_spec(**data)

    assert spec.entity_detail["source"] == "weapon"
    assert spec.entity_detail["sections"][0]["fields"] == [{"field": "atk", "label": "攻击"}]
    assert spec.entity_input_rules[0]["equals"] == 0.0


@pytest.mark.parametrize(
    ("kwargs", "match"),
    [
        ({"entity_detail": {"source": "weapon"}}, "entity_detail"),
        (
            {
                "entity_detail": {
                    "source": "weapon",
                    "sections": [{"fields": [{"field": "missing"}]}],
                }
            },
            "entity_detail",
        ),
        (
            {
                "entity_input_rules": [
                    {"source": "weapon", "field": "is_energy", "equals": 0, "disable": ["user_input.missing"]}
                ]
            },
            "entity_input_rules",
        ),
    ],
)
def test_invalid_entity_meta_rejected(kwargs: dict, match: str) -> None:
    data = _base(
        variables=[
            {"name": "atk", "type": "float", "source": "weapon", "default": 100},
            {"name": "armor", "type": "float", "source": "user_input", "default": 0},
        ],
        data_files={"weapon": [{"名称": "剑", "atk": 65, "is_energy": 0}]},
        **kwargs,
    )

    with pytest.raises(SpecError, match=match):
        normalize_spec(**data)
