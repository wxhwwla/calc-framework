"""变量 Schema 校验 — 单元测试。"""

import pytest

from calc_framework.dag.schema import DAGGraph, DAGVariable
from calc_framework.data.context import make_context
from calc_framework.data.schema import validate_variables, VariableValidationError


def _make_graph(variables: dict[str, DAGVariable]) -> DAGGraph:
    return DAGGraph(
        name="test",
        variables=variables,
        nodes={},
        outputs={},
    )


class TestValidateVariables:
    def test_empty_variables_always_passes(self):
        graph = _make_graph({})
        ctx = make_context()
        validate_variables(graph, ctx)

    def test_var_present_in_context_passes(self):
        graph = _make_graph({
            "character.攻击": DAGVariable(type="float", source="character"),
        })
        ctx = make_context(character={"攻击": 500})
        validate_variables(graph, ctx)

    def test_var_missing_in_context_raises(self):
        graph = _make_graph({
            "character.攻击": DAGVariable(type="float", source="character"),
        })
        ctx = make_context()
        with pytest.raises(VariableValidationError, match="character.攻击"):
            validate_variables(graph, ctx)

    def test_var_with_default_does_not_raise_when_missing(self):
        graph = _make_graph({
            "enemy.防御": DAGVariable(type="float", source="enemy", default=100),
        })
        ctx = make_context()
        validate_variables(graph, ctx)  # 不抛异常

    def test_float_type_passes_with_number(self):
        graph = _make_graph({
            "character.攻击": DAGVariable(type="float", source="character"),
        })
        ctx = make_context(character={"攻击": 500})
        validate_variables(graph, ctx)

    def test_int_passes_with_int(self):
        graph = _make_graph({
            "character.等级": DAGVariable(type="int", source="character"),
        })
        ctx = make_context(character={"等级": 80})
        validate_variables(graph, ctx)

    def test_bool_passes_with_bool(self):
        graph = _make_graph({
            "character.is_crit": DAGVariable(type="bool", source="character"),
        })
        ctx = make_context(character={"is_crit": True})
        validate_variables(graph, ctx)

    def test_type_mismatch_raises(self):
        graph = _make_graph({
            "character.等级": DAGVariable(type="int", source="character"),
        })
        ctx = make_context(character={"等级": 80.5})
        with pytest.raises(VariableValidationError, match="类型"):
            validate_variables(graph, ctx)

    def test_multiple_vars_reports_first_error(self):
        graph = _make_graph({
            "character.a": DAGVariable(type="float", source="character"),
            "character.b": DAGVariable(type="float", source="character"),
        })
        ctx = make_context()
        with pytest.raises(VariableValidationError):
            validate_variables(graph, ctx)

    def test_nested_path_resolves(self):
        graph = _make_graph({
            "character.stats.攻击": DAGVariable(type="float", source="character"),
        })
        ctx = make_context(character={"stats": {"攻击": 500}})
        validate_variables(graph, ctx)
