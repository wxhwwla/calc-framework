# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""
Coverage expansion tests for calc_framework.

Covers under-tested areas:
- inverse/ — registry, engine, schema, strategies, advanced fitters
- data/ — json_loader, attr_schema, loader, schema validation
- config/ — adapter discovery, manager edge cases, file_watcher
- plugin/ — registration, builtin validation, lifecycle
"""

from __future__ import annotations

import json
import math
import sys
import tempfile
from pathlib import Path

import pytest

# path setup for framework tests at root level
_SRC = Path(__file__).resolve().parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

# =========================================================================
# Inverse Engine — Registry & FormulaType
# =========================================================================


class TestInverseRegistryExpanded:
    """Registry registration/unregistration and edge cases."""

    def test_register_multiple_types(self):
        from calc_framework.inverse.base import FloorFormulaFitter
        from calc_framework.inverse.registry import FormulaType, Registry

        r = Registry()
        r.register(FormulaType(id="t1", fitter=FloorFormulaFitter()))
        r.register(FormulaType(id="t2", fitter=FloorFormulaFitter()))
        r.register(FormulaType(id="t3", fitter=FloorFormulaFitter()))
        assert len(r.list_ids()) == 3
        assert "t1" in r.list_ids()
        assert "t2" in r.list_ids()
        assert "t3" in r.list_ids()

    def test_register_overwrites_existing(self):
        from calc_framework.inverse.base import FloorFormulaFitter
        from calc_framework.inverse.registry import FormulaType, Registry

        r = Registry()
        ft1 = FormulaType(id="same", name="First", fitter=FloorFormulaFitter())
        ft2 = FormulaType(id="same", name="Second", fitter=FloorFormulaFitter())
        r.register(ft1)
        r.register(ft2)
        assert r.get("same").name == "Second"

    def test_global_registry_has_four_types(self):
        from calc_framework.inverse.registry import registry

        ids = registry.list_ids()
        assert "floor_linear" in ids
        assert "exponential" in ids
        assert "piecewise" in ids
        assert "threshold" in ids

    def test_global_registry_get_default(self):
        from calc_framework.inverse.registry import registry

        ft = registry.get("floor_linear")
        assert ft.id == "floor_linear"
        assert ft.fitter is not None

    def test_list_types_returns_formula_type_objects(self):
        from calc_framework.inverse.registry import registry

        types = registry.list_types()
        assert len(types) >= 4
        for ft in types:
            assert ft.id

    def test_registry_get_unknown_key(self):
        from calc_framework.inverse.registry import registry

        with pytest.raises(KeyError, match="未知公式类型"):
            registry.get("completely_made_up_type")

    def test_formula_type_without_fitter_to_dict_raises(self):
        from calc_framework.inverse.registry import FormulaType

        ft = FormulaType(id="bare")
        with pytest.raises(ValueError, match="未绑定"):
            ft.to_dict()

    def test_formula_type_to_dict_includes_param_descriptions(self):
        from calc_framework.inverse.base import FloorFormulaFitter
        from calc_framework.inverse.registry import FormulaType

        ft = FormulaType(
            id="desc_test",
            name="DescTest",
            description="A test description",
            fitter=FloorFormulaFitter(),
        )
        d = ft.to_dict()
        assert d["id"] == "desc_test"
        assert d["name"] == "DescTest"
        assert d["description"] == "A test description"
        assert "param_names" in d
        assert "param_descriptions" in d


# =========================================================================
# Inverse Engine — Engine fit_auto and convenience layer
# =========================================================================


class TestInverseEngineExpanded:
    """InverseEngine fit_auto, data_to_params, params_to_curve expanded tests."""

    def test_data_to_params_simple(self):
        from calc_framework.inverse.engine import InverseEngine

        engine = InverseEngine()
        params = engine.data_to_params([100, 105, 110, 115, 120])
        assert params.base == 100
        assert params.growth == 5
        assert params.divisor == 1

    def test_data_to_params_with_divisor(self):
        from calc_framework.inverse.engine import InverseEngine

        # data where growth/divisor implies a non-trivial divisor
        data = [29 + math.floor((163 * i) / 57) for i in range(90)]
        engine = InverseEngine()
        params = engine.data_to_params(data)
        assert params.base == 29
        assert params.divisor > 0

    def test_data_to_params_raises_on_failure(self):
        from calc_framework.inverse.engine import InverseEngine

        engine = InverseEngine()
        with pytest.raises(ValueError, match="拟合失败"):
            engine.data_to_params([1, 999999, 3])

    def test_params_to_curve_from_dict(self):
        from calc_framework.inverse.engine import InverseEngine

        engine = InverseEngine()
        curve = engine.params_to_curve(
            {"base": 100, "growth": 5, "divisor": 1, "offset": 0},
            num_levels=10,
        )
        assert len(curve) == 10
        assert curve[0] == 100.0
        assert curve[9] == 145.0

    def test_params_to_curve_with_overrides(self):
        from calc_framework.inverse.base import GrowthParams
        from calc_framework.inverse.engine import InverseEngine

        engine = InverseEngine()
        params = GrowthParams(base=100, growth=5, divisor=1)
        curve = engine.params_to_curve(
            params,
            num_levels=12,
            level_overrides={10: 200.0, 11: 220.0, 12: 240.0},
        )
        # levels 1-9 follow formula, 10-12 are overridden
        assert curve[0] == 100.0  # lv1
        assert curve[8] == 140.0  # lv9
        assert curve[9] == 200.0  # lv10 overridden
        assert curve[10] == 220.0  # lv11 overridden
        assert curve[11] == 240.0  # lv12 overridden

    def test_params_to_curve_decimal_with_overrides(self):
        from calc_framework.inverse.base import GrowthParams
        from calc_framework.inverse.engine import InverseEngine

        engine = InverseEngine()
        params = GrowthParams(base=10.0, growth=1.0, divisor=2, is_decimal=True)
        curve = engine.params_to_curve(
            params,
            num_levels=5,
            level_overrides={3: 99.9},
        )
        assert curve[0] == 10.0
        assert curve[1] == 10.5
        assert curve[2] == 99.9  # overridden
        assert len(curve) == 5

    def test_compute_accepts_growth_params_directly(self):
        from calc_framework.inverse.base import GrowthParams
        from calc_framework.inverse.engine import InverseEngine

        engine = InverseEngine()
        params = GrowthParams(base=50, growth=10, divisor=1)
        result = engine.compute("floor_linear", params, num_levels=5)
        assert result == [50.0, 60.0, 70.0, 80.0, 90.0]

    def test_validate_accepts_growth_params_directly(self):
        from calc_framework.inverse.base import GrowthParams
        from calc_framework.inverse.engine import InverseEngine

        engine = InverseEngine()
        params = GrowthParams(base=100, growth=5, divisor=1)
        data = [100, 105, 110, 115, 120]
        result = engine.validate("floor_linear", params, data)
        assert result.is_exact

    def test_fit_auto_returns_best_formula(self):
        from calc_framework.inverse.engine import InverseEngine

        engine = InverseEngine()
        data = [100 + i * 5 for i in range(9)]
        result = engine.fit_auto(data)
        assert result is not None
        formula_id, fit_result = result
        assert formula_id == "floor_linear"
        assert fit_result.is_exact

    def test_fit_auto_with_non_linear_data(self):
        from calc_framework.inverse.engine import InverseEngine

        engine = InverseEngine()
        # Data that no formula can fit well
        data = [1, 1000, 2, 2000, 3, 3000]
        result = engine.fit_auto(data)
        # May return None or some result
        if result is not None:
            assert isinstance(result, tuple)
            assert len(result) == 2

    def test_list_formula_types_returns_all(self):
        from calc_framework.inverse.engine import InverseEngine

        engine = InverseEngine()
        types = engine.list_formula_types()
        assert len(types) >= 4
        for t in types:
            assert "id" in t
            assert "name" in t

    def test_fit_with_custom_num_levels(self):
        from calc_framework.inverse.engine import InverseEngine

        engine = InverseEngine()
        data = [100 + i * 3 for i in range(50)]
        result = engine.fit(data, "floor_linear", num_levels=50)
        assert result.is_exact
        assert result.params["growth"] == 3

    def test_fit_with_options_passthrough(self):
        from calc_framework.inverse.engine import InverseEngine

        engine = InverseEngine()
        data = [50 + i * 2 for i in range(10)]
        result = engine.fit(
            data,
            "floor_linear",
            divisor_range=(1, 10),
            growth_range=(1, 50),
        )
        assert result.is_exact


# =========================================================================
# Inverse Schema — GameInverseAdapter and InverseSchema
# =========================================================================


class TestInverseSchemaExpanded:
    """InverseSchema and GameInverseAdapter tests."""

    def test_schema_creation_defaults(self):
        from calc_framework.inverse.schema import InverseSchema

        s = InverseSchema(length=90)
        assert s.length == 90
        assert s.formula_id == "floor_linear"
        assert s.label == ""
        assert s.special_indices is None
        assert s.search_options is None

    def test_schema_extract_base_data_no_special(self):
        from calc_framework.inverse.schema import InverseSchema

        s = InverseSchema(length=10, label="Test")
        data = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
        extracted = s.extract_base_data(data)
        assert list(extracted) == data

    def test_schema_extract_base_data_with_special(self):
        from calc_framework.inverse.schema import InverseSchema

        s = InverseSchema(length=12, special_indices=[9, 10, 11])
        data = [float(i) for i in range(1, 13)]
        extracted = s.extract_base_data(data)
        assert list(extracted) == [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0]

    def test_schema_extract_special_values(self):
        from calc_framework.inverse.schema import InverseSchema

        s = InverseSchema(length=12, special_indices=[9, 10, 11])
        data = [float(i) for i in range(1, 13)]
        special = s.extract_special_values(data)
        assert special == [10.0, 11.0, 12.0]

    def test_schema_search_options(self):
        from calc_framework.inverse.schema import InverseSchema

        s = InverseSchema(
            length=30,
            search_options={"divisor_range": (1, 100), "growth_range": (1, 200)},
        )
        assert s.search_options["divisor_range"] == (1, 100)
        assert s.search_options["growth_range"] == (1, 200)


class TestGameInverseAdapter:
    """GameInverseAdapter with concrete implementations."""

    def _make_adapter(self, engine=None):
        from calc_framework.inverse.schema import GameInverseAdapter, InverseSchema

        class _TestAdapter(GameInverseAdapter):
            @property
            def schemas(self):
                return [
                    InverseSchema(length=10, label="10-level"),
                    InverseSchema(length=12, label="12-level", special_indices=[9, 10, 11]),
                    InverseSchema(
                        length=30,
                        label="30-level custom",
                        search_options={"divisor_range": (1, 50)},
                    ),
                ]

            def default_formula(self):
                return "floor_linear"

        return _TestAdapter(engine=engine)

    def test_adapter_fit_matches_by_length(self):
        adapter = self._make_adapter()
        data = [100.0 + i * 5 for i in range(10)]
        result = adapter.fit(data)
        assert result.is_exact
        assert result.params["growth"] == 5

    def test_adapter_fit_with_special_indices(self):
        adapter = self._make_adapter()
        # 12 data points: lv1-lv9 follow formula, lv10-12 are special
        data = [100.0 + i * 5 for i in range(9)] + [200.0, 220.0, 240.0]
        result = adapter.fit(data)
        assert result.is_exact
        assert result.params.get("special_values") == [200.0, 220.0, 240.0]

    def test_adapter_fit_no_match_raises(self):
        adapter = self._make_adapter()
        with pytest.raises(ValueError, match="不支持的数据长度"):
            adapter.fit([1.0, 2.0, 3.0])  # length 3 doesn't match any schema

    def test_adapter_compute_uses_default_formula(self):
        adapter = self._make_adapter()
        from calc_framework.inverse.base import GrowthParams

        params = GrowthParams(base=100, growth=5, divisor=1)
        curve = adapter.compute(params, num_levels=10)
        assert len(curve) == 10
        assert curve[0] == 100.0

    def test_adapter_compute_with_explicit_formula(self):
        adapter = self._make_adapter()
        from calc_framework.inverse.base import GrowthParams

        params = GrowthParams(base=100, growth=5, divisor=1)
        curve = adapter.compute(params, num_levels=10, formula_id="floor_linear")
        assert len(curve) == 10
        assert curve[0] == 100.0

    def test_adapter_validate(self):
        adapter = self._make_adapter()
        from calc_framework.inverse.base import GrowthParams

        params = GrowthParams(base=100, growth=5, divisor=1)
        data = [100.0 + i * 5 for i in range(10)]
        result = adapter.validate(params, data)
        assert result.is_exact

    def test_adapter_data_to_params(self):
        adapter = self._make_adapter()
        data = [100.0 + i * 5 for i in range(10)]
        params = adapter.data_to_params(data)
        assert params.base == 100
        assert params.growth == 5

    def test_adapter_data_to_params_raises_on_bad_data(self):
        adapter = self._make_adapter()
        with pytest.raises(ValueError, match="拟合失败"):
            adapter.data_to_params([1.0, 999999.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0])

    def test_adapter_fit_special_logic_hook_default(self):
        from calc_framework.inverse.schema import GameInverseAdapter, InverseSchema

        class _NoHookAdapter(GameInverseAdapter):
            @property
            def schemas(self):
                return [InverseSchema(length=5, label="5-level")]

            def default_formula(self):
                return "floor_linear"

        adapter = _NoHookAdapter()
        data = [100.0 + i * 5 for i in range(5)]
        result = adapter.fit(data)
        assert result.is_exact

    def test_adapter_on_no_match_custom(self):
        from calc_framework.inverse.schema import GameInverseAdapter, InverseSchema

        class _CustomErrorAdapter(GameInverseAdapter):
            @property
            def schemas(self):
                return [InverseSchema(length=5)]

            def default_formula(self):
                return "floor_linear"

            def on_no_match(self, data):
                raise RuntimeError(f"Custom error for len={len(data)}")

        adapter = _CustomErrorAdapter()
        with pytest.raises(RuntimeError, match="Custom error"):
            adapter.fit([1.0])


# =========================================================================
# GrowthParams — data class
# =========================================================================


class TestGrowthParamsExpanded:
    """GrowthParams dataclass forms and conversions."""

    def test_default_values(self):
        from calc_framework.inverse.base import GrowthParams

        p = GrowthParams(base=100, growth=5, divisor=1)
        assert p.base == 100
        assert p.growth == 5
        assert p.offset == 0.0
        assert p.is_decimal is False
        assert p.special_values is None

    def test_tuple_property(self):
        from calc_framework.inverse.base import GrowthParams

        p = GrowthParams(base=100, growth=5, divisor=1, offset=0)
        assert p.tuple() == (100, 5, 1, 0)

    def test_to_dict_and_from_dict_roundtrip(self):
        from calc_framework.inverse.base import GrowthParams

        p = GrowthParams(
            base=100,
            growth=5,
            divisor=1,
            offset=3,
            is_decimal=True,
            special_values=[200.0, 220.0],
        )
        d = p.to_dict()
        p2 = GrowthParams.from_dict(d)
        assert p2.base == 100
        assert p2.growth == 5
        assert p2.offset == 3
        assert p2.is_decimal is True
        assert p2.special_values == [200.0, 220.0]

    def test_from_dict_minimal(self):
        from calc_framework.inverse.base import GrowthParams

        p = GrowthParams.from_dict({"base": 50, "growth": 10, "divisor": 1})
        assert p.base == 50
        assert p.growth == 10
        assert p.offset == 0.0
        assert p.is_decimal is False

    def test_fit_result_growth_params_property(self):
        from calc_framework.inverse.base import FitResult

        r = FitResult(
            params={"base": 100, "growth": 5, "divisor": 1, "offset": 0},
            is_exact=True,
        )
        gp = r.growth_params
        assert gp is not None
        assert gp.base == 100

    def test_fit_result_growth_params_returns_none(self):
        from calc_framework.inverse.base import FitResult

        r = FitResult(params={}, is_exact=True)
        assert r.growth_params is None


# =========================================================================
# Data Layer — JsonDataLoader
# =========================================================================


class TestJsonDataLoader:
    """JsonDataLoader caching and reloading."""

    def test_get_loads_once(self):
        from calc_framework.data.json_loader import JsonDataLoader

        calls = [0]

        def _load():
            calls[0] += 1
            return {"key": "value"}

        loader = JsonDataLoader(_load)
        assert loader.loaded is False
        data = loader.get()
        assert data == {"key": "value"}
        assert calls[0] == 1
        assert loader.loaded is True
        # second call uses cache
        data2 = loader.get()
        assert calls[0] == 1
        assert data2 == {"key": "value"}

    def test_reload_clears_cache(self):
        from calc_framework.data.json_loader import JsonDataLoader

        calls = [0]

        def _load():
            calls[0] += 1
            return {"count": calls[0]}

        loader = JsonDataLoader(_load)
        assert loader.get() == {"count": 1}
        loader.reload()
        assert loader.loaded is False
        assert loader.get() == {"count": 2}

    def test_generic_type_parameter(self):
        from calc_framework.data.json_loader import JsonDataLoader

        loader = JsonDataLoader[int](lambda: 42)
        assert loader.get() == 42

    def test_complex_data_structure(self):
        from calc_framework.data.json_loader import JsonDataLoader

        loader = JsonDataLoader[list[dict]](lambda: [{"a": 1}, {"b": 2}])
        data = loader.get()
        assert len(data) == 2

    def test_loaded_property_after_get(self):
        from calc_framework.data.json_loader import JsonDataLoader

        loader = JsonDataLoader(lambda: "data")
        assert not loader.loaded
        loader.get()
        assert loader.loaded

    def test_reload_then_loaded_is_false(self):
        from calc_framework.data.json_loader import JsonDataLoader

        loader = JsonDataLoader(lambda: "data")
        loader.get()
        loader.reload()
        assert not loader.loaded


# =========================================================================
# Data Layer — AttributeSchema
# =========================================================================


class TestAttributeSchemaExpanded:
    """AttributeSchema resolve, validate, serialization."""

    def test_attribute_decl_creation(self):
        from calc_framework.data.attr_schema import AttributeDecl

        decl = AttributeDecl(name="基础攻击", type="float", source="character")
        assert decl.name == "基础攻击"
        assert decl.type == "float"
        assert decl.source == "character"

    def test_attribute_decl_to_dict(self):
        from calc_framework.data.attr_schema import AttributeDecl

        decl = AttributeDecl(name="hp", type="int", source="character", default=100)
        d = decl.to_dict()
        assert d["name"] == "hp"
        assert d["type"] == "int"
        assert d["default"] == 100

    def test_attribute_decl_from_dict_minimal(self):
        from calc_framework.data.attr_schema import AttributeDecl

        decl = AttributeDecl.from_dict({"name": "defense"})
        assert decl.name == "defense"
        assert decl.type == "float"
        assert decl.source == "character"

    def test_attribute_decl_from_dict_invalid_type(self):
        from calc_framework.data.attr_schema import AttributeDecl, AttributeSchemaError

        with pytest.raises(AttributeSchemaError, match="不支持的属性类型"):
            AttributeDecl.from_dict({"name": "x", "type": "invalid_type"})

    def test_attribute_decl_from_dict_invalid_source(self):
        from calc_framework.data.attr_schema import AttributeDecl, AttributeSchemaError

        with pytest.raises(AttributeSchemaError, match="不支持的 source"):
            AttributeDecl.from_dict({"name": "x", "source": "invalid_source"})

    def test_attribute_decl_from_dict_missing_name(self):
        from calc_framework.data.attr_schema import AttributeDecl, AttributeSchemaError

        with pytest.raises(AttributeSchemaError, match="缺少有效的 'name'"):
            AttributeDecl.from_dict({})

    def test_schema_resolve_basic(self):
        from calc_framework.data.attr_schema import AttributeDecl, AttributeSchema

        schema = AttributeSchema(
            attributes=[
                AttributeDecl(name="攻击力", type="float", source="character"),
                AttributeDecl(name="防御力", type="int", source="character"),
                AttributeDecl(name="护甲", type="int", source="enemy"),
            ]
        )
        raw = {"character": {"攻击力": 500, "防御力": 200}, "enemy": {"护甲": 100}}
        context = schema.resolve(raw)
        assert context["character"]["攻击力"] == 500.0
        assert context["character"]["防御力"] == 200
        assert context["enemy"]["护甲"] == 100

    def test_schema_resolve_missing_value_uses_default(self):
        from calc_framework.data.attr_schema import AttributeDecl, AttributeSchema

        schema = AttributeSchema(
            attributes=[
                AttributeDecl(name="atk", type="float", source="character", default=100.0),
            ]
        )
        context = schema.resolve({"character": {}})
        assert context["character"]["atk"] == 100.0

    def test_schema_resolve_fills_all_sources(self):
        from calc_framework.data.attr_schema import AttributeSchema

        schema = AttributeSchema(attributes=[])
        context = schema.resolve({})
        for src in ["character", "weapon", "equipment", "enemy", "computed"]:
            assert src in context

    def test_schema_validate_passes(self):
        from calc_framework.data.attr_schema import AttributeDecl, AttributeSchema

        schema = AttributeSchema(attributes=[AttributeDecl(name="atk", type="float", source="character")])
        errors = schema.validate({"character": {"atk": 100.0}})
        assert errors == []

    def test_schema_validate_missing_required(self):
        from calc_framework.data.attr_schema import AttributeDecl, AttributeSchema

        schema = AttributeSchema(attributes=[AttributeDecl(name="atk", type="float", source="character")])
        errors = schema.validate({"character": {}})
        assert len(errors) > 0
        assert "缺少必填属性" in errors[0]

    def test_schema_validate_type_mismatch_int(self):
        from calc_framework.data.attr_schema import AttributeDecl, AttributeSchema

        schema = AttributeSchema(attributes=[AttributeDecl(name="level", type="int", source="character")])
        errors = schema.validate({"character": {"level": "not_an_int"}})
        assert len(errors) > 0

    def test_schema_validate_type_mismatch_bool(self):
        from calc_framework.data.attr_schema import AttributeDecl, AttributeSchema

        schema = AttributeSchema(attributes=[AttributeDecl(name="flag", type="bool", source="character")])
        errors = schema.validate({"character": {"flag": "not_bool"}})
        assert len(errors) > 0

    def test_schema_validate_with_default_skips_missing(self):
        from calc_framework.data.attr_schema import AttributeDecl, AttributeSchema

        schema = AttributeSchema(attributes=[AttributeDecl(name="opt", type="float", source="character", default=0.0)])
        errors = schema.validate({"character": {}})
        assert errors == []

    def test_schema_to_json_and_from_file(self):
        from calc_framework.data.attr_schema import AttributeDecl, AttributeSchema

        schema = AttributeSchema(attributes=[AttributeDecl(name="atk", type="float", source="character")])
        json_str = schema.to_json()
        assert "atk" in json_str

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
            f.write(json_str)
            tmp_path = f.name
        try:
            loaded = AttributeSchema.from_file(tmp_path)
            assert len(loaded.attributes) == 1
            assert loaded.attributes[0].name == "atk"
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    def test_schema_from_dict_with_attr_alias(self):
        from calc_framework.data.attr_schema import AttributeSchema

        schema = AttributeSchema.from_dict(
            {
                "attr": [
                    {"name": "defense", "type": "int", "source": "enemy"},
                ]
            }
        )
        assert len(schema.attributes) == 1
        assert schema.attributes[0].name == "defense"

    def test_schema_from_dict_invalid(self):
        from calc_framework.data.attr_schema import AttributeSchema, AttributeSchemaError

        with pytest.raises(AttributeSchemaError, match="缺少 'attributes' 列表"):
            AttributeSchema.from_dict({})

    def test_schema_coerce_percent_type(self):
        from calc_framework.data.attr_schema import AttributeDecl, AttributeSchema

        schema = AttributeSchema(attributes=[AttributeDecl(name="bonus", type="percent", source="character")])
        context = schema.resolve({"character": {"bonus": "25"}})
        assert context["character"]["bonus"] == 25.0

    def test_schema_coerce_str_to_int(self):
        from calc_framework.data.attr_schema import AttributeDecl, AttributeSchema

        schema = AttributeSchema(attributes=[AttributeDecl(name="level", type="int", source="character")])
        context = schema.resolve({"character": {"level": 80}})
        assert context["character"]["level"] == 80

    def test_schema_save_and_reload(self):
        from calc_framework.data.attr_schema import AttributeDecl, AttributeSchema

        schema = AttributeSchema(
            attributes=[
                AttributeDecl(name="hp", type="int", source="character"),
                AttributeDecl(name="mp", type="float", source="computed", default=0.0),
            ]
        )
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
            tmp_path = f.name
        try:
            schema.save(tmp_path)
            loaded = AttributeSchema.from_file(tmp_path)
            assert len(loaded.attributes) == 2
            names = {a.name for a in loaded.attributes}
            assert names == {"hp", "mp"}
        finally:
            Path(tmp_path).unlink(missing_ok=True)


# =========================================================================
# Data Layer — Variable Schema Validation
# =========================================================================


class TestVariableValidation:
    """Variable schema validation tests."""

    def test_resolve_path_nested(self):
        from calc_framework.data import schema as s_mod

        ctx = {"character": {"atk": 500}}
        result = s_mod._resolve_path(ctx, "character.atk")
        assert result == 500

    def test_resolve_path_not_found(self):
        from calc_framework.data import schema as s_mod

        ctx = {"character": {}}
        result = s_mod._resolve_path(ctx, "character.missing")
        assert result is None

    def test_resolve_path_shallow(self):
        from calc_framework.data import schema as s_mod

        ctx = {"top": 42}
        result = s_mod._resolve_path(ctx, "top")
        assert result == 42

    def test_check_type_float_accepts_int(self):
        from calc_framework.data import schema as s_mod

        # float accepts int (as per _check_type)
        s_mod._check_type("test", 42, "float")  # should not raise

    def test_check_type_int_rejects_bool(self):
        from calc_framework.data import schema as s_mod

        with pytest.raises(s_mod.VariableValidationError, match="期望 int"):
            s_mod._check_type("test", True, "int")

    def test_check_type_bool_rejects_int(self):
        from calc_framework.data import schema as s_mod

        with pytest.raises(s_mod.VariableValidationError, match="期望 bool"):
            s_mod._check_type("test", 1, "bool")

    def test_check_type_str_rejects_int(self):
        from calc_framework.data import schema as s_mod

        with pytest.raises(s_mod.VariableValidationError, match="期望 str"):
            s_mod._check_type("test", 123, "str")


# =========================================================================
# Config Layer — AdapterPackage & discover_adapters
# =========================================================================


class TestConfigAdapter:
    """AdapterPackage and discover_adapters tests."""

    def test_adapter_error_base_class(self):
        from calc_framework.config.adapter import AdapterError

        err = AdapterError("test error")
        assert isinstance(err, Exception)

    def test_adapter_not_found_error(self):
        from calc_framework.config.adapter import AdapterError, AdapterNotFoundError

        err = AdapterNotFoundError("not found")
        assert isinstance(err, AdapterError)

    def test_invalid_meta_error(self):
        from calc_framework.config.adapter import AdapterError, InvalidMetaError

        err = InvalidMetaError("invalid meta")
        assert isinstance(err, AdapterError)

    def test_discover_adapters_empty_dir(self, tmp_path):
        from calc_framework.config.manager import discover_adapters

        result = discover_adapters(tmp_path)
        assert result == {}

    def test_discover_adapters_with_valid_meta(self, tmp_path):
        from calc_framework.config.manager import discover_adapters

        adapter_dir = tmp_path / "test_game"
        adapter_dir.mkdir()
        (adapter_dir / "meta.json").write_text(
            json.dumps({"name": "TestGame", "schema_version": "dag-v1"}),
            encoding="utf-8",
        )
        result = discover_adapters(tmp_path)
        assert "TestGame" in result
        assert result["TestGame"] == adapter_dir

    def test_discover_adapters_skips_underscore_dirs(self, tmp_path):
        from calc_framework.config.manager import discover_adapters

        hidden_dir = tmp_path / "_hidden"
        hidden_dir.mkdir()
        (hidden_dir / "meta.json").write_text(
            json.dumps({"name": "Hidden"}),
            encoding="utf-8",
        )
        result = discover_adapters(tmp_path)
        assert "Hidden" not in result

    def test_discover_adapters_skips_non_dirs(self, tmp_path):
        from calc_framework.config.manager import discover_adapters

        (tmp_path / "not_a_dir.txt").write_text("hello", encoding="utf-8")
        discover_adapters(tmp_path)  # should not error

    def test_discover_adapters_invalid_json(self, tmp_path):
        from calc_framework.config.manager import discover_adapters

        bad_dir = tmp_path / "bad_game"
        bad_dir.mkdir()
        (bad_dir / "meta.json").write_text("not json", encoding="utf-8")
        result = discover_adapters(tmp_path)
        assert "bad_game" not in result

    def test_discover_adapters_no_meta_json(self, tmp_path):
        from calc_framework.config.manager import discover_adapters

        empty_dir = tmp_path / "empty_game"
        empty_dir.mkdir()
        result = discover_adapters(tmp_path)
        assert "empty_game" not in result

    def test_discover_adapters_uses_dirname_as_fallback(self, tmp_path):
        from calc_framework.config.manager import discover_adapters

        adapter_dir = tmp_path / "my_game"
        adapter_dir.mkdir()
        (adapter_dir / "meta.json").write_text(
            json.dumps({"schema_version": "dag-v1"}),
            encoding="utf-8",
        )
        result = discover_adapters(tmp_path)
        assert "my_game" in result


class TestAdapterManagerExpanded:
    """AdapterManager edge cases."""

    def test_manager_init_empty(self, tmp_path):
        from calc_framework.config.manager import AdapterManager

        mgr = AdapterManager(adapters_dir=tmp_path)
        assert mgr.names == []
        assert mgr.available_adapters == {}

    def test_manager_load_unknown_raises(self, tmp_path):
        from calc_framework.config.manager import AdapterManager

        mgr = AdapterManager(adapters_dir=tmp_path)
        with pytest.raises(KeyError, match="未找到"):
            mgr.load("nonexistent")

    def test_manager_refresh(self, tmp_path):
        from calc_framework.config.manager import AdapterManager

        mgr = AdapterManager(adapters_dir=tmp_path)
        mgr.refresh()  # should not error
        assert mgr.names == []

    def test_manager_summary(self, tmp_path):
        from calc_framework.config.manager import AdapterManager

        mgr = AdapterManager(adapters_dir=tmp_path)
        summary = mgr.summary()
        assert isinstance(summary, list)


# =========================================================================
# Config Layer — FileWatcher
# =========================================================================


class TestFileWatcherExpanded:
    """FileWatcher lifecycle tests."""

    def test_file_watcher_creation(self, tmp_path):
        from calc_framework.config.file_watcher import FileWatcher

        f = tmp_path / "test.txt"
        f.write_text("hello", encoding="utf-8")
        callback_called = []

        def callback():
            callback_called.append(True)

        watcher = FileWatcher(f, on_change=callback, poll_interval=0.5)
        assert not watcher.is_running
        assert watcher.path == f

    def test_file_watcher_start_stop(self, tmp_path):
        import time

        from calc_framework.config.file_watcher import FileWatcher

        f = tmp_path / "test.txt"
        f.write_text("hello", encoding="utf-8")

        callback_called = []

        def callback():
            callback_called.append(True)

        watcher = FileWatcher(f, on_change=callback, poll_interval=0.5)
        watcher.start()
        assert watcher.is_running
        time.sleep(0.1)
        watcher.stop()
        assert not watcher.is_running

    def test_file_watcher_double_start(self, tmp_path):
        import time

        from calc_framework.config.file_watcher import FileWatcher

        f = tmp_path / "test.txt"
        f.write_text("hello", encoding="utf-8")
        watcher = FileWatcher(f, on_change=lambda: None, poll_interval=0.5)
        watcher.start()
        watcher.start()  # should log warning, not raise
        time.sleep(0.1)
        watcher.stop()

    def test_file_watcher_poll_interval_min(self):
        import time

        from calc_framework.config.file_watcher import FileWatcher

        f = Path(tempfile.gettempdir()) / "_fw_test.txt"
        f.write_text("hello", encoding="utf-8")
        watcher = FileWatcher(f, on_change=lambda: None, poll_interval=0.1)
        # poll_interval should be clamped to 0.5 minimum
        assert watcher._poll_interval == 0.5
        try:
            watcher.start()
            time.sleep(0.1)
            watcher.stop()
        finally:
            f.unlink(missing_ok=True)


# =========================================================================
# Plugin Layer — Base, Registry, Builtin
# =========================================================================


class TestPluginBaseExpanded:
    """Plugin base class and meta."""

    def test_plugin_meta_defaults(self):
        from calc_framework.plugin.base import PluginMeta

        meta = PluginMeta(name="test_plugin")
        assert meta.version == "1.0.0"
        assert meta.description == ""
        assert meta.dependencies == []
        assert meta.author == ""

    def test_plugin_meta_full(self):
        from calc_framework.plugin.base import PluginMeta

        meta = PluginMeta(
            name="full_plugin",
            version="2.0.0",
            description="A full plugin",
            dependencies=["dep1", "dep2"],
            author="test_author",
        )
        assert meta.name == "full_plugin"
        assert meta.version == "2.0.0"
        assert meta.dependencies == ["dep1", "dep2"]
        assert meta.author == "test_author"

    def test_base_plugin_default_on_load(self):
        from calc_framework.plugin.base import BasePlugin, PluginMeta

        class _MinPlugin(BasePlugin):
            @property
            def meta(self):
                return PluginMeta(name="min")

        p = _MinPlugin()
        assert p.on_load() == {}

    def test_base_plugin_on_unload_noop(self):
        from calc_framework.plugin.base import BasePlugin, PluginMeta

        class _MinPlugin(BasePlugin):
            @property
            def meta(self):
                return PluginMeta(name="min")

        p = _MinPlugin()
        p.on_unload()  # should not raise

    def test_base_plugin_on_adapter_attach_noop(self):
        from calc_framework.plugin.base import BasePlugin, PluginMeta

        class _MinPlugin(BasePlugin):
            @property
            def meta(self):
                return PluginMeta(name="min")

        p = _MinPlugin()
        p.on_adapter_attach(object())  # should not raise


class TestPluginRegistryExpanded:
    """PluginRegistry lifecycle and apply."""

    def test_get_registry_singleton(self):
        from calc_framework.plugin.registry import get_registry

        r1 = get_registry()
        r2 = get_registry()
        assert r1 is r2

    def test_list_plugins_includes_builtins(self):
        from calc_framework.plugin.registry import list_plugins

        names = list_plugins()
        assert isinstance(names, list)
        assert "crit_handler" in names
        assert "dodge_handler" in names
        assert "distance_decay" in names

    def test_clear_removes_all(self):
        from calc_framework.plugin.builtin import CritPlugin
        from calc_framework.plugin.registry import PluginRegistry

        reg = PluginRegistry()
        reg.register(CritPlugin())
        assert len(reg.list()) == 1
        reg.clear()
        assert len(reg.list()) == 0

    def test_apply_to_adapter_unknown_plugin(self):
        from calc_framework.plugin.registry import PluginRegistry

        reg = PluginRegistry()
        svc = self._make_dag_svc()
        reg.apply_to_adapter(["nonexistent_plugin"], svc)
        # should log warning, not raise

    def _make_dag_svc(self):
        from calc_framework.dag.serializer import dag_from_dict
        from calc_framework.dag.service import DAGService

        graph = dag_from_dict(
            {
                "schema_version": "dag-v1",
                "name": "test",
                "nodes": {"d": {"type": "const", "value": 0}},
                "outputs": {"d": {"node": "d", "label": "d"}},
            }
        )
        return DAGService(dag=graph)

    def test_register_then_get(self):
        from calc_framework.plugin.builtin import CritPlugin
        from calc_framework.plugin.registry import PluginRegistry

        reg = PluginRegistry()
        plugin = CritPlugin()
        reg.register(plugin)
        assert reg.get("crit_handler") is plugin
        reg.clear()

    def test_unregister_calls_on_unload(self):
        from calc_framework.plugin.base import BasePlugin, PluginMeta
        from calc_framework.plugin.registry import PluginRegistry

        unload_called = []

        class _UnloadPlugin(BasePlugin):
            @property
            def meta(self):
                return PluginMeta(name="unload_test")

            def on_unload(self):
                unload_called.append(True)

        reg = PluginRegistry()
        reg.register(_UnloadPlugin())
        reg.unregister("unload_test")
        assert len(unload_called) == 1

    def test_apply_to_adapter_empty_list(self):
        from calc_framework.plugin.registry import PluginRegistry

        reg = PluginRegistry()
        svc = self._make_dag_svc()
        reg.apply_to_adapter([], svc)
        # should not raise


class TestBuiltinPluginsExpanded:
    """Expanded builtin plugin validation."""

    def test_crit_plugin_dependencies(self):
        from calc_framework.plugin.builtin import CritPlugin

        p = CritPlugin()
        assert p.meta.dependencies == []

    def test_dodge_plugin_author(self):
        from calc_framework.plugin.builtin import DodgePlugin

        p = DodgePlugin()
        assert p.meta.author == "framework"

    def test_distance_decay_plugin_variables_count(self):
        from calc_framework.plugin.builtin import DistanceDecayPlugin

        p = DistanceDecayPlugin()
        data = p.on_load()
        vars_data = data.get("variables", {})
        assert "attack.distance" in vars_data
        assert "attack.decay_start" in vars_data
        assert "attack.decay_end" in vars_data

    def test_crit_plugin_template_structure(self):
        from calc_framework.plugin.builtin import CritPlugin

        p = CritPlugin()
        data = p.on_load()
        tpl = data["templates"]["crit_basic"]
        assert tpl["output_node"] == "result"
        assert "crit_rate" in tpl["parameters"]
        assert "crit_dmg" in tpl["parameters"]
        assert "is_crit" in tpl["parameters"]

    def test_distance_decay_template_structure(self):
        from calc_framework.plugin.builtin import DistanceDecayPlugin

        p = DistanceDecayPlugin()
        data = p.on_load()
        tpl = data["templates"]["linear_distance_decay"]
        assert tpl["output_node"] == "in_range"
        assert "distance" in tpl["parameters"]
        assert "start_at" in tpl["parameters"]
        assert "end_at" in tpl["parameters"]

    def test_register_builtins_idempotent(self):
        from calc_framework.plugin.builtin import register_builtin_plugins
        from calc_framework.plugin.registry import list_plugins

        register_builtin_plugins()
        names_before = list_plugins()
        register_builtin_plugins()
        names_after = list_plugins()
        assert names_before == names_after

    def test_dodge_plugin_variables(self):
        from calc_framework.plugin.builtin import DodgePlugin

        p = DodgePlugin()
        data = p.on_load()
        vars_data = data.get("variables", {})
        assert "character.accuracy" in vars_data
        assert vars_data["character.accuracy"]["default"] == 1.0
        assert "enemy.dodge_rate" in vars_data
        assert vars_data["enemy.dodge_rate"]["default"] == 0.0


# =========================================================================
# FitResult summary
# =========================================================================


class TestFitResultExpanded:
    """FitResult edge cases."""

    def test_fit_result_defaults(self):
        from calc_framework.inverse.base import FitResult

        r = FitResult()
        assert r.params == {}
        assert r.computed == []
        assert r.max_error == 0.0
        assert r.is_exact is False

    def test_fit_result_summary_exact(self):
        from calc_framework.inverse.base import FitResult

        r = FitResult(params={"base": 100, "growth": 5}, is_exact=True)
        s = r.summary()
        assert "✓ 精确匹配" in s

    def test_fit_result_summary_approx(self):
        from calc_framework.inverse.base import FitResult

        r = FitResult(params={"base": 100, "growth": 5}, max_error=0.5)
        s = r.summary()
        assert "≈" in s
        assert "0.5000" in s

    def test_fit_result_growth_params_none_for_insufficient(self):
        from calc_framework.inverse.base import FitResult

        r = FitResult(params={"unknown_key": 1})
        assert r.growth_params is None
