#!/usr/bin/env python3
"""生成的完整终末地 DAG 与现有引擎的数值对比测试。"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest

from calc_framework.dag.engine import evaluate_graph
from calc_framework.dag.serializer import load_dag

_REPO_ROOT = Path(__file__).resolve().parents[3]
_FRAMEWORK_DIR = _REPO_ROOT / "framework"
_PKG_ROOT = _REPO_ROOT / "endfield_damage_calculator"

if str(_PKG_ROOT) not in sys.path:
    sys.path.insert(0, str(_PKG_ROOT))


PARTICIPANTS_JSON = (
    _PKG_ROOT / "character_weapon_equipment" / "character_data" / "characters.json"
)
WEAPONS_JSON = (
    _PKG_ROOT / "character_weapon_equipment" / "weapon_data" / "weapons.json"
)

_EXPECTED_OUTPUT = _FRAMEWORK_DIR / "src" / "calc_framework" / "configs" / "endfield_full.dag.json"


def _minimal_context() -> dict[str, dict[str, Any]]:
    """构建最小完整上下文，所有变量均有默认值。"""
    return {
        "角色": {
            "基础攻击": 0.0, "力量": 0.0, "敏捷": 0.0, "智识": 0.0, "意志": 0.0,
            "主能力": "", "副能力": "",
        },
        "武器": {
            "基础攻击": 0.0, "攻击力+": 0.0, "附加攻击力+": 0.0,
        },
        "装备": {
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


def _build_dag_context(char: dict[str, Any], weapon: dict[str, Any], level: int, trust_level: int) -> dict[str, dict[str, Any]]:
    """从现有引擎计算结果中提取 DAG 所需的所有上下文变量。"""
    from calculation.multiplicative_zones.ability_bonus_details import (
        calculate_ability_bonus_with_details,
    )
    from calculation.multiplicative_zones.attribute_zone import (
        calculate_attribute_zones_with_details,
    )
    from calculation.multiplicative_zones.final_attack_zone import (
        calculate_final_attack_with_details,
    )

    main_attr = char.get("主能力", "")
    sub_attr = char.get("副能力", "")

    final = calculate_final_attack_with_details(
        char, weapon, char_level=level, weapon_level=level, trust_level=trust_level,
    )
    attr = calculate_attribute_zones_with_details(
        char, weapon, level=level, trust_level=trust_level,
    )
    ability = calculate_ability_bonus_with_details(
        char, weapon, level=level, trust_level=trust_level,
    )

    return {
        "角色": {
            "基础攻击": final["char_base_attack"],
            "力量": attr["力量"]["base"],
            "敏捷": attr["敏捷"]["base"],
            "智识": attr["智识"]["base"],
            "意志": attr["意志"]["base"],
            "主能力": main_attr,
            "副能力": sub_attr,
        },
        "武器": {
            "基础攻击": final["weapon_base_attack"],
            "攻击力+": final["attack_bonus_multiplier"] - 1.0,
            "附加攻击力+": final["additional_attack"],
        },
        "装备": {
            "攻击力平值": 0.0,
        },
        "computed": {
            "主能力平值加算": ability["main_flat"],
            "副能力平值加算": ability["sub_flat"],
            "主能力百分比": ability["main_pct"],
            "副能力百分比": ability["sub_pct"],
            "主能力": main_attr,
            "副能力": sub_attr,
            "最终攻击力": 0.0,
            "技能倍率": 1.0,
            "暴击区": 1.0,
            "伤害加成": 1.0,
            "伤害减免": 1.0,
            "增幅": 1.0,
            "虚弱": 1.0,
            "庇护": 1.0,
            "脆弱": 1.0,
            "易伤": 1.0,
            "防御": 0.5,
            "失衡易伤": 1.0,
            "抗性": 1.0,
            "非主控减伤": 1.0,
            "连击增伤": 1.0,
            "特殊乘区": 1.0,
        },
    }


class TestGeneratedEndfieldDAG:
    """验证 dag_config.py 产出的 DAG 与现有引擎一致。"""

    @pytest.fixture(scope="class")
    def generated_dag(self):
        from calculation.multiplicative_zones.dag_config import generate, OUTPUT_PATH

        dag = generate()
        assert dag.name == "终末地伤害公式（完整版）"
        assert OUTPUT_PATH == _EXPECTED_OUTPUT, f"{OUTPUT_PATH} != {_EXPECTED_OUTPUT}"
        return dag

    @pytest.fixture(scope="class")
    def saved_dag(self, generated_dag):
        import json
        from calculation.multiplicative_zones.dag_config import save_dag

        save_dag(generated_dag)
        assert _EXPECTED_OUTPUT.exists(), f"输出文件不存在: {_EXPECTED_OUTPUT}"

        with _EXPECTED_OUTPUT.open(encoding="utf-8") as f:
            raw = json.load(f)
        assert raw["schema_version"] == "dag-v1"
        assert "subgraphs" in raw and "ability_bonus" in raw["subgraphs"]
        assert "subgraphs" in raw and "final_attack" in raw["subgraphs"]
        assert "subgraphs" in raw and "single_hit_damage" in raw["subgraphs"]
        return load_dag(_EXPECTED_OUTPUT)

    @pytest.fixture(scope="class")
    def context(self):
        import json

        char: dict[str, Any] | None = None
        weapon: dict[str, Any] | None = None
        for item in json.loads(PARTICIPANTS_JSON.read_text(encoding="utf-8")):
            if item.get("名称") == "秋栗":
                char = item
                break
        for item in json.loads(WEAPONS_JSON.read_text(encoding="utf-8")):
            if item.get("名称") == "逐鳞3.0":
                weapon = item
                break
        if char is None or weapon is None:
            pytest.skip("测试数据不可用")
        return _build_dag_context(char, weapon, level=80, trust_level=0)

    def test_ability_bonus_subgraph(self, saved_dag, context):
        """验证 ability_bonus 子图数值与现有引擎一致。"""
        from calculation.multiplicative_zones.ability_bonus_details import (
            calculate_ability_bonus_with_details,
        )
        import json

        char: dict[str, Any] | None = None
        weapon: dict[str, Any] | None = None
        for item in json.loads(PARTICIPANTS_JSON.read_text(encoding="utf-8")):
            if item.get("名称") == "秋栗":
                char = item
                break
        for item in json.loads(WEAPONS_JSON.read_text(encoding="utf-8")):
            if item.get("名称") == "逐鳞3.0":
                weapon = item
                break

        existing = calculate_ability_bonus_with_details(
            char, weapon, level=80, trust_level=0,
        )
        ctx = _minimal_context()
        ctx["computed"].update({
            "主能力平值加算": existing["main_flat"],
            "副能力平值加算": existing["sub_flat"],
            "主能力百分比": existing["main_pct"],
            "副能力百分比": existing["sub_pct"],
            "主能力": existing["main_attr"],
            "副能力": existing["sub_attr"],
        })
        results = evaluate_graph(saved_dag, ctx)

        dag_bonus = results.outputs.get("能力值加成")
        assert dag_bonus is not None, "DAG 未输出能力值加成"
        assert dag_bonus == pytest.approx(existing["bonus"], rel=1e-9), (
            f"DAG: {dag_bonus}, Existing: {existing['bonus']}"
        )

    def test_final_attack_parity(self, saved_dag, context):
        """验证最终攻击力 DAG 输出与现有引擎一致。"""
        from calculation.multiplicative_zones.final_attack_zone import (
            calculate_final_attack_with_details,
        )
        import json

        char: dict[str, Any] | None = None
        weapon: dict[str, Any] | None = None
        for item in json.loads(PARTICIPANTS_JSON.read_text(encoding="utf-8")):
            if item.get("名称") == "秋栗":
                char = item
                break
        for item in json.loads(WEAPONS_JSON.read_text(encoding="utf-8")):
            if item.get("名称") == "逐鳞3.0":
                weapon = item
                break

        existing = calculate_final_attack_with_details(
            char, weapon, char_level=80, weapon_level=80, trust_level=0,
        )

        from calculation.multiplicative_zones.ability_bonus_details import (
            calculate_ability_bonus_with_details,
        )
        ability = calculate_ability_bonus_with_details(char, weapon, level=80, trust_level=0)

        ctx = _minimal_context()
        ctx["角色"].update({
            "基础攻击": existing["char_base_attack"],
            "主能力": ability["main_attr"],
            "副能力": ability["sub_attr"],
        })
        ctx["武器"].update({
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

        results = evaluate_graph(saved_dag, ctx)
        dag_final = results.outputs.get("最终攻击力")
        assert dag_final is not None, "DAG 未输出最终攻击力"
        assert dag_final == pytest.approx(existing["final_attack"], rel=1e-9), (
            f"DAG: {dag_final}, Existing: {existing['final_attack']}"
        )

    def test_single_hit_damage_parity(self, saved_dag, context):
        """验证单段伤害 15 乘区 DAG 输出与现有引擎一致。"""
        from calculation.damage.engine.types import DamageContext
        from calculation.damage.engine.calculate import calculate_single_hit_damage

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

        dag_ctx = _minimal_context()
        dag_ctx["computed"].update({
            "最终攻击力": ctx.final_attack,
            "技能倍率": ctx.skill_multiplier,
            "暴击区": 1.0,
            "伤害加成": 1.0 + ctx.damage_type_bonus,
            "伤害减免": 1.0,
            "增幅": 1.0,
            "虚弱": 1.0,
            "庇护": 1.0,
            "脆弱": 1.0,
            "易伤": 1.0,
            "防御": 100.0 / (100.0 + ctx.enemy_defense),
            "失衡易伤": float(1.0),
            "抗性": 1.0,
            "非主控减伤": 1.0,
            "连击增伤": 1.0,
            "特殊乘区": 1.0,
        })

        results = evaluate_graph(saved_dag, dag_ctx)
        dag_damage = results.outputs.get("最终伤害")
        assert dag_damage is not None, "DAG 未输出最终伤害"
        assert dag_damage == pytest.approx(existing.final_damage, rel=1e-9), (
            f"DAG: {dag_damage}, Existing: {existing.final_damage}"
        )

    def test_all_outputs_present(self, saved_dag, context):
        """验证 DAG 包含所有预期输出。"""
        results = evaluate_graph(saved_dag, context)
        expected = {"最终攻击力", "最终伤害"}
        assert expected.issubset(set(results.outputs.keys())), (
            f"缺少输出: {expected - set(results.outputs.keys())}"
        )

    def test_graph_is_valid(self, generated_dag):
        """验证生成的 DAG 结构有效（schema_version、子图引用正确）。"""
        assert generated_dag.schema_version == "dag-v1"
        assert "ability_bonus" in generated_dag.subgraphs
        assert "final_attack" in generated_dag.subgraphs
        assert "single_hit_damage" in generated_dag.subgraphs
        assert len(generated_dag.outputs) >= 2
