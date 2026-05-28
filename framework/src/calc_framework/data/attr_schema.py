#!/usr/bin/env python3
"""属性声明 Schema — 让适配器声明自己的属性结构，自动构建 DataContext。

用法::

    schema = AttributeSchema.from_file("attr_schema.json")
    ctx = schema.resolve(raw_data)
    errors = schema.validate(ctx)

适配器在 ``meta.json`` 中声明 ``attr_schema`` 路径后，
框架可自动加载并执行标准化转换。
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

AttrSource = Literal["character", "weapon", "equipment", "enemy", "computed"]
AttrType = Literal["float", "int", "bool", "str", "percent"]

VALID_SOURCES: set[str] = {"character", "weapon", "equipment", "enemy", "computed"}
VALID_TYPES: set[str] = {"float", "int", "bool", "str", "percent"}


class AttributeSchemaError(ValueError):
    """属性 Schema 相关错误。"""


@dataclass
class AttributeDecl:
    name: str
    type: AttrType = "float"
    source: AttrSource = "character"
    default: Any | None = None
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"name": self.name, "type": self.type, "source": self.source}
        if self.default is not None:
            d["default"] = self.default
        if self.description:
            d["description"] = self.description
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AttributeDecl:
        name = data.get("name")
        if not name or not isinstance(name, str):
            raise AttributeSchemaError(f"属性声明缺少有效的 'name': {data!r}")
        _type = data.get("type", "float")
        if _type not in VALID_TYPES:
            raise AttributeSchemaError(f"不支持的属性类型 {_type!r}, 有效值: {VALID_TYPES}")
        _source = data.get("source", "character")
        if _source not in VALID_SOURCES:
            raise AttributeSchemaError(f"不支持的 source {_source!r}, 有效值: {VALID_SOURCES}")
        return cls(
            name=name,
            type=_type,
            source=_source,
            default=data.get("default"),
            description=data.get("description", ""),
        )


@dataclass
class AttributeSchema:
    attributes: list[AttributeDecl] = field(default_factory=list)

    def _coerce(self, value: Any, decl: AttributeDecl) -> Any:
        if value is None:
            return decl.default
        if decl.type == "float":
            return float(value)
        if decl.type == "int":
            return int(value)
        if decl.type == "bool":
            return bool(value)
        if decl.type == "str":
            return str(value)
        if decl.type == "percent":
            return float(value)
        return value

    def resolve(self, raw_data: dict[str, dict[str, Any]]) -> dict[str, Any]:
        """将原始数据按 Schema 解析为标准 DataContext。

        Args:
            raw_data: 按 source 分组的原始属性值。
                如 ``{"character": {"基础攻击": 100}, "enemy": {"防御": 200}}``。

        Returns:
            符合 DataContext 格式的字典，每个 source 下的字段名直接暴露。
        """
        context: dict[str, dict[str, Any]] = {}
        for decl in self.attributes:
            if decl.source not in context:
                context[decl.source] = {}
            source_data = raw_data.get(decl.source, {})
            raw_value = source_data.get(decl.name)
            context[decl.source][decl.name] = self._coerce(raw_value, decl)
        for source in VALID_SOURCES:
            context.setdefault(source, {})
        return context

    def validate(self, context: dict[str, Any]) -> list[str]:
        """校验 DataContext 是否满足 Schema 要求。

        Returns:
            错误消息列表，为空表示校验通过。
        """
        errors: list[str] = []
        for decl in self.attributes:
            source_data = context.get(decl.source, {})
            value = source_data.get(decl.name)
            if value is None and decl.default is None:
                errors.append(
                    f"缺少必填属性 {decl.source}.{decl.name}"
                )
                continue
            if value is None:
                continue
            if decl.type == "float" and not isinstance(value, (int, float)):
                errors.append(
                    f"{decl.source}.{decl.name} 应为 {decl.type}, 实际 {type(value).__name__}"
                )
            if decl.type == "int" and not isinstance(value, int):
                errors.append(
                    f"{decl.source}.{decl.name} 应为 {decl.type}, 实际 {type(value).__name__}"
                )
            if decl.type == "bool" and not isinstance(value, bool):
                errors.append(
                    f"{decl.source}.{decl.name} 应为 {decl.type}, 实际 {type(value).__name__}"
                )
        return errors

    def to_dict(self) -> dict[str, Any]:
        return {"attributes": [a.to_dict() for a in self.attributes]}

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)

    def save(self, path: str | Path) -> None:
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.to_json())

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AttributeSchema:
        raw = data.get("attributes", data.get("attr"))
        if not isinstance(raw, list):
            raise AttributeSchemaError("Schema 缺少 'attributes' 列表")
        decls = [AttributeDecl.from_dict(item) for item in raw]
        return cls(attributes=decls)

    @classmethod
    def from_file(cls, path: str | Path) -> AttributeSchema:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)
