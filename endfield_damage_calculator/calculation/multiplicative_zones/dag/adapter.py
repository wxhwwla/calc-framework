#!/usr/bin/env python3
"""DAG 适配器：将 DAG 引擎接入 zone_snapshot 计算链。

设计：
- ``EndfieldContextLoader`` 实现框架 ``DataContextLoader`` 接口
- ``AdapterPackage`` 替代旧的 ``_get_dag_service()``，零自定义缓存
- ``compute_snapshot_with_dag`` 用 DAG 引擎替代现有引擎生成乘区展示行
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from calculation.multiplicative_zones.zone_snapshot import MultiplicativeZoneSelection

_FRAMEWORK_DIR = Path(__file__).resolve().parents[4] / "framework"
_SRC_DIR = _FRAMEWORK_DIR / "src"
_ADAPTER_DIR = _FRAMEWORK_DIR / "adapters" / "endfield"

if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

from calc_framework.config.adapter import AdapterPackage

from calculation.multiplicative_zones import ZoneDisplayLine
from calculation.multiplicative_zones.dag.loader import EndfieldContextLoader


def build_dag_context(
    char: dict[str, Any],
    weapon: dict[str, Any] | None,
    *,
    char_level: int,
    weapon_level: int,
    trust_level: int = 0,
    bonuses_kwargs: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """从角色/武器数据构建 DAG 求值上下文（委托 EndfieldContextLoader）。"""
    loader = EndfieldContextLoader()
    return loader.build_context(
        character=char,
        weapon=weapon,
        char_level=char_level,
        weapon_level=weapon_level,
        trust_level=trust_level,
        bonuses_kwargs=bonuses_kwargs or {},
    )


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
    pkg = _ensure_dag()
    kwargs = bonuses_kwargs or {}
    ctx = build_dag_context(
        char, weapon,
        char_level=char_level, weapon_level=weapon_level,
        trust_level=trust_level, bonuses_kwargs=kwargs,
    )

    result = pkg.dag_service.evaluate(ctx)
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
    from calculation.multiplicative_zones.base_zone import DefenseReductionZone
    from calculation.multiplicative_zones.final_attack_zone import (
        calculate_final_attack_with_details,
    )

    attr_display_order = ("力量", "敏捷", "智识", "意志")

    char = selection.character
    weapon = selection.weapon
    kwargs = selection.bonuses.calculation_kwargs()
    lines: list[ZoneDisplayLine] = []

    defense = DefenseReductionZone().calculate()
    lines.append(ZoneDisplayLine(f"敌方防御减伤: {defense:.4f}", "#4ECDC4"))

    attr_details = calculate_attribute_zones_with_details(
        char, weapon, level=selection.char_level, trust_level=selection.trust_level, **kwargs,
    )
    for attr_name in attr_display_order:
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


_ADAPTER_PACKAGE: AdapterPackage | None = None


def _ensure_dag() -> AdapterPackage:
    """获取终末地 AdapterPackage（模块级缓存 + 惰性生成）。

    首次访问如 DAG JSON 缺失，则自动运行 config 脚本生成。
    """
    global _ADAPTER_PACKAGE
    if _ADAPTER_PACKAGE is not None:
        return _ADAPTER_PACKAGE

    if not _ADAPTER_DIR.is_dir():
        _ADAPTER_DIR.mkdir(parents=True)
        _write_default_meta()

    try:
        _ADAPTER_PACKAGE = AdapterPackage(_ADAPTER_DIR)
    except Exception:
        _generate_dag_json()
        _ADAPTER_PACKAGE = AdapterPackage(_ADAPTER_DIR)

    return _ADAPTER_PACKAGE


def _generate_dag_json() -> None:
    from calculation.multiplicative_zones.dag.config import generate, save_dag

    g = generate()
    save_dag(g)


def _write_default_meta() -> None:
    import json

    (_ADAPTER_DIR / "meta.json").write_text(
        json.dumps({
            "name": "终末地伤害计算",
            "game": "明日方舟：终末地",
            "version": "3.0.0",
            "schema_version": "dag-v1",
            "entry_dag": "../../src/calc_framework/configs/endfield_full.dag.json",
        }, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
