#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""OpenAPI 契约归一化与校验。

把 FastAPI 生成的 schema 归一化为稳定、可提交的契约（路径、方法、
operationId、tags、参数、请求体/响应模型与状态码），避免描述文字等
易变字段造成噪音。CI 中由 ``web/backend/tests/test_openapi_contract.py``
调用，禁止路由或模型悄悄漂移。

用法（仓库根目录）::

    python tools/quality/contracts/check_openapi.py
    python tools/quality/contracts/check_openapi.py --write
"""

from __future__ import annotations

import argparse
import difflib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
CONTRACT_PATH = REPO / "docs" / "openapi-contract.json"
HTTP_METHODS = ("get", "post", "put", "patch", "delete", "options", "head", "trace")
COMPOSITE_KEYS = ("anyOf", "oneOf", "allOf")


def _normalize_schema(node: object) -> dict:
    """把 JSON Schema 归一化为稳定结构：``$ref``、组合类型、数组与标量类型。"""
    if not isinstance(node, dict):
        return {}
    if "$ref" in node and isinstance(node["$ref"], str):
        return {"$ref": node["$ref"].rsplit("/", 1)[-1]}
    for key in COMPOSITE_KEYS:
        if key in node and isinstance(node[key], list):
            variants = [_normalize_schema(item) for item in node[key]]
            variants.sort(key=lambda item: json.dumps(item, sort_keys=True, ensure_ascii=False))
            return {key: variants}
    node_type = node.get("type")
    if node_type == "array":
        return {"type": "array", "items": _normalize_schema(node.get("items", {}))}
    if isinstance(node_type, str):
        return {"type": node_type}
    if isinstance(node.get("properties"), dict):
        return {"properties": sorted(node["properties"])}
    return {}


def _normalize_content(content: object) -> dict:
    if not isinstance(content, dict):
        return {}
    return {
        media_type: {"schema": _normalize_schema(media.get("schema", {}))}
        for media_type, media in sorted(content.items())
        if isinstance(media, dict)
    }


def _normalize_parameters(parameters: object) -> list[dict]:
    if not isinstance(parameters, list):
        return []
    normalized = [
        {
            "in": parameter.get("in"),
            "name": parameter.get("name"),
            "required": bool(parameter.get("required", False)),
            "schema": _normalize_schema(parameter.get("schema", {})),
        }
        for parameter in parameters
        if isinstance(parameter, dict)
    ]
    normalized.sort(key=lambda item: (str(item["in"]), str(item["name"])))
    return normalized


def _normalize_request_body(request_body: object) -> dict | None:
    if not isinstance(request_body, dict):
        return None
    return {
        "required": bool(request_body.get("required", False)),
        "content": _normalize_content(request_body.get("content", {})),
    }


def _normalize_security(security: object) -> list[list[str]] | None:
    if security is None:
        return None
    if not isinstance(security, list):
        return []
    requirements = [sorted(key for key in requirement if isinstance(requirement, dict)) for requirement in security]
    requirements = [item for item in requirements if item]
    requirements.sort()
    return requirements


def contract_from_schema(schema: dict) -> dict:
    """从 FastAPI schema 提取稳定契约。

    Args:
        schema: ``FastAPI.openapi()`` 的返回值

    Returns:
        ``{"paths": {path: {method: operation}}}``
    """
    paths: dict[str, dict] = {}
    for path, item in sorted((schema.get("paths") or {}).items()):
        # 只收录 API 路径；根路径重定向等页面路由取决于前端构建产物是否存在于工作树，
        # 纳入契约会让干净 clone / CI 与本地开发机产生无意义差异。
        if not path.startswith("/api/") or not isinstance(item, dict):
            continue
        operations: dict[str, dict] = {}
        for method, operation in sorted(item.items()):
            if method not in HTTP_METHODS or not isinstance(operation, dict):
                continue
            responses = {
                str(code): {"content": _normalize_content(response.get("content", {}))}
                for code, response in sorted((operation.get("responses") or {}).items())
                if isinstance(response, dict)
            }
            operations[method] = {
                "operationId": operation.get("operationId"),
                "tags": sorted(operation.get("tags", [])),
                "security": _normalize_security(operation.get("security")),
                "parameters": _normalize_parameters(operation.get("parameters", [])),
                "requestBody": _normalize_request_body(operation.get("requestBody")),
                "responses": responses,
            }
        paths[path] = operations
    return {"paths": paths}


def diff_contracts(expected: dict, actual: dict) -> list[str]:
    """返回两份契约的 unified diff 行；无差异时为空列表。"""
    expected_text = json.dumps(expected, ensure_ascii=False, indent=2, sort_keys=True).splitlines()
    actual_text = json.dumps(actual, ensure_ascii=False, indent=2, sort_keys=True).splitlines()
    return list(
        difflib.unified_diff(
            expected_text,
            actual_text,
            fromfile="committed",
            tofile="generated",
            lineterm="",
        )
    )


def load_contract(path: Path = CONTRACT_PATH) -> dict:
    """读取已提交的契约文件。"""
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"OpenAPI 契约格式错误：{path}")
    return data


def _ensure_import_paths() -> None:
    for path in (REPO, REPO / "web" / "backend", REPO / "framework" / "src"):
        if str(path) not in sys.path:
            sys.path.insert(0, str(path))


def build_contract() -> dict:
    """导入 FastAPI app 并生成当前契约。"""
    _ensure_import_paths()
    from web.backend.main import app

    return contract_from_schema(app.openapi())


def write_contract(path: Path = CONTRACT_PATH) -> dict:
    """生成契约并写入文件，返回契约内容。"""
    contract = build_contract()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(contract, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return contract


def main(argv: list[str] | None = None) -> int:
    """CLI 入口：校验或重写 OpenAPI 契约。

    Returns:
        退出码（0 通过，1 失败）
    """
    parser = argparse.ArgumentParser(description="校验 OpenAPI 契约")
    parser.add_argument("--write", action="store_true", help="用当前 app 重写契约文件")
    parser.add_argument("--contract", type=Path, default=CONTRACT_PATH)
    args = parser.parse_args(argv)

    if args.write:
        contract = write_contract(args.contract)
        print(f"已写入 OpenAPI 契约：{args.contract}（{len(contract['paths'])} 条路径）")
        return 0

    expected = load_contract(args.contract)
    differences = diff_contracts(expected, build_contract())
    for line in differences:
        print(line)
    if differences:
        print("OpenAPI 契约检查失败：请运行 python tools/quality/contracts/check_openapi.py --write")
        return 1
    print(f"OpenAPI 契约检查通过（{len(expected['paths'])} 条路径）。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
