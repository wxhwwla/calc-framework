#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# SPDX-License-Identifier: AGPL-3.0
# ruff: noqa: E402

# 上述 E402 是必需的：framework 未安装为 pip 包，需 sys.path.insert 后才能 import

"""卡牌RPG 适配器集成测试 — 验证框架能无缝加载和执行跨品类游戏。"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

_ADAPTER_DIR = Path(__file__).resolve().parents[2] / "adapters" / "card_rpg"

_ADAPTER_PARENT = _ADAPTER_DIR.parent

_FRAMEWORK_SRC = Path(__file__).resolve().parents[2] / "src"

_FRAMEWORK_ROOT = Path(__file__).resolve().parents[2]


if str(_FRAMEWORK_SRC) not in sys.path:
    sys.path.insert(0, str(_FRAMEWORK_SRC))

if str(_FRAMEWORK_ROOT) not in sys.path:
    sys.path.insert(0, str(_FRAMEWORK_ROOT))

if str(_ADAPTER_PARENT) not in sys.path:
    sys.path.insert(0, str(_ADAPTER_PARENT))


from calc_framework.config.adapter import AdapterPackage
from calc_framework.data.attr_schema import AttributeSchema


def _load_card_rpg_loader():
    """用 importlib 直接文件加载，避开 adapters 命名空间冲突。"""

    loader_path = _ADAPTER_DIR / "loader.py"

    spec = importlib.util.spec_from_file_location("card_rpg_loader", loader_path)

    mod = importlib.util.module_from_spec(spec)

    spec.loader.exec_module(mod)

    return mod.CardRPGLoader


CardRPGLoader = _load_card_rpg_loader()


@pytest.fixture
def adapter_pkg() -> AdapterPackage:
    return AdapterPackage(str(_ADAPTER_DIR))


class TestAdapterLoads:
    """验证适配器包能够被框架正常加载。"""

    def test_meta_json_exists(self):
        meta_path = _ADAPTER_DIR / "meta.json"

        assert meta_path.exists()

    def test_dag_json_exists(self):
        dag_path = _ADAPTER_DIR / "card_rpg.dag.json"

        assert dag_path.exists()

    def test_attr_schema_exists(self):
        schema_path = _ADAPTER_DIR / "attr_schema.json"

        assert schema_path.exists()

    def test_adapter_package_loads(self, adapter_pkg):
        assert adapter_pkg.meta["name"] == "卡牌RPG伤害计算"

        assert adapter_pkg.meta["game"] == "经典卡牌RPG（示例）"

    def test_dag_service_loaded(self, adapter_pkg):
        svc = adapter_pkg.dag_service

        assert svc is not None

        graph = svc.dag

        assert "total_atk" in graph.nodes

        assert "final_damage" in graph.nodes

        assert len(graph.outputs) == 4

    def test_functions_registered(self, adapter_pkg):
        adapter_pkg.dag_service  # trigger lazy load

        from calc_framework.dag.sandbox import list_functions

        funcs = list_functions()

        assert "clamp" in funcs

    def test_attr_schema_loads(self):
        schema = AttributeSchema.from_file(_ADAPTER_DIR / "attr_schema.json")

        names = {a.name for a in schema.attributes}

        assert "ATK" in names

        assert "DEF" in names

        assert "crit_rate" in names

        assert "ATK_bonus" in names


class TestDAGEvaluation:
    """验证 DAG 公式能正确求值。"""

    def test_basic_attack(self, adapter_pkg):
        svc = adapter_pkg.dag_service

        ctx = {
            "character": {"ATK": 100, "DEF": 50, "crit_rate": 0.05, "crit_dmg": 0.5},
            "weapon": {"ATK_bonus": 0},
            "enemy": {"DEF": 60},
            "user_input": {"skill_mult": 1.0, "is_crit": False},
        }

        result = svc.evaluate(ctx)

        assert result.outputs["总攻击力"] == pytest.approx(100.0)

        assert result.outputs["基础伤害"] == pytest.approx(70.0)

        assert result.outputs["暴击倍率"] == pytest.approx(1.0)

        assert result.outputs["最终伤害"] == pytest.approx(70.0)

    def test_with_weapon_bonus(self, adapter_pkg):
        svc = adapter_pkg.dag_service

        ctx = {
            "character": {"ATK": 100, "DEF": 50, "crit_rate": 0.05, "crit_dmg": 0.5},
            "weapon": {"ATK_bonus": 25},
            "enemy": {"DEF": 60},
            "user_input": {"skill_mult": 1.0, "is_crit": False},
        }

        result = svc.evaluate(ctx)

        assert result.outputs["总攻击力"] == pytest.approx(125.0)

        assert result.outputs["最终伤害"] == pytest.approx(95.0)

    def test_critical_hit(self, adapter_pkg):
        svc = adapter_pkg.dag_service

        ctx = {
            "character": {"ATK": 100, "DEF": 50, "crit_rate": 0.05, "crit_dmg": 0.5},
            "weapon": {"ATK_bonus": 0},
            "enemy": {"DEF": 60},
            "user_input": {"skill_mult": 1.0, "is_crit": True},
        }

        result = svc.evaluate(ctx)

        assert result.outputs["暴击倍率"] == pytest.approx(1.5)

        assert result.outputs["最终伤害"] == pytest.approx(105.0)

    def test_skill_multiplier(self, adapter_pkg):
        svc = adapter_pkg.dag_service

        ctx = {
            "character": {"ATK": 100, "DEF": 50, "crit_rate": 0.05, "crit_dmg": 0.5},
            "weapon": {"ATK_bonus": 0},
            "enemy": {"DEF": 60},
            "user_input": {"skill_mult": 2.5, "is_crit": False},
        }

        result = svc.evaluate(ctx)

        assert result.outputs["基础伤害"] == pytest.approx(220.0)

        assert result.outputs["最终伤害"] == pytest.approx(220.0)

    def test_negative_base_clamped_to_zero(self, adapter_pkg):
        svc = adapter_pkg.dag_service

        ctx = {
            "character": {"ATK": 10, "DEF": 50, "crit_rate": 0.05, "crit_dmg": 0.5},
            "weapon": {"ATK_bonus": 0},
            "enemy": {"DEF": 200},
            "user_input": {"skill_mult": 1.0, "is_crit": False},
        }

        result = svc.evaluate(ctx)

        assert result.outputs["基础伤害"] == pytest.approx(0.0)

        assert result.outputs["最终伤害"] == pytest.approx(0.0)

    def test_default_values(self, adapter_pkg):
        svc = adapter_pkg.dag_service

        ctx = {
            "character": {"ATK": 100},
            "enemy": {},
            "user_input": {},
        }

        result = svc.evaluate(ctx)

        assert result.outputs["总攻击力"] == pytest.approx(100.0)

        assert result.outputs["最终伤害"] == pytest.approx(75.0)

    def test_high_value_no_overflow(self, adapter_pkg):
        svc = adapter_pkg.dag_service

        ctx = {
            "character": {"ATK": 99999, "DEF": 9999, "crit_rate": 0.05, "crit_dmg": 3.0},
            "weapon": {"ATK_bonus": 5000},
            "enemy": {"DEF": 9999},
            "user_input": {"skill_mult": 9.9, "is_crit": True},
        }

        result = svc.evaluate(ctx)

        # total_atk = 99999 + 5000 = 104999

        # atk_x_skill = 104999 * 9.9 = 1039490.1

        # half_def = 9999 * 0.5 = 4999.5

        # base_dmg = 1039490.1 - 4999.5 = 1034490.6

        # clamped = min(1034490.6, 999999) = 999999

        # crit_mult = 1 + 3.0 = 4.0

        # final = 999999 * 4.0 = 3999996

        assert result.outputs["基础伤害"] == pytest.approx(999999.0)

        assert result.outputs["最终伤害"] == pytest.approx(3999996.0)


class TestCardRPGLoader:
    """验证 CardRPGLoader 能正确构建 DataContext。"""

    def test_loader_basic(self):
        loader = CardRPGLoader()

        ctx = loader.build_context(
            character={"ATK": 100, "DEF": 50, "crit_rate": 0.05, "crit_dmg": 0.5},
            weapon={"ATK_bonus": 15},
            enemy={"DEF": 60},
        )

        assert ctx["character"]["ATK"] == 100.0

        assert ctx["character"]["DEF"] == 50.0

        assert ctx["weapon"]["ATK_bonus"] == 15.0

        assert ctx["enemy"]["DEF"] == 60.0

    def test_loader_defaults(self):
        loader = CardRPGLoader()

        ctx = loader.build_context(character={"ATK": 100})

        assert ctx["character"]["ATK"] == 100.0

        assert ctx["character"]["DEF"] == 0.0

        assert ctx["character"]["crit_rate"] == 0.05

        assert ctx["weapon"]["ATK_bonus"] == 0.0

        assert ctx["enemy"]["DEF"] == 50.0

    def test_loader_with_schema(self):
        schema = AttributeSchema.from_file(_ADAPTER_DIR / "attr_schema.json")

        loader = CardRPGLoader(attr_schema=schema)

        ctx = loader.build_context(
            character={"ATK": 100, "DEF": 50},
            weapon={"ATK_bonus": 15},
            enemy={"DEF": 60},
        )

        assert ctx["character"]["ATK"] == 100.0

        assert ctx["character"]["DEF"] == 50.0

        assert ctx["character"]["crit_rate"] == 0.05  # default

        assert ctx["weapon"]["ATK_bonus"] == 15.0

        assert ctx["enemy"]["DEF"] == 60.0

    def test_loader_with_schema_end_to_end(self, adapter_pkg):
        schema = AttributeSchema.from_file(_ADAPTER_DIR / "attr_schema.json")

        loader = CardRPGLoader(attr_schema=schema)

        ctx = loader.build_context(
            character={"ATK": 150, "DEF": 30, "crit_rate": 0.1, "crit_dmg": 0.8},
            weapon={"ATK_bonus": 20},
            enemy={"DEF": 80},
        )

        ctx["user_input"] = {"skill_mult": 1.5, "is_crit": True}

        result = adapter_pkg.dag_service.evaluate(ctx)

        assert result.outputs["总攻击力"] == pytest.approx(170.0)

        assert result.outputs["最终伤害"] == pytest.approx(387.0)


class TestDAGJsonContract:
    """验证 card_rpg.dag.json 符合框架的 JSON Schema 规范。"""

    def test_variables_have_required_fields(self):
        dag_path = _ADAPTER_DIR / "card_rpg.dag.json"

        with open(dag_path, encoding="utf-8") as f:
            data = json.load(f)

        assert "schema_version" in data

        assert data["schema_version"] == "dag-v1"

        assert "variables" in data

        assert "nodes" in data

        assert "outputs" in data

        for var_name, var_def in data["variables"].items():
            assert "type" in var_def, f"变量 {var_name} 缺少 type"

            assert "source" in var_def, f"变量 {var_name} 缺少 source"

        for node_id, node_def in data["nodes"].items():
            assert "type" in node_def, f"节点 {node_id} 缺少 type"

    def test_outputs_refer_to_existing_nodes(self):
        dag_path = _ADAPTER_DIR / "card_rpg.dag.json"

        with open(dag_path, encoding="utf-8") as f:
            data = json.load(f)

        all_nodes = set(data["nodes"].keys())

        for out_name, out_def in data["outputs"].items():
            assert out_def["node"] in all_nodes, f"输出 {out_name} 引用了不存在的节点 {out_def['node']}"

    def test_subgraphs_are_empty(self):
        dag_path = _ADAPTER_DIR / "card_rpg.dag.json"

        with open(dag_path, encoding="utf-8") as f:
            data = json.load(f)

        assert data.get("subgraphs", {}) == {}
