#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# SPDX-License-Identifier: AGPL-3.0
"""沙箱控制流扩展测试 — 比较、布尔、三元与安全边界。"""

import pytest

from calc_framework.dag.errors import DAGRuntimeError, DAGSecurityError
from calc_framework.dag.sandbox import (
    evaluate,
    parse_expr,
    register_function,
    unregister_function,
)


class TestComparisons:
    """比较运算符。"""

    @pytest.mark.parametrize(
        ("expr", "expected"),
        [
            ("a < b", 0.0),
            ("a <= b", 1.0),
            ("a > b", 0.0),
            ("a >= b", 1.0),
            ("a == b", 1.0),
            ("a != b", 0.0),
        ],
    )
    def test_operators(self, expr: str, expected: float) -> None:
        assert evaluate(parse_expr(expr), {"a": 1.0, "b": 1.0}) == pytest.approx(expected)

    def test_chained_true(self) -> None:
        assert evaluate(parse_expr("1 < 2 < 3"), {}) == pytest.approx(1.0)

    def test_chained_false(self) -> None:
        assert evaluate(parse_expr("1 < 3 < 2"), {}) == pytest.approx(0.0)

    def test_chained_short_circuits(self) -> None:
        assert evaluate(parse_expr("1 > 2 > (1 / 0)"), {}) == pytest.approx(0.0)

    def test_chained_comparator_evaluated_once(self) -> None:
        calls = {"n": 0}

        def next_val() -> float:
            calls["n"] += 1
            return 2.0

        register_function("next_val", next_val)
        try:
            assert evaluate(parse_expr("1 < next_val() < 3"), {}) == pytest.approx(1.0)
        finally:
            unregister_function("next_val")
        assert calls["n"] == 1

    def test_result_is_float(self) -> None:
        result = evaluate(parse_expr("1 < 2"), {})

        assert isinstance(result, float)
        assert result == 1.0

    def test_type_mismatch_raises(self) -> None:
        with pytest.raises(DAGRuntimeError, match="比较"):
            evaluate(parse_expr("1 < 'a'"), {})


class TestBooleanLogic:
    """布尔运算符与短路语义。"""

    def test_not_true(self) -> None:
        assert evaluate(parse_expr("not 0"), {}) == pytest.approx(1.0)

    def test_not_false(self) -> None:
        assert evaluate(parse_expr("not 1"), {}) == pytest.approx(0.0)

    def test_and_returns_last_operand(self) -> None:
        assert evaluate(parse_expr("1 and 2"), {}) == pytest.approx(2.0)

    def test_and_returns_first_falsy(self) -> None:
        assert evaluate(parse_expr("0 and 2"), {}) == pytest.approx(0.0)

    def test_or_returns_first_truthy(self) -> None:
        assert evaluate(parse_expr("1 or 2"), {}) == pytest.approx(1.0)

    def test_or_returns_last_operand(self) -> None:
        assert evaluate(parse_expr("0 or 2"), {}) == pytest.approx(2.0)

    def test_and_short_circuits(self) -> None:
        assert evaluate(parse_expr("0 and (1 / 0)"), {}) == pytest.approx(0.0)

    def test_or_short_circuits(self) -> None:
        assert evaluate(parse_expr("1 or (1 / 0)"), {}) == pytest.approx(1.0)

    def test_precedence(self) -> None:
        assert evaluate(parse_expr("1 and 0 or 2"), {}) == pytest.approx(2.0)

    def test_nested_boolean(self) -> None:
        assert evaluate(parse_expr("not (1 and 0)"), {}) == pytest.approx(1.0)


class TestTernary:
    """Python 三元表达式。"""

    def test_true_branch(self) -> None:
        assert evaluate(parse_expr("1 if a else 2"), {"a": 1.0}) == pytest.approx(1.0)

    def test_false_branch(self) -> None:
        assert evaluate(parse_expr("1 if a else 2"), {"a": 0.0}) == pytest.approx(2.0)

    def test_dead_branch_not_evaluated_true(self) -> None:
        assert evaluate(parse_expr("1 if 1 else (1 / 0)"), {}) == pytest.approx(1.0)

    def test_dead_branch_not_evaluated_false(self) -> None:
        assert evaluate(parse_expr("(1 / 0) if 0 else 2"), {}) == pytest.approx(2.0)

    def test_nested_ternary(self) -> None:
        expr = "1 if a else 2 if b else 3"

        assert evaluate(parse_expr(expr), {"a": 1.0, "b": 1.0}) == pytest.approx(1.0)
        assert evaluate(parse_expr(expr), {"a": 0.0, "b": 1.0}) == pytest.approx(2.0)
        assert evaluate(parse_expr(expr), {"a": 0.0, "b": 0.0}) == pytest.approx(3.0)


class TestNewSyntaxSecurity:
    """新增语法的安全边界。"""

    @pytest.mark.parametrize("expr", ["1 in a", "1 not in a", "1 is a", "1 is not a"])
    def test_membership_and_identity_rejected(self, expr: str) -> None:
        with pytest.raises(DAGSecurityError):
            parse_expr(expr)

    def test_ifexp_dead_branch_validated(self) -> None:
        with pytest.raises(DAGSecurityError):
            parse_expr("1 if 1 else (lambda: 1)")

    def test_boolop_dead_operand_validated(self) -> None:
        with pytest.raises(DAGSecurityError):
            parse_expr("0 and __import__('os')")

    def test_compare_comparator_validated(self) -> None:
        with pytest.raises(DAGSecurityError):
            parse_expr("1 < obj.attr")
