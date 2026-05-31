# SPDX-License-Identifier: AGPL-3.0
"""适配包 JSON Schema 定义和校验。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ADAPTER_PACKAGE_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft-07/schema#",
    "$id": "https://calc-framework.github.io/schemas/adapter-package.json",
    "title": "Calc Framework 适配包",
    "description": "游戏适配包的元信息定义（meta.json）",
    "type": "object",
    "required": ["schema_version", "name", "dag_files", "description"],
    "properties": {
        "schema_version": {
            "type": "string",
            "description": "适配包格式版本",
            "enum": ["adapter-v1"],
        },
        "name": {
            "type": "string",
            "description": "适配器名称（唯一标识）",
            "minLength": 1,
        },
        "version": {
            "type": "string",
            "description": "语义版本号",
            "pattern": "^\\d+\\.\\d+\\.\\d+$",
        },
        "description": {
            "type": "string",
            "description": "适配器描述",
        },
        "author": {
            "type": "string",
            "description": "作者",
        },
        "game": {
            "type": "string",
            "description": "游戏名称（如「明日方舟：终末地」「卡牌RPG演示」）",
        },
        "tags": {
            "type": "array",
            "items": {"type": "string"},
            "description": "标签（如 rpg, action, strategy）",
        },
        "dag_files": {
            "type": "array",
            "items": {"type": "string"},
            "description": "DAG 公式 JSON 文件列表（相对于适配包根目录）",
            "minItems": 1,
        },
        "functions": {
            "type": "object",
            "additionalProperties": {"type": "string"},
            "description": "自定义函数映射: {函数名: 文件路径}",
        },
        "attr_schema": {
            "type": "string",
            "description": "属性声明 Schema 文件路径",
        },
        "plugins": {
            "type": "array",
            "items": {"type": "string"},
            "description": "依赖的插件列表",
        },
        "screenshots": {
            "type": "array",
            "items": {"type": "string"},
            "description": "截图路径列表",
        },
    },
}


def validate_against_schema(data: dict[str, Any]) -> list[str]:
    """校验数据是否符合适配包 Schema。

    使用轻量手动校验（避免引入 jsonschema 依赖）。
    Returns:
        错误信息列表，空列表表示通过。
    """
    errors: list[str] = []

    required = ADAPTER_PACKAGE_SCHEMA.get("required", [])
    for field in required:
        if field not in data:
            errors.append(f"缺少必填字段: {field}")

    if not errors:
        if data.get("schema_version") not in ("adapter-v1",):
            errors.append(f"不支持的 schema_version: {data.get('schema_version')}")

        name = data.get("name", "")
        if not isinstance(name, str) or not name.strip():
            errors.append("name 不能为空")

        dag_files = data.get("dag_files", [])
        if not isinstance(dag_files, list) or len(dag_files) == 0:
            errors.append("dag_files 不能为空")

    return errors


def validate_package(adapter_dir: str | Path) -> list[str]:
    """校验适配包目录的 meta.json 合法性。"""
    path = Path(adapter_dir)
    meta_path = path / "meta.json"
    if not meta_path.is_file():
        return [f"未找到 {meta_path}"]

    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return [f"meta.json 解析失败: {exc}"]

    errors = validate_against_schema(meta)

    dag_files = meta.get("dag_files", [])
    for dag_file in dag_files:
        dag_path = path / dag_file
        if not dag_path.is_file():
            errors.append(f"DAG 文件未找到: {dag_file}")

    return errors
