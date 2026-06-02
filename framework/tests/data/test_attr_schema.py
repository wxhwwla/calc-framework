#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""属性 Schema 单元测试。"""

from __future__ import annotationsimport jsonimport tempfilefrom pathlib import Pathimport pytestfrom calc_framework.data.attr_schema import (    AttributeDecl,    AttributeSchema,    AttributeSchemaError,)class TestAttributeDecl:
    def test_create_minimal(self):
        decl = AttributeDecl(name="攻击力", type="float", source="character")
        assert decl.name == "攻击力"
        assert decl.type == "float"
        assert decl.source == "character"
        assert decl.default is None

    def test_create_with_default(self):
        decl = AttributeDecl(name="暴击率", type="percent", source="character", default=0.05)
        assert decl.default == 0.05

    def test_from_dict_minimal(self):
        decl = AttributeDecl.from_dict({"name": "防御", "type": "int", "source": "enemy"})
        assert decl.name == "防御"
        assert decl.type == "int"
        assert decl.source == "enemy"

    def test_from_dict_defaults(self):
        decl = AttributeDecl.from_dict({"name": "攻击力"})
        assert decl.type == "float"
        assert decl.source == "character"

    def test_from_dict_missing_name(self):
        with pytest.raises(AttributeSchemaError, match="缺少有效的 'name'"):
            AttributeDecl.from_dict({"type": "float"})

    def test_from_dict_invalid_type(self):
        with pytest.raises(AttributeSchemaError, match="不支持的属性类型"):
            AttributeDecl.from_dict({"name": "x", "type": "complex"})

    def test_from_dict_invalid_source(self):
        with pytest.raises(AttributeSchemaError, match="不支持的 source"):
            AttributeDecl.from_dict({"name": "x", "source": "pet"})

    def test_to_dict(self):
        decl = AttributeDecl(name="攻击力", type="float", source="character")
        d = decl.to_dict()
        assert d == {"name": "攻击力", "type": "float", "source": "character"}

    def test_to_dict_with_default(self):
        decl = AttributeDecl(name="暴击率", type="percent", source="character", default=0.05)
        d = decl.to_dict()
        assert d["default"] == 0.05


