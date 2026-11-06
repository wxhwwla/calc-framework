# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""沙箱函数元信息 — 单元测试。"""

from __future__ import annotations

import pytest

from calc_framework.dag.sandbox import register_function, unregister_function
from calc_framework.dag.sandbox_config import list_function_specs


def test_list_function_specs_includes_builtins() -> None:
    specs = {item["name"]: item for item in list_function_specs()}

    assert "sqrt" in specs
    assert specs["sqrt"]["kind"] == "builtin"
    assert specs["sqrt"]["signature"]
    assert "integral" in specs


def test_list_function_specs_includes_custom_functions() -> None:
    def double(x: float) -> float:
        """返回两倍值。"""
        return x * 2

    register_function("mcp_test_double", double)
    try:
        specs = {item["name"]: item for item in list_function_specs()}
        assert specs["mcp_test_double"]["kind"] == "custom"
        assert "x" in specs["mcp_test_double"]["signature"]
        assert specs["mcp_test_double"]["description"] == "返回两倍值。"
    finally:
        unregister_function("mcp_test_double")


def test_list_function_specs_merges_duplicate_names_by_builtin_first() -> None:
    with pytest.raises(ValueError):
        register_function("sqrt", lambda x: x)
