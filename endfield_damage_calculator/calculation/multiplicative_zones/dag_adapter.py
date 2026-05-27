#!/usr/bin/env python3
"""DAG 适配器：将 DAG 引擎接入 zone_snapshot 计算链。

设计：
- ``build_dag_context`` 从 char/weapon/levels 提取 DAG 所需上下文（委托现有引擎做预处理）
- ``evaluate_attack_chain_via_dag`` 加载 DAG → 构建上下文 → 求值 → 返回攻击力/能力值结果
- ``compute_snapshot_with_dag`` 用 DAG 引擎替代现有引擎生成乘区展示行
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from calc_framework.dag.schema import DAGGraph
    from calculation.multiplicative_zones.zone_snapshot import MultiplicativeZoneSelection

_FRAMEWORK_DIR = Path(__file__).resolve().parents[3] / "framework"
_SRC_DIR = _FRAMEWORK_DIR / "src"

if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

_CONFIGS_DIR = _SRC_DIR / "calc_framework" / "configs"
_DAG_PATH = _CONFIGS_DIR / "endfield_full.dag.json"

from calculation.multiplicative_zones import ZoneDisplayLine


def _existing_attack_chain(
    char: dict[str, Any],
    weapon: dict[str, Any] | None,
    *,
    char_level: int,
    weapon_level: int,
    trust_level: int,
    bonuses_kwargs: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """运行现有引擎三层计算，返回 (attr_details, ability, final)。"""
    from calculation.multiplicative_zones.ability_bonus_details import (
        calculate_ability_bonus_with_details,
    )
    from calculation.multiplicative_zones.attribute_zone import (
        calculate_attribute_zones_with_details,
    )
    from calculation.multiplicative_zones.final_attack_zone import (
        calculate_final_attack_with_details,
    )

    attr = calculate_attribute_zones_with_details(
        char, weapon, level=char_level, trust_level=trust_level, **bonuses_kwargs,
    )
    ability = calculate_ability_bonus_with_details(
        char, weapon, level=char_level, trust_level=trust_level, **bonuses_kwargs,
    )
    final = calculate_final_attack_with_details(
        char, weapon,
        char_level=char_level, weapon_level=weapon_level,
        trust_level=trust_level, **bonuses_kwargs,
    )
    return attr, ability, final


def build_dag_context(
    char: dict[str, Any],
    weapon: dict[str, Any] | None,
    *,
    char_level: int,
    weapon_level: int,
    trust_level: int = 0,
    bonuses_kwargs: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """从角色/武器数据构建 DAG 求值上下文。

    委托现有引擎做预处理（装备词条解析、武器技能分类等重型逻辑），
    然后将中间结果填入 DAG 上下文完成公式求值。
    """
    kwargs = bonuses_kwargs or {}
    attr, ability, final = _existing_attack_chain(
        char, weapon,
        char_level=char_level, weapon_level=weapon_level,
        trust_level=trust_level, bonuses_kwargs=kwargs,
    )

    return {
        "角色": {
            "基础攻击": final["char_base_attack"],
            "力量": attr["力量"]["base"],
            "敏捷": attr["敏捷"]["base"],
            "智识": attr["智识"]["base"],
            "意志": attr["意志"]["base"],
            "主能力": ability["main_attr"],
            "副能力": ability["sub_attr"],
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
            "主能力": ability["main_attr"],
            "副能力": ability["sub_attr"],
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


_DAG_SERVICE_CACHE: Any = None


def _get_dag_service() -> Any:
    """获取 DAGService（模块级缓存 + 惰性生成）。"""
    global _DAG_SERVICE_CACHE
    if _DAG_SERVICE_CACHE is not None:
        return _DAG_SERVICE_CACHE

    from calc_framework.dag.service import DAGService

    if _DAG_PATH.exists():
        _DAG_SERVICE_CACHE = DAGService.from_file(_DAG_PATH)
        return _DAG_SERVICE_CACHE

    _DAG_PATH.parent.mkdir(parents=True, exist_ok=True)
    from calculation.multiplicative_zones.dag_config import generate, save_dag
    g = generate()
    save_dag(g)
    _DAG_SERVICE_CACHE = DAGService(g)
    return _DAG_SERVICE_CACHE


def evaluate_attack_chain_via_dag(
    char: dict[str, Any],
    weapon: dict[str, Any] | None,
    *,
    char_level: int,
    weapon_level: int,
    trust_level: int = 0,
    bonuses_kwargs: dict[str, Any] | None = None,
) -> dict[str, float]:
    """用 DAG 引擎计算攻击力链，返回结果字典。

    返回:
        {"final_attack": float, "ability_bonus": float}
    """
    svc = _get_dag_service()

    kwargs = bonuses_kwargs or {}
    ctx = build_dag_context(
        char, weapon,
        char_level=char_level, weapon_level=weapon_level,
        trust_level=trust_level, bonuses_kwargs=kwargs,
    )

    result = svc.evaluate(ctx)
    return {
        "final_attack": result.outputs.get("最终攻击力", 0.0),
        "ability_bonus": result.outputs.get("能力值加成", 0.0),
    }


def compute_snapshot_with_dag(
    selection: MultiplicativeZoneSelection,
) -> list[ZoneDisplayLine]:
    """用 DAG 引擎计算完整乘区快照，返回展示行列表。

    攻击力链（最终攻击力 + 能力值加成）由 DAG 求值，
    属性显示行（力量/敏捷/智识/意志）仍委托现有引擎（DAG 未做装备平铺解析）。
    """
    from calculation.multiplicative_zones.ability_bonus_details import (
        calculate_ability_bonus_with_details,
    )
    from calculation.multiplicative_zones.attribute_zone import (
        calculate_attribute_zones_with_details,
    )
    from calculation.multiplicative_zones.defense_zone import DefenseReductionZone
    from calculation.multiplicative_zones.final_attack_zone import (
        calculate_final_attack_with_details,
    )

    ATTR_DISPLAY_ORDER = ("力量", "敏捷", "智识", "意志")

    char = selection.character
    weapon = selection.weapon
    kwargs = selection.bonuses.calculation_kwargs()
    lines: list[ZoneDisplayLine] = []

    defense = DefenseReductionZone().calculate()
    lines.append(ZoneDisplayLine(f"敌方防御减伤: {defense:.4f}", "#4ECDC4"))

    attr_details = calculate_attribute_zones_with_details(
        char, weapon, level=selection.char_level, trust_level=selection.trust_level, **kwargs,
    )
    for attr_name in ATTR_DISPLAY_ORDER:
        details = attr_details.get(attr_name, {"base": 0.0, "bonus": 0.0, "total": 0.0})
        base_value = details["base"]
        bonus_value = details["bonus"]
        total_value = details["total"]
        if bonus_value > 0:
            text = f"{attr_name}: {total_value:.1f} ({base_value:.1f}+{bonus_value:.1f})"
        else:
            text = f"{attr_name}: {total_value:.1f}"
        lines.append(ZoneDisplayLine(text, "#B8B8B8"))

    ability = calculate_ability_bonus_with_details(
        char, weapon, level=selection.char_level, trust_level=selection.trust_level, **kwargs,
    )

    dag_result = evaluate_attack_chain_via_dag(
        char, weapon,
        char_level=selection.char_level,
        weapon_level=selection.weapon_level,
        trust_level=selection.trust_level,
        bonuses_kwargs=kwargs,
    )
    dag_ability_bonus = dag_result["ability_bonus"]
    dag_final_attack = dag_result["final_attack"]

    main_attr = ability["main_attr"]
    sub_attr = ability["sub_attr"]
    if main_attr and sub_attr:
        ab_text = (
            f"能力值加成: {dag_ability_bonus:.4f} "
            f"({main_attr}:{ability['main_value']:.1f}*0.005+"
            f"{sub_attr}:{ability['sub_value']:.1f}*0.002)"
        )
    else:
        ab_text = f"能力值加成: {dag_ability_bonus:.4f}"
    lines.append(ZoneDisplayLine(ab_text, "#FFD700"))

    final = calculate_final_attack_with_details(
        char, weapon,
        char_level=selection.char_level, weapon_level=selection.weapon_level,
        trust_level=selection.trust_level, **kwargs,
    )

    lines.append(
        ZoneDisplayLine(
            f"基础攻击力: {final['base_attack']:.1f} "
            f"({final['char_base_attack']:.1f}+{final['weapon_base_attack']:.1f})",
            "#00D4AA",
        )
    )
    lines.append(
        ZoneDisplayLine(
            f"攻击加成攻击力: {final['attack_bonus_attack']:.1f} "
            f"({final['base_attack']:.1f}×{final['attack_bonus_multiplier']:.3f})",
            "#9B59B6",
        )
    )
    lines.append(
        ZoneDisplayLine(
            f"中间攻击力: {final['intermediate_attack']:.1f} "
            f"({final['attack_bonus_attack']:.1f}+{final['additional_attack']:.1f})",
            "#3498DB",
        )
    )

    ability_multiplier = 1.0 + dag_ability_bonus

    lines.append(
        ZoneDisplayLine(
            f"最终攻击力: {dag_final_attack:.1f} "
            f"({final['intermediate_attack']:.1f}×{ability_multiplier:.4f})",
            "#E74C3C",
        )
    )
    return lines
