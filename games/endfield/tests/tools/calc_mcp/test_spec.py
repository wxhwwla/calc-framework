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
