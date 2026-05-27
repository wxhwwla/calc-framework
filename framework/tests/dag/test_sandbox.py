#!/usr/bin/env python3
"""AST 沙箱单元测试。"""


import pytest
from calc_framework.dag.errors import DAGCompileError, DAGRuntimeError, DAGSecurityError
from calc_framework.dag.sandbox import evaluate, parse_expr, validate_expr


class TestSimpleArithmetic:
    """基本四则运算。"""

    def test_add(self) -> None:
        assert evaluate(parse_expr("1 + 2"), {}) == pytest.approx(3.0)

    def test_subtract(self) -> None:
        assert evaluate(parse_expr("5 - 3"), {}) == pytest.approx(2.0)

    def test_multiply(self) -> None:
        assert evaluate(parse_expr("4 * 3"), {}) == pytest.approx(12.0)

    def test_divide(self) -> None:
        assert evaluate(parse_expr("10 / 4"), {}) == pytest.approx(2.5)

    def test_negate(self) -> None:
        assert evaluate(parse_expr("-3"), {}) == pytest.approx(-3.0)

    def test_precedence(self) -> None:
        assert evaluate(parse_expr("1 + 2 * 3"), {}) == pytest.approx(7.0)

    def test_parentheses(self) -> None:
        assert evaluate(parse_expr("(1 + 2) * 3"), {}) == pytest.approx(9.0)


class TestVariableSubstitution:
    """变量注入。"""

    def test_single_var(self) -> None:
        assert evaluate(parse_expr("x"), {"x": 42.0}) == pytest.approx(42.0)

    def test_var_in_expression(self) -> None:
        assert evaluate(parse_expr("a + b * c"), {"a": 1.0, "b": 2.0, "c": 3.0}) == pytest.approx(7.0)

    def test_missing_var_raises(self) -> None:
        tree = parse_expr("x + y")
        with pytest.raises(DAGRuntimeError, match="变量"):
            evaluate(tree, {"x": 1.0})

    def test_multiple_refs_same_var(self) -> None:
        assert evaluate(parse_expr("x + x * x"), {"x": 2.0}) == pytest.approx(6.0)


class TestWhitelistedFunctions:
    """白名单内置函数。"""

    def test_floor(self) -> None:
        assert evaluate(parse_expr("floor(3.7)"), {}) == pytest.approx(3.0)

    def test_ceil(self) -> None:
        assert evaluate(parse_expr("ceil(3.2)"), {}) == pytest.approx(4.0)

    def test_abs_positive(self) -> None:
        assert evaluate(parse_expr("abs(-5)"), {}) == pytest.approx(5.0)

    def test_sqrt(self) -> None:
        assert evaluate(parse_expr("sqrt(16)"), {}) == pytest.approx(4.0)

    def test_min_two_args(self) -> None:
        assert evaluate(parse_expr("min(3, 7)"), {}) == pytest.approx(3.0)

    def test_max_two_args(self) -> None:
        assert evaluate(parse_expr("max(3, 7)"), {}) == pytest.approx(7.0)

    def test_nested_functions(self) -> None:
        assert evaluate(parse_expr("floor(sqrt(10))"), {}) == pytest.approx(3.0)

    def test_whitelist_func_with_vars(self) -> None:
        assert evaluate(parse_expr("min(a, b)"), {"a": 5.0, "b": 10.0}) == pytest.approx(5.0)


class TestRejectedOperations:
    """拒绝白名单外的语法。"""

    def test_power_rejected(self) -> None:
        with pytest.raises(DAGSecurityError):
            parse_expr("2 ** 3")

    def test_comparison_rejected(self) -> None:
        with pytest.raises(DAGSecurityError):
            parse_expr("a > b")

    def test_boolean_and_rejected(self) -> None:
        with pytest.raises(DAGSecurityError):
            parse_expr("a and b")

    def test_ternary_rejected(self) -> None:
        with pytest.raises(DAGSecurityError):
            parse_expr("1 if a else 2")

    def test_attribute_rejected(self) -> None:
        with pytest.raises(DAGSecurityError):
            parse_expr("obj.attr")

    def test_list_literal_rejected(self) -> None:
        with pytest.raises(DAGSecurityError):
            parse_expr("[1, 2, 3]")

    def test_dict_literal_rejected(self) -> None:
        with pytest.raises(DAGSecurityError):
            parse_expr("{'a': 1}")

    def test_import_rejected(self) -> None:
        with pytest.raises(DAGSecurityError):
            parse_expr("__import__('os')")

    def test_lambda_rejected(self) -> None:
        with pytest.raises(DAGSecurityError):
            parse_expr("lambda x: x+1")

    def test_non_whitelist_call_rejected(self) -> None:
        with pytest.raises(DAGSecurityError):
            parse_expr("open('file')")


class TestParseValidation:
    """表达式解析校验。"""

    def test_empty_expr_rejected(self) -> None:
        with pytest.raises(DAGCompileError):
            parse_expr("")

    def test_invalid_syntax_rejected(self) -> None:
        with pytest.raises(DAGCompileError):
            parse_expr("1 + +")

    def test_float_literals(self) -> None:
        assert evaluate(parse_expr("3.14 + 0.86"), {}) == pytest.approx(4.0)

    def test_negative_numbers(self) -> None:
        assert evaluate(parse_expr("1 + -3"), {}) == pytest.approx(-2.0)

    def test_validate_expr_does_not_raise_for_valid(self) -> None:
        validate_expr("1 + floor(a) / 100")

    def test_validate_expr_raises_for_invalid(self) -> None:
        with pytest.raises(DAGSecurityError):
            validate_expr("1 ** 2")


class TestRuntimeErrors:
    """运行时错误处理。"""

    def test_divide_by_zero_raises(self) -> None:
        tree = parse_expr("1 / a")
        with pytest.raises(DAGRuntimeError):
            evaluate(tree, {"a": 0.0})

    def test_sqrt_negative_raises(self) -> None:
        tree = parse_expr("sqrt(-1)")
        with pytest.raises(DAGRuntimeError):
            evaluate(tree, {})


class TestComplexExpressions:
    """复合表达式。"""

    def test_endfield_style_atk_zone(self) -> None:
        expr = "1 + atk_bonus / 100"
        assert evaluate(parse_expr(expr), {"atk_bonus": 25.0}) == pytest.approx(1.25)

    def test_defense_zone(self) -> None:
        expr = "100 / (100 + defense)"
        assert evaluate(parse_expr(expr), {"defense": 200.0}) == pytest.approx(100.0 / 300.0)

    def test_ability_formula(self) -> None:
        expr = "(total_attrs - 4 * 10) / 100 + 1"
        assert evaluate(parse_expr(expr), {"total_attrs": 80.0}) == pytest.approx(1.4)
