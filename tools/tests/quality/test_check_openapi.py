# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""OpenAPI 契约归一化的回归测试。"""

from __future__ import annotations

from tools.quality.contracts import check_openapi


def _schema() -> dict:
    return {
        "paths": {
            "/api/items/{item_id}": {
                "get": {
                    "operationId": "get_item",
                    "tags": ["items"],
                    "parameters": [
                        {"name": "item_id", "in": "path", "required": True, "schema": {"type": "string"}},
                        {"name": "q", "in": "query", "required": False, "schema": {"type": "integer"}},
                    ],
                    "responses": {
                        "200": {
                            "description": "ok",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Item"}}},
                        }
                    },
                }
            }
        }
    }


def test_contract_keeps_route_method_params_and_models() -> None:
    """契约包含路径、方法、参数、请求/响应模型与错误码。"""
    contract = check_openapi.contract_from_schema(_schema())

    operation = contract["paths"]["/api/items/{item_id}"]["get"]
    assert operation["operationId"] == "get_item"
    assert operation["parameters"] == [
        {"in": "path", "name": "item_id", "required": True, "schema": {"type": "string"}},
        {"in": "query", "name": "q", "required": False, "schema": {"type": "integer"}},
    ]
    assert operation["responses"]["200"]["content"]["application/json"]["schema"] == {"$ref": "Item"}


def test_contract_is_order_independent() -> None:
    """同一 schema 的不同键顺序应产生相同契约。"""
    first = _schema()
    second = {
        "paths": {
            "/api/items/{item_id}": {
                "get": {
                    "responses": first["paths"]["/api/items/{item_id}"]["get"]["responses"],
                    "parameters": list(reversed(first["paths"]["/api/items/{item_id}"]["get"]["parameters"])),
                    "tags": ["items"],
                    "operationId": "get_item",
                }
            }
        }
    }

    assert check_openapi.contract_from_schema(first) == check_openapi.contract_from_schema(second)


def test_diff_reports_removed_route() -> None:
    """删除路由时能给出可读差异。"""
    old = check_openapi.contract_from_schema(_schema())
    new = check_openapi.contract_from_schema({"paths": {}})

    differences = check_openapi.diff_contracts(old, new)

    assert any("/api/items/{item_id}" in line for line in differences)
