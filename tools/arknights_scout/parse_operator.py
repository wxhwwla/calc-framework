# SPDX-License-Identifier: AGPL-3.0
"""Arknights 干员 wikitext 解析器。

从 {{干员 ...}} 模板中提取基础数值、天赋和技能。
"""

from __future__ import annotations

import re
from typing import Any


_TEMPLATE_START_RE = re.compile(r"\{\{\s*(?:干员|特勤干员)")

_KEY_VAL_RE = re.compile(r"^\|([^=\n]+?)\s*=[ \t]*(.*?)$", re.MULTILINE)


def _extract_template_body(text: str) -> str | None:
    """查找 `{{干员 / {{特勤干员}}` 模板并提取主体内容。

    使用计数器跟踪嵌套 `{{` / `}}` 深度以正确匹配关闭括号。
    """
    start = _TEMPLATE_START_RE.search(text)
    if not start:
        return None
    pos = start.start()
    # 跳过 `{{干员` 和同一行上的其余内容（注释等）
    nl = text.find("\n", pos)
    if nl == -1:
        return None
    body_start = nl + 1
    # 从模板开头 +1（跳过开头的 {{）计数深度
    depth = 1
    i = body_start
    while i < len(text) - 1:
        if text[i : i + 2] == "{{":
            depth += 1
            i += 2
        elif text[i : i + 2] == "}}":
            depth -= 1
            if depth == 0:
                return text[body_start:i]
            i += 2
        else:
            i += 1
    return None


def parse_template_kv(text: str) -> dict[str, str]:
    """从 `{{干员 ...}}` 或 `{{特勤干员 ...}}` wikitext 中提取所有 key=value 对。"""
    body = _extract_template_body(text)
    if not body:
        return {}
    result: dict[str, str] = {}
    for m in _KEY_VAL_RE.finditer(body):
        key = m.group(1).strip()
        val = m.group(2).strip()
        if val:
            result[key] = val
    return result


def parse_rarity(rarity_str: str) -> int:
    try:
        return int(rarity_str)
    except (ValueError, TypeError):
        return 0


def parse_trust_bonus(kv: dict[str, str]) -> dict[str, int]:
    result: dict[str, int] = {}
    for field, label in [("信赖攻击", "攻击"), ("信赖防御", "防御"), ("信赖生命", "生命"), ("信赖法抗", "法抗")]:
        raw = kv.get(field, "").strip()
        if raw.startswith("+"):
            raw = raw[1:]
        if raw:
            try:
                result[label] = int(raw)
            except ValueError:
                pass
    return result


def parse_talents(kv: dict[str, str]) -> list[dict[str, str]]:
    talents: list[dict[str, str]] = []
    for i in range(1, 4):
        name = kv.get(f"天赋{i}", "").strip()
        if not name:
            continue
        desc = kv.get(f"天赋{i}描述", "").strip()
        unlock = kv.get(f"天赋{i}解锁条件", "").strip()
        talent: dict[str, str] = {"name": name, "description": desc}
        if unlock:
            talent["unlock"] = unlock
        upgraded = kv.get(f"天赋{i}提升后", "").strip()
        upgrade_desc = kv.get(f"天赋{i}提升后描述", "").strip()
        if upgraded and upgrade_desc:
            talent["upgrade_name"] = upgraded
            talent["upgrade_description"] = upgrade_desc
        if upgraded and not upgrade_desc:
            talent["upgrade_name"] = upgraded
        talents.append(talent)
    return talents


def _parse_level_range(values: list[str]) -> list[dict[str, Any]]:
    levels: list[dict[str, Any]] = []
    for raw in values:
        if not raw or raw == "-":
            continue
        level: dict[str, Any] = {}
        try:
            level["sp_cost"] = int(raw)
        except ValueError:
            level["sp_cost_raw"] = raw
        levels.append(level)
    return levels