class TestAttributeSchema:
    def test_empty_schema(self):
        schema = AttributeSchema()
        assert schema.attributes == []

    def test_from_dict_list(self):
        data = {
            "attributes": [
                {"name": "攻击力", "type": "float", "source": "character"},
                {"name": "防御", "type": "float", "source": "enemy", "default": 100},
            ]
        }
        schema = AttributeSchema.from_dict(data)
        assert len(schema.attributes) == 2
        assert schema.attributes[0].name == "攻击力"
        assert schema.attributes[1].name == "防御"
        assert schema.attributes[1].default == 100

    def test_from_dict_alias_attr(self):
        data = {
            "attr": [
                {"name": "HP", "type": "int", "source": "character"},
            ]
        }
        schema = AttributeSchema.from_dict(data)
        assert len(schema.attributes) == 1
        assert schema.attributes[0].name == "HP"

    def test_from_dict_missing_list(self):
        with pytest.raises(AttributeSchemaError, match="缺少 'attributes' 列表"):
            AttributeSchema.from_dict({"foo": "bar"})

    def test_from_file(self):
        data = {
            "attributes": [
                {"name": "ATK", "type": "float", "source": "character"},
            ]
        }
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            json.dump(data, f)
            fpath = f.name
        try:
            schema = AttributeSchema.from_file(fpath)
            assert len(schema.attributes) == 1
            assert schema.attributes[0].name == "ATK"
        finally:
            Path(fpath).unlink(missing_ok=True)

    def test_resolve_basic(self):
        schema = AttributeSchema.from_dict({
            "attributes": [
                {"name": "攻击力", "type": "float", "source": "character"},
                {"name": "防御", "type": "float", "source": "enemy"},
            ]
        })
        ctx = schema.resolve({
            "character": {"攻击力": 100},
            "enemy": {"防御": 200},
        })
        assert ctx["character"]["攻击力"] == 100.0
        assert ctx["enemy"]["防御"] == 200.0

    def test_resolve_type_coercion(self):
        schema = AttributeSchema.from_dict({
            "attributes": [
                {"name": "HP", "type": "int", "source": "character"},
                {"name": "暴击率", "type": "percent", "source": "character"},
            ]
        })
        ctx = schema.resolve({
            "character": {"HP": 1000, "暴击率": 0.5},
        })
        assert ctx["character"]["HP"] == 1000
        assert isinstance(ctx["character"]["HP"], int)
        assert ctx["character"]["暴击率"] == 0.5

    def test_resolve_missing_source_data(self):
        schema = AttributeSchema.from_dict({
            "attributes": [
                {"name": "攻击力", "type": "float", "source": "character"},
            ]
        })
        ctx = schema.resolve({})
        assert ctx["character"]["攻击力"] is None

    def test_resolve_default_fallback(self):
        schema = AttributeSchema.from_dict({
            "attributes": [
                {"name": "防御", "type": "float", "source": "enemy", "default": 100},
            ]
        })
        ctx = schema.resolve({"enemy": {}})
        assert ctx["enemy"]["防御"] == 100

    def test_resolve_all_sources_initialized(self):
        schema = AttributeSchema()
        ctx = schema.resolve({})
        for key in ("character", "weapon", "equipment", "enemy", "computed"):
            assert key in ctx
            assert ctx[key] == {}

    def test_validate_ok(self):
        schema = AttributeSchema.from_dict({
            "attributes": [
                {"name": "攻击力", "type": "float", "source": "character"},
            ]
        })
        ctx = {"character": {"攻击力": 100.0}}
        errors = schema.validate(ctx)
        assert errors == []

    def test_validate_missing_required(self):
        schema = AttributeSchema.from_dict({
            "attributes": [
                {"name": "攻击力", "type": "float", "source": "character"},
            ]
        })
        ctx = {"character": {}}
        errors = schema.validate(ctx)
        assert len(errors) == 1
        assert "缺少必填属性" in errors[0]

    def test_validate_type_mismatch(self):
        schema = AttributeSchema.from_dict({
            "attributes": [
                {"name": "HP", "type": "int", "source": "character"},
            ]
        })
        ctx = {"character": {"HP": "很多"}}
        errors = schema.validate(ctx)
        assert len(errors) == 1
        assert "应为 int" in errors[0]

    def test_validate_default_suppresses_missing(self):
        schema = AttributeSchema.from_dict({
            "attributes": [
                {"name": "暴击率", "type": "percent", "source": "character", "default": 0.05},
            ]
        })
        ctx = {"character": {}}
        errors = schema.validate(ctx)
        assert errors == []

    def test_validate_float_accepts_int(self):
        schema = AttributeSchema.from_dict({
            "attributes": [
                {"name": "攻击力", "type": "float", "source": "character"},
            ]
        })
        ctx = {"character": {"攻击力": 100}}
        errors = schema.validate(ctx)
        assert errors == []

    def test_to_dict_roundtrip(self):
        schema = AttributeSchema.from_dict({
            "attributes": [
                {"name": "ATK", "type": "float", "source": "character"},
                {"name": "DEF", "type": "float", "source": "enemy", "default": 100},
            ]
        })
        d = schema.to_dict()
        assert len(d["attributes"]) == 2
        assert d["attributes"][0]["name"] == "ATK"
        assert d["attributes"][1]["default"] == 100

    def test_save_and_reload(self):
        schema = AttributeSchema.from_dict({
            "attributes": [
                {"name": "力量", "type": "float", "source": "character"},
            ]
        })
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            fpath = f.name
        try:
            schema.save(fpath)
            loaded = AttributeSchema.from_file(fpath)
            assert len(loaded.attributes) == 1
            assert loaded.attributes[0].name == "力量"
        finally:
            Path(fpath).unlink(missing_ok=True)

    def test_endfield_schema_file(self):
        schema_path = Path(__file__).parents[3] / "framework" / "adapters" / "endfield" / "attr_schema.json"
        assert schema_path.exists(), f"attr_schema.json not found at {schema_path}"
        schema = AttributeSchema.from_file(schema_path)
        names = {a.name for a in schema.attributes}
        assert "基础攻击" in names
        assert "暴击率" in names
        assert "防御" in names
        assert "攻击力+" in names
