#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""终末地 DAG 与现有引擎的数值对比测试。

通过框架 AdapterPackage 加载 DAG，EndfieldContextLoader 构建 DataContext。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pytest
from calc_framework.config.adapter import AdapterPackage

_REPO_ROOT = Path(__file__).resolve().parents[4]
_FRAMEWORK_DIR = _REPO_ROOT / "framework"
_PKG_ROOT = _REPO_ROOT / "adapters" / "endfield" / "calc"
_ADAPTER_DIR = _FRAMEWORK_DIR / "adapters" / "endfield"

if str(_PKG_ROOT) not in sys.path:
    sys.path.insert(0, str(_PKG_ROOT))

PARTICIPANTS_JSON = (
    _REPO_ROOT / "adapters" / "endfield" / "data" / "characters.json"
)
WEAPONS_JSON = (
    _REPO_ROOT / "adapters" / "endfield" / "data" / "weapons.json"
)
_EXPECTED_OUTPUT = _FRAMEWORK_DIR / "src" / "calc_framework" / "configs" / "endfield_full.dag.json"


def _load_by_name(path: Path, name: str) -> dict[str, Any]:
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    for item in data:
        if item.get("名称") == name:
            return item
    raise KeyError(name)


def _minimal_context() -> dict[str, dict[str, Any]]:
    return {
        "character": {
            "基础攻击": 0.0, "力量": 0.0, "敏捷": 0.0, "智识": 0.0, "意志": 0.0,
            "主能力": "", "副能力": "",
            "暴击率": 0.0, "暴击伤害": 0.0,
        },
        "weapon": {
            "基础攻击": 0.0, "攻击力+": 0.0, "附加攻击力+": 0.0,
        },
        "equipment": {
            "攻击力平值": 0.0,
        },
        "computed": {
            "主能力平值加算": 0.0, "副能力平值加算": 0.0,
            "主能力百分比": 0.0, "副能力百分比": 0.0,
            "主能力": "", "副能力": "",
            "最终攻击力": 0.0,
            "技能倍率": 1.0,
            "暴击区": 1.0, "伤害加成": 1.0, "伤害减免": 1.0,
            "增幅": 1.0, "虚弱": 1.0, "庇护": 1.0,
            "脆弱": 1.0, "易伤": 1.0, "防御": 0.5,
            "失衡易伤": 1.0, "抗性": 1.0,
            "非主控减伤": 1.0, "连击增伤": 1.0, "特殊乘区": 1.0,
        },
    }