def parse_skills(kv: dict[str, str]) -> list[dict[str, Any]]:
    skills: list[dict[str, Any]] = []
    for i in range(1, 4):
        name = kv.get(f"技能{i}", "").strip()
        if not name:
            continue

        skill: dict[str, Any] = {"name": name}
        skill_type = kv.get(f"技能{i}回复类型", "").strip()
        if skill_type:
            skill["sp_type"] = skill_type
        trigger = kv.get(f"技能{i}触发类型", "").strip()
        if trigger:
            skill["trigger"] = trigger

        descriptions: list[str] = []
        sp_costs: list[str] = []
        init_sps: list[str] = []
        durations: list[str] = []

        for lvl in range(1, 11):
            desc = kv.get(f"技能{i}描述{lvl}", "").strip()
            sp = kv.get(f"技能{i}技力消耗{lvl}", "").strip()
            init = kv.get(f"技能{i}初始技力{lvl}", "").strip()
            dur = kv.get(f"技能{i}持续时间{lvl}", "").strip()

            has_desc = bool(desc)
            has_sp = bool(sp)
            has_init = bool(init)
            has_dur = bool(dur)

            if has_desc:
                descriptions.append(desc)
            if has_sp:
                sp_costs.append(sp)
            if has_init:
                init_sps.append(init)
            if has_dur:
                durations.append(dur)

        if not descriptions and not sp_costs:
            continue

        max_len = max(len(descriptions), len(sp_costs), len(init_sps), len(durations))
        levels: list[dict[str, Any]] = []
        for idx in range(max_len):
            level: dict[str, Any] = {}
            if idx < len(descriptions):
                level["description"] = descriptions[idx]
            if idx < len(sp_costs):
                level["sp_cost"] = int(sp_costs[idx]) if sp_costs[idx].isdigit() else sp_costs[idx]
            if idx < len(init_sps):
                level["init_sp"] = int(init_sps[idx]) if init_sps[idx].isdigit() else init_sps[idx]
            if idx < len(durations):
                level["duration"] = durations[idx]
            levels.append(level)

        if levels:
            skill["levels"] = levels
            skills.append(skill)

    return skills


def parse_base_stats(kv: dict[str, str], rarity: int) -> dict[str, Any]:
    stats: dict[str, Any] = {}
    for field, key in [("初始生命max", "hp"), ("初始攻击max", "atk"), ("初始防御max", "def"), ("初始法抗max", "res")]:
        raw = kv.get(field, "").strip()
        if raw:
            try:
                stats[key] = int(raw)
            except ValueError:
                pass

    interval = kv.get("攻击间隔", "").strip()
    if interval:
        try:
            stats["attack_interval"] = float(interval)
        except ValueError:
            pass

    block = kv.get("阻挡数", "").strip()
    if block:
        try:
            stats["block"] = int(block)
        except ValueError:
            pass

    cost = kv.get("部署费用", "").strip()
    if cost:
        try:
            stats["deploy_cost"] = int(cost)
        except ValueError:
            pass

    return stats


def parse_potentials(kv: dict[str, str]) -> list[str]:
    potentials: list[str] = []
    for i in range(2, 7):
        desc = kv.get(f"潜能{i}", "").strip()
        if desc:
            potentials.append(desc)
    return potentials


def parse_modules(kv: dict[str, str]) -> list[dict[str, str]]:
    modules: list[dict[str, str]] = []
    base_name = kv.get("模组名", "").strip()
    if not base_name:
        return modules
    module: dict[str, str] = {"name": base_name}
    task1 = kv.get("模组解锁任务1", "").strip()
    if task1:
        module["unlock_task_1"] = task1
    task2 = kv.get("模组解锁任务2", "").strip()
    if task2:
        module["unlock_task_2"] = task2
    materials = kv.get("模组解锁材料", "").strip()
    if materials:
        module["unlock_materials"] = materials
    stat_changes = kv.get("基础数值变化", "").strip()
    if stat_changes:
        module["stat_changes"] = stat_changes
    trait_update = kv.get("分支特性更新", "").strip()
    if trait_update:
        module["trait_update"] = trait_update
    modules.append(module)
    return modules


def parse_operator(wikitext: str) -> dict[str, Any] | None:
    """从干员页 wikitext 中解析完整干员数据。"""
    kv = parse_template_kv(wikitext)
    if not kv:
        return None

    name = kv.get("干员代号", kv.get("英文名", "")).strip()
    if not name:
        return None

    rarity_str = kv.get("星级", "1")
    rarity = parse_rarity(rarity_str)

    operator: dict[str, Any] = {
        "名称": name,
        "_entity_type": "character",
        "星级": rarity,
    }

    prof = kv.get("职业", "").strip()
    if prof:
        operator["职业"] = prof
    branch = kv.get("分支", "").strip()
    if branch:
        operator["分支"] = branch
    tags = kv.get("标签", "").strip()
    if tags:
        operator["标签"] = tags
    trait = kv.get("特性", "").strip()
    if trait:
        operator["特性"] = trait

    base_stats = parse_base_stats(kv, rarity)
    if base_stats:
        operator["基础属性"] = base_stats
    trust = parse_trust_bonus(kv)
    if trust:
        operator["信赖加成"] = trust
    talents = parse_talents(kv)
    if talents:
        operator["天赋"] = talents
    skills = parse_skills(kv)
    if skills:
        operator["技能"] = skills

    potentials = parse_potentials(kv)
    if potentials:
        operator["潜能"] = potentials

    modules = parse_modules(kv)
    if modules:
        operator["模组"] = modules

    return operator
