# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""明日方舟技能描述解析器。

从 BWIKI 爬取的技能描述 text 中提取：
- 伤害倍率 / 攻击力加成
- 连发数/段数
- 条件触发倍率
- 伤害类型 / 治疗标记
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


@dataclass
class ParsedSkillInfo:
    """技能解析结果。

    语义说明（用于 DAG 计算）：
    - effective_multiplier: 每段伤害的最终乘数（推荐给 DAG 的 skill_multiplier）
    - atk_buff_hint: 若技能含 ATK buff，给出建议的 atk_percent_bonus
    """

    name: str = ""
    sp_type: str = ""
    trigger: str = ""

    effective_multiplier: float = 1.0
    atk_buff_hint: float = 0.0
    hit_count: int = 1
    has_conditional: bool = False
    conditional_mult: float = 1.0

    damage_type: str = "physical"
    is_healing: bool = False
    sp_cost: int = 0
    init_sp: int = 0
    duration: int = 0
    description: str = ""

    total_mult: float = 1.0

    # 原始提取值（调试用）
    _atk_buff_pct: float = 0.0
    _direct_atk_mult: float = 1.0
    _equiv_damage_mult: float = 1.0


def _strip_wiki_markup(text: str) -> str:
    text = re.sub(r"\{\{蓝色\|([^}]+)\}\}", r"\1", text)
    text = re.sub(r"\{\{color\|[^|]+\|([^}]+)\}\}", r"\1", text)
    text = re.sub(r"<BR\s*/?>", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    """strip wiki markup。"""
    return text.strip()


def parse_skill(skill_data: dict[str, Any], level: int = 7) -> ParsedSkillInfo:
    """解析指定等级的技能参数。"""
    info = ParsedSkillInfo(
        name=skill_data.get("name", ""),
        sp_type=skill_data.get("sp_type", ""),
        trigger=skill_data.get("trigger", ""),
    )

    levels = skill_data.get("levels", [])
    if not levels:
        return info

    idx = min(max(level - 1, 0), len(levels) - 1)
    lv = levels[idx]
    raw_desc = lv.get("description", "")
    info.description = _strip_wiki_markup(raw_desc)
    info.sp_cost = lv.get("sp_cost", 0)
    info.init_sp = lv.get("init_sp", 0)

    dur_str = str(lv.get("duration", "0"))
    try:
        info.duration = int(dur_str)
    except ValueError:
        info.duration = 0

    _extract_all_params(info, raw_desc)

    return info


def _extract_all_params(info: ParsedSkillInfo, raw_desc: str) -> None:
    """全面提取所有参数（不早返回）。"""
    desc = _strip_wiki_markup(raw_desc)

    # --- 治疗检测 ---
    # 严格：只有明确说"治疗"才标记（排除"恢复技力""恢复生命上限"等）
    if "治疗" in desc and "攻击力" in desc:
        info.is_healing = True
    # "相当于攻击力XX%的生命"也视为治疗
    if re.search(r"相当于攻击力[\d.]+%的.*?(?:生命|血量)", desc):
        info.is_healing = True

    # --- 伤害类型 ---
    type_order = [("真实", "true"), ("法术", "magical"), ("物理", "physical")]
    for kw, dt in type_order:
        if kw in desc:
            info.damage_type = dt
            break

    # --- 条件触发倍率 ---
    cond = re.search(r"仅攻击到(?:一个|1个)敌人时.*?攻击力提升至(\d+(?:\.\d+)?)%", desc)
    if cond:
        info.has_conditional = True
        info.conditional_mult = float(cond.group(1)) / 100.0

    # --- 纯攻速技能 ---
    if "攻击速度" in desc and "攻击力" not in desc and "相当于" not in desc:
        info.effective_multiplier = 1.0
        _extract_hit_count(info, desc)
        _compute_total(info)
        return

    # --- 攻击力+XX% (ATK buff) ---
    buff = re.search(r"攻击力\+(\d+(?:\.\d+)?)%", desc)
    if buff:
        info._atk_buff_pct = float(buff.group(1)) / 100.0

    # --- 攻击力提升至XX% (direct ATK set) ---
    # 排除条件语句内的（如"仅攻击到一人时对其攻击力提升至150%"）
    for m in re.finditer(r"攻击力提升至(\d+(?:\.\d+)?)%", desc):
        pos = m.start()
        before = desc[max(0, pos - 15) : pos]
        if "仅攻击到" in before or "仅" in before:
            continue
        info._direct_atk_mult = float(m.group(1)) / 100.0
        break

    # --- 相当于攻击力XX% (damage conversion) ---
    eq = re.search(r"相当于攻击力(\d+(?:\.\d+)?)%", desc)
    if eq:
        info._equiv_damage_mult = float(eq.group(1)) / 100.0

    # --- 攻击力XX%的 (damage conversion, variant) ---
    if info._equiv_damage_mult == 1.0:
        pct_of = re.search(r"攻击力(\d+(?:\.\d+)?)%的", desc)
        if pct_of:
            info._equiv_damage_mult = float(pct_of.group(1)) / 100.0

    # --- 连发数 ---
    _extract_hit_count(info, desc)

    # --- 确定 effective_multiplier ---
    _resolve_effective_mult(info)

    # --- 计算总倍率 ---
    _compute_total(info)


def _resolve_effective_mult(info: ParsedSkillInfo) -> None:
    """综合各种原始值确定 effective_multiplier。"""
    has_buff = info._atk_buff_pct > 0.0
    has_direct = info._direct_atk_mult > 1.0
    has_equiv = info._equiv_damage_mult > 1.0 or (info._equiv_damage_mult < 1.0 and info._equiv_damage_mult != 1.0)

    # 规则 1: 有 equivalent damage mult → 用它
    if has_equiv:
        info.effective_multiplier = info._equiv_damage_mult
        info.atk_buff_hint = info._atk_buff_pct
        return

    # 规则 2: 有 direct ATK set → 用它
    if has_direct:
        info.effective_multiplier = info._direct_atk_mult
        info.atk_buff_hint = info._atk_buff_pct
        return

    # 规则 3: 只有 ATK buff → ATK 加成的普攻
    if has_buff:
        info.effective_multiplier = 1.0
        info.atk_buff_hint = info._atk_buff_pct
        return

    # 规则 4: 都没有 → 1.0
    info.effective_multiplier = 1.0


def _extract_hit_count(info: ParsedSkillInfo, desc: str) -> None:
    for pat in [r"(\d+)连发", r"(\d+)次射击", r"连续攻击(\d+)次"]:
        m = re.search(pat, desc)
        if m:
            info.hit_count = int(m.group(1))
            return
    """extract hit count。"""


def _compute_total(info: ParsedSkillInfo) -> None:
    info.total_mult = info.effective_multiplier * info.hit_count
    """compute total。"""


def parse_auto_attack() -> ParsedSkillInfo:
    """返回普攻的解析结果。"""
    return ParsedSkillInfo(name="普攻", description="普通攻击")