class TestEndfieldDAGIntegration:
    @pytest.fixture(scope="class")
    def generated_dag(self):
        from calc_engine.endfield.calc.multiplicative_zones.dag.config import OUTPUT_PATH, generate

        dag = generate()
        assert dag.name == "终末地伤害公式（完整版）"
        assert OUTPUT_PATH == _EXPECTED_OUTPUT, f"{OUTPUT_PATH} != {_EXPECTED_OUTPUT}"
        return dag

    @pytest.fixture(scope="class")
    def adapter_pkg(self, generated_dag):
        from calc_engine.endfield.calc.multiplicative_zones.dag.config import save_dag

        save_dag(generated_dag)
        assert _EXPECTED_OUTPUT.exists(), f"输出文件不存在: {_EXPECTED_OUTPUT}"
        return AdapterPackage(_ADAPTER_DIR)

    @pytest.fixture(scope="class")
    def context(self):
        from calc_engine.endfield.calc.multiplicative_zones.dag.loader import EndfieldContextLoader

        char = _load_by_name(PARTICIPANTS_JSON, "秋栗")
        weapon = _load_by_name(WEAPONS_JSON, "逐鳞3.0")
        loader = EndfieldContextLoader()
        return loader.build_context(
            character=char, weapon=weapon,
            char_level=80, weapon_level=80, trust_level=0,
        )

    def test_dag_json_is_valid(self, adapter_pkg):
        raw = json.loads(_EXPECTED_OUTPUT.read_text(encoding="utf-8"))
        assert raw["schema_version"] == "dag-v1"
        assert "subgraphs" in raw and "ability_bonus" in raw["subgraphs"]
        assert "subgraphs" in raw and "final_attack" in raw["subgraphs"]
        assert "subgraphs" in raw and "single_hit_damage" in raw["subgraphs"]

    def test_ability_bonus_parity(self, adapter_pkg):
        from calc_engine.endfield.calc.multiplicative_zones.ability_bonus_details import (
            calculate_ability_bonus_with_details,
        )

        char = _load_by_name(PARTICIPANTS_JSON, "秋栗")
        weapon = _load_by_name(WEAPONS_JSON, "逐鳞3.0")
        existing = calculate_ability_bonus_with_details(char, weapon, level=80, trust_level=0)

        ctx = _minimal_context()
        ctx["computed"].update({
            "主能力平值加算": existing["main_flat"],
            "副能力平值加算": existing["sub_flat"],
            "主能力百分比": existing["main_pct"],
            "副能力百分比": existing["sub_pct"],
            "主能力": existing["main_attr"],
            "副能力": existing["sub_attr"],
        })

        result = adapter_pkg.dag_service.evaluate(ctx)
        dag_bonus = result.outputs.get("能力值加成")
        assert dag_bonus is not None, "DAG 未输出能力值加成"
        assert dag_bonus == pytest.approx(existing["bonus"], rel=1e-9), (
            f"DAG: {dag_bonus}, Existing: {existing['bonus']}"
        )

    def test_final_attack_parity(self, adapter_pkg):
        from calc_engine.endfield.calc.multiplicative_zones.ability_bonus_details import (
            calculate_ability_bonus_with_details,
        )
        from calc_engine.endfield.calc.multiplicative_zones.final_attack_zone import (
            calculate_final_attack_with_details,
        )

        char = _load_by_name(PARTICIPANTS_JSON, "秋栗")
        weapon = _load_by_name(WEAPONS_JSON, "逐鳞3.0")
        existing = calculate_final_attack_with_details(
            char, weapon, char_level=80, weapon_level=80, trust_level=0,
        )
        ability = calculate_ability_bonus_with_details(char, weapon, level=80, trust_level=0)

        ctx = _minimal_context()
        ctx["character"].update({
            "基础攻击": existing["char_base_attack"],
            "主能力": ability["main_attr"],
            "副能力": ability["sub_attr"],
        })
        ctx["weapon"].update({
            "基础攻击": existing["weapon_base_attack"],
            "攻击力+": existing["attack_bonus_multiplier"] - 1.0,
            "附加攻击力+": existing["additional_attack"],
        })
        ctx["computed"].update({
            "主能力平值加算": ability["main_flat"],
            "副能力平值加算": ability["sub_flat"],
            "主能力百分比": ability["main_pct"],
            "副能力百分比": ability["sub_pct"],
            "主能力": ability["main_attr"],
            "副能力": ability["sub_attr"],
        })

        result = adapter_pkg.dag_service.evaluate(ctx)
        dag_final = result.outputs.get("最终攻击力")
        assert dag_final is not None, "DAG 未输出最终攻击力"
        assert dag_final == pytest.approx(existing["final_attack"], rel=1e-9), (
            f"DAG: {dag_final}, Existing: {existing['final_attack']}"
        )

    def test_context_loader_output(self, context):
        assert "character" in context
        assert "weapon" in context
        assert "equipment" in context
        assert "computed" in context
        assert context["character"]["基础攻击"] > 0
        assert context["weapon"]["基础攻击"] > 0

    def test_full_dag_evaluation(self, adapter_pkg, context):
        import copy
        ctx = copy.deepcopy(context)

        result = adapter_pkg.dag_service.evaluate(ctx)
        final_atk = result.outputs["最终攻击力"]
        assert final_atk > 0

        ctx["computed"]["最终攻击力"] = final_atk
        ctx["computed"]["技能倍率"] = 1.5
        result2 = adapter_pkg.dag_service.evaluate(ctx)
        assert result2.outputs.get("最终伤害", 0.0) > 0

    def test_single_hit_damage_parity(self, adapter_pkg):
        from calc_engine.endfield.calc.damage.engine.calculate import calculate_single_hit_damage
        from calc_engine.endfield.calc.damage.engine.types import DamageContext

        ctx = DamageContext(
            final_attack=1254.9936,
            skill_multiplier=1.5,
            damage_type="物理",
            skill_type="战技",
            is_unbalanced=False,
            is_true_damage=False,
            enemy_defense=100.0,
            enemy_resistance=0.0,
            ignore_resistance=0.0,
            imbalance_vulnerability_coeff=1.0,
            crit_rate=0.0,
            crit_damage=0.0,
            damage_type_bonus=0.15,
            skill_type_bonus=0.0,
            imbalance_damage_bonus=0.0,
            other_damage_bonus=0.0,
        )
        existing = calculate_single_hit_damage(ctx, effects=[], crit_mode="non_crit")

        dag_ctx = {
            "character": {
                "基础攻击": ctx.final_attack,
                "力量": 0.0, "敏捷": 0.0, "智识": 0.0, "意志": 0.0,
                "主能力": "", "副能力": "",
                "暴击率": ctx.crit_rate, "暴击伤害": ctx.crit_damage,
            },
            "weapon": {
                "基础攻击": 0.0, "攻击力+": 0.0, "附加攻击力+": 0.0,
            },
            "equipment": {"攻击力平值": 0.0},
            "enemy": {"防御": ctx.enemy_defense},
            "computed": {
                "主能力平值加算": 0.0, "副能力平值加算": 0.0,
                "主能力百分比": 0.0, "副能力百分比": 0.0,
                "主能力": "", "副能力": "",
                "技能倍率": ctx.skill_multiplier,
                "伤害加成": 1.0 + ctx.damage_type_bonus,
                "伤害减免": 1.0,
                "增幅": 1.0, "虚弱": 1.0, "庇护": 1.0,
                "脆弱": 1.0, "易伤": 1.0,
                "失衡易伤": 1.0, "抗性": 1.0,
                "非主控减伤": 1.0, "连击增伤": 1.0, "特殊乘区": 1.0,
            },
        }

        result = adapter_pkg.dag_service.evaluate(dag_ctx)
        dag_damage = result.outputs.get("最终伤害")
        assert dag_damage is not None, "DAG 未输出最终伤害"
        assert dag_damage == pytest.approx(existing.final_damage, rel=1e-9), (
            f"DAG: {dag_damage}, Existing: {existing.final_damage}"
        )

    def test_attribute_zones_output(self, context):
        """验证属性乘区 DAG 输出 力量/敏捷/智识/意志 最终值。"""
        from calc_framework.config.adapter import AdapterPackage

        pkg = AdapterPackage(_ADAPTER_DIR)
        result = pkg.dag_service.evaluate(dict(context))
        for attr_name in ("力量", "敏捷", "智识", "意志"):
            output_key = f"{attr_name}最终值"
            total = result.outputs.get(output_key)
            assert total is not None, f"DAG 未输出 {output_key}"
            base = context["character"].get(attr_name, 0.0)
            bonus = context["computed"].get(f"{attr_name}加成值", 0.0)
            assert total == pytest.approx(base + bonus, rel=1e-9), (
                f"{attr_name}: DAG total={total}, base+bonus={base}+{bonus}"
            )
