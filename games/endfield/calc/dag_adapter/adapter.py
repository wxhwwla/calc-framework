#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""DAG 适配器：将 DAG 引擎接入 zone_snapshot 计算链。

迁移自 ``multiplicative_zones.dag.adapter``。

设计：
- ``EndfieldContextLoader`` 实现框架 ``DataContextLoader`` 接口
- ``AdapterPackage`` 替代旧的 ``_get_dag_service()``，零自定义缓存
- ``compute_snapshot_with_dag`` 用 DAG 引擎替代现有引擎生成乘区展示行
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from calc_framework.config.adapter import AdapterPackage

from games.endfield.calc.dag_adapter.loader import EndfieldContextLoader
from games.endfield.calc.zone_snapshot.types import ZoneDisplayLine

_FRAMEWORK_DIR = Path(__file__).resolve().parents[4] / "framework"
_SRC_DIR = _FRAMEWORK_DIR / "src"
_ADAPTER_DIR = _FRAMEWORK_DIR / "adapters" / "endfield"

if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

ATTR_DISPLAY_ORDER = ("力量", "敏捷", "智识", "意志")


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
    selection: Any,
) -> list[ZoneDisplayLine]:
    """用 DAG 引擎计算完整乘区快照，返回展示行列表。

    全部乘区值由 DAG 求值，不再调用旧引擎的任何计算函数：
    - ability_bonus / final_attack / defense_reduction 由 DAG 子图直接计算
    - 属性乘区（力量/敏捷/智识/意志）从 DAG 输出 + Context 展示行
    - 全部中间值和最终值均从 DAG 输出读取
    """
    char = selection.character
    weapon = selection.weapon
    b = selection.bonuses
    kwargs: dict[str, Any] = b.calculation_kwargs()

    pkg = _ensure_dag()
    ctx = build_dag_context(
        char, weapon,
        char_level=selection.char_level,
        weapon_level=selection.weapon_level,
        trust_level=selection.trust_level,
        bonuses_kwargs=kwargs,
    )
    result = pkg.dag_service.evaluate(ctx)
    zo = result.outputs

    lines: list[ZoneDisplayLine] = []

    # 防御减伤 — DAG 计算
    def_reduction = zo.get("防御区", 0.5)
    lines.append(ZoneDisplayLine(f"敌方防御减伤: {def_reduction:.4f}", "#4ECDC4"))

    # 属性乘区 — 全部从 DAG 输出 + Context 读取
    for attr_name in ATTR_DISPLAY_ORDER:
        total = zo.get(f"{attr_name}最终值", 0.0)
        base = ctx.get("character", {}).get(attr_name, 0.0)
        bonus = ctx.get("computed", {}).get(f"{attr_name}加成值", 0.0)
        if bonus > 0:
            text = f"{attr_name}: {total:.1f} ({base:.1f}+{bonus:.1f})"
        else:
            text = f"{attr_name}: {total:.1f}"
        lines.append(ZoneDisplayLine(text, "#B8B8B8"))

    # 能力值加成 — DAG 计算
    ability_bonus = zo.get("能力值加成", 0.0)
    main_attr = ctx.get("computed", {}).get("主能力", "")
    sub_attr = ctx.get("computed", {}).get("副能力", "")
    if main_attr and sub_attr:
        main_flat = ctx.get("computed", {}).get("主能力平值加算", 0.0)
        sub_flat = ctx.get("computed", {}).get("副能力平值加算", 0.0)
        main_pct = ctx.get("computed", {}).get("主能力百分比", 0.0)
        sub_pct = ctx.get("computed", {}).get("副能力百分比", 0.0)
        ab_text = (
            f"能力值加成: {ability_bonus:.4f} "
            f"({main_attr}:{main_flat:.1f}*(1+{main_pct:.1f}%)*0.005+"
            f"{sub_attr}:{sub_flat:.1f}*(1+{sub_pct:.1f}%)*0.002)"
        )
    else:
        ab_text = f"能力值加成: {ability_bonus:.4f}"
    lines.append(ZoneDisplayLine(ab_text, "#FFD700"))

    # 攻击力链详情 — 全部从 DAG 输出 + Context 读取
    base_atk = ctx.get("computed", {}).get("基础攻击力合计", 0.0)
    char_base = ctx.get("computed", {}).get("角色基础攻击力", 0.0)
    weapon_base = ctx.get("computed", {}).get("武器基础攻击力", 0.0)
    atk_bonus_atk = ctx.get("computed", {}).get("攻击加成攻击力", 0.0)
    mid_atk = ctx.get("computed", {}).get("中间攻击力", 0.0)
    add_atk = ctx.get("computed", {}).get("额外攻击力", 0.0)
    atk_mult = 1.0 + ctx.get("weapon", {}).get("攻击力+", 0.0)

    lines.append(
        ZoneDisplayLine(
            f"基础攻击力: {base_atk:.1f} "
            f"({char_base:.1f}+{weapon_base:.1f})",
            "#00D4AA",
        )
    )
    lines.append(
        ZoneDisplayLine(
            f"攻击加成攻击力: {atk_bonus_atk:.1f} "
            f"({base_atk:.1f}×{atk_mult:.3f})",
            "#9B59B6",
        )
    )
    lines.append(
        ZoneDisplayLine(
            f"中间攻击力: {mid_atk:.1f} "
            f"({atk_bonus_atk:.1f}+{add_atk:.1f})",
            "#3498DB",
        )
    )

    final_atk = zo.get("最终攻击力", 0.0)
    lines.append(
        ZoneDisplayLine(
            f"最终攻击力: {final_atk:.1f} "
            f"({mid_atk:.1f}×(1+{ability_bonus:.4f}))",
            "#E74C3C",
        )
    )

    # 最终伤害 — DAG 计算（15 乘区连乘）
    final_dmg = zo.get("最终伤害", 0.0)
    lines.append(ZoneDisplayLine(f"最终伤害: {final_dmg:.2f}", "#E74C3C"))

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
    from games.endfield.calc.dag_adapter.config import generate, save_dag

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
