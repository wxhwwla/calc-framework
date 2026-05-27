#!/usr/bin/env python3
"""DAG 异常类单元测试。"""


from calc_framework.dag.errors import (
    DAGCompileError,
    DAGCycleError,
    DAGError,
    DAGRuntimeError,
    DAGSecurityError,
)


class TestDAGErrors:
    """验证所有 DAG 异常类的继承关系与构造行为。"""

    def test_dag_error_is_base_exception(self) -> None:
        assert issubclass(DAGError, Exception)

    def test_compile_error_is_dag_error(self) -> None:
        assert issubclass(DAGCompileError, DAGError)

    def test_security_error_is_dag_error(self) -> None:
        assert issubclass(DAGSecurityError, DAGError)

    def test_runtime_error_is_dag_error(self) -> None:
        assert issubclass(DAGRuntimeError, DAGError)

    def test_cycle_error_is_dag_error(self) -> None:
        assert issubclass(DAGCycleError, DAGError)

    def test_compile_error_message_and_node_id(self) -> None:
        exc = DAGCompileError("解析失败: 非法语法", node_id="atk_sum")
        assert str(exc) == "解析失败: 非法语法"
        assert exc.node_id == "atk_sum"

    def test_security_error_message_and_node_type(self) -> None:
        exc = DAGSecurityError("禁止使用 import 语句", offending_node="Import")
        assert str(exc) == "禁止使用 import 语句"
        assert exc.offending_node == "Import"

    def test_dag_error_chaining(self) -> None:
        """所有 DAGError 子类都可以包装原始异常。"""
        inner = ValueError("原始错误")
        for cls in (DAGCompileError, DAGSecurityError, DAGRuntimeError, DAGCycleError):
            try:
                try:
                    raise inner
                except ValueError as e:
                    raise cls("外层信息") from e
            except cls as exc:
                assert exc.__cause__ is inner
