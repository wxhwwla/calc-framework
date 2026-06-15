# SPDX-License-Identifier: AGPL-3.0
"""Web 请求体 → LoadoutState（与桌面 GUI 共用预览/快照接缝）。"""

from __future__ import annotations

from typing import Any

from games.endfield.calc.loadout.slot_search import FixedLoadoutSelection
from games.endfield.calc.skills.weapon_selection import WeaponSkillSelection
from games.endfield.data_loading.enemy_params import ENEMY_PARAM_FIELDS, default_enemy_params
from games.endfield.gui.app.loadout_state import LoadoutState, _resolve_selected_skill_for_search


def _parse_manual_buffs(raw: Any) -> dict[str, list[dict[str, str | float]]]:
    if not isinstance(raw, dict):
        return {}
    out: dict[str, list[dict[str, str | float]]] = {}
    for key, entries in raw.items():
        if not isinstance(entries, list):
            continue
        parsed: list[dict[str, str | float]] = []
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            parsed.append(
                {
                    "effect_type": str(entry.get("effect_type", "")),
                    "value": float(entry.get("value", 0.0)),
                }
            )
        if parsed:
            out[str(key)] = parsed
    """parse manual buffs。"""
    return out


def _weapon_selection_from_web(
    weapon_data: dict[str, Any],
    weapon_skill_values: dict[str, Any] | None,
) -> WeaponSkillSelection:
    wsv = weapon_skill_values or {}
    normal_levels: list[int] = []
    for idx in range(1, 4):
        normal_levels.append(max(0, int(wsv.get(f"normal_skill_{idx}_level", 0))))
    special_states: list[dict[str, int]] = []
    for idx in range(1, 3):
        level = max(0, int(wsv.get(f"special_skill_{idx}_level", 0)))
        if level > 0:
            special_states.append(
                {
                    "level": level,
                    "stack": max(0, int(wsv.get(f"special_skill_{idx}_stack", 0))),
                }
            )
    return WeaponSkillSelection.from_preset_view(
        weapon_data,
        weapon_normal_levels=normal_levels,
        weapon_special_states=special_states,
    )
    """weapon selection from web。"""


def _legacy_weapon_specials(selection: WeaponSkillSelection) -> tuple[Any, ...]:
    n1, n2, n3 = selection.normal_skills
    s1, s2 = selection.special_skills
    return (
        n1[0],
        n1[1],
        n2[0],
        n2[1],
        n3[0],
        n3[1],
        s1[0],
        s1[1],
        s1[2],
        s2[0],
        s2[1],
        s2[2],
    )
    """legacy weapon specials。"""


def _enemy_fields(body: dict[str, Any]) -> dict[str, Any]:
    enemy = dict(default_enemy_params())
    nested = body.get("enemy_params")
    if isinstance(nested, dict):
        enemy.update({k: nested[k] for k in nested if k in enemy or k in nested})
    for key in ENEMY_PARAM_FIELDS:
        if key in body:
            enemy[key] = body[key]
    """enemy fields。"""
    return enemy


def _find_equipment_row(
    name: str | None,
    catalog_key: str,
    catalog: dict[str, list[dict[str, Any]]],
) -> dict | None:
    """按名称在 catalog 中查找装备行（与 GUI read_fixed_loadout_selection 一致）。"""
    if not name:
        return None
    for row in catalog.get(catalog_key) or []:
        if str(row.get("名称") or "") == str(name):
            return row
    return None


def resolve_fixed_loadout_selection(
    *,
    fixed_equipment_names: dict[str, Any] | None,
    equipment_catalog: dict[str, list[dict[str, Any]]],
    fixed_loadout_raw: dict[str, Any] | None = None,
) -> FixedLoadoutSelection:
    """Web 固定配装名 → ``FixedLoadoutSelection``（dict 行，供搜索/预览共用）。"""
    names: dict[str, Any] = dict(fixed_equipment_names or {})
    raw = fixed_loadout_raw if isinstance(fixed_loadout_raw, dict) else {}

    def _slot_value(slot_key: str, catalog_key: str) -> dict | None:
        if names.get(slot_key):
            return _find_equipment_row(str(names[slot_key]), catalog_key, equipment_catalog)
        item = raw.get(slot_key)
        if isinstance(item, dict):
            return item
        if isinstance(item, str) and item:
            return _find_equipment_row(item, catalog_key, equipment_catalog)
        """slot value。"""
        return None

    return FixedLoadoutSelection(
        chest=_slot_value("chest", "chest"),
        gloves=_slot_value("gloves", "gloves"),
        accessory_a=_slot_value("accessory_a", "accessories"),
        accessory_b=_slot_value("accessory_b", "accessories"),
    )


def _calculation_mode_from_body(body: dict[str, Any]) -> str:
    """Web 计算模式 → LoadoutState.calculation_mode。"""
    explicit = str(body.get("calculation_mode") or body.get("calc_mode") or "").strip()
    if explicit in ("single_skill_search", "multi_skill_search"):
        return explicit
    if bool(body.get("use_manual_multi_skill_counts", False)):
        return "multi_skill_search"
    return "single_skill_search"


def weapon_preset_from_web_values(
    weapon_skill_values: dict[str, Any] | None,
) -> tuple[list[int], list[dict[str, int]]]:
    """weapon_skill_values → weapon_normal_levels / weapon_special_states。"""
    wsv = weapon_skill_values or {}
    normal = [max(0, int(wsv.get(f"normal_skill_{i}_level", 0))) for i in range(1, 4)]
    special: list[dict[str, int]] = []
    for i in range(1, 3):
        level = max(0, int(wsv.get(f"special_skill_{i}_level", 0)))
        if level > 0:
            special.append(
                {
                    "level": level,
                    "stack": max(0, int(wsv.get(f"special_skill_{i}_stack", 0))),
                }
            )
    return normal, special


def resolve_search_skill_fields(
    char_data: dict[str, Any],
    *,
    skill_1_level: int,
    skill_2_level: int,
    skill_3_level: int,
) -> tuple[str, str, float, str]:
    """与 GUI ``_resolve_selected_skill_for_search`` 相同语义。"""
    return _resolve_selected_skill_for_search(
        char_data,
        skill_1_level=skill_1_level,
        skill_2_level=skill_2_level,
        skill_3_level=skill_3_level,
    )


def build_loadout_state_from_web(
    *,
    char_data: dict[str, Any],
    weapon_data: dict[str, Any],
    body: dict[str, Any],
) -> LoadoutState:
    """将 Web JSON 转为 ``LoadoutState``。"""
    raw_levels = body.get("skill_levels")
    if isinstance(raw_levels, list) and len(raw_levels) >= 3:
        skill_levels = (int(raw_levels[0]), int(raw_levels[1]), int(raw_levels[2]))
    else:
        skill_levels = (
            int(body.get("skill_1_level", 8)),
            int(body.get("skill_2_level", 8)),
            int(body.get("skill_3_level", 8)),
        )
    skill_name, skill_type, skill_multiplier, damage_type = _resolve_selected_skill_for_search(
        char_data,
        skill_1_level=skill_levels[0],
        skill_2_level=skill_levels[1],
        skill_3_level=skill_levels[2],
    )
    enemy = _enemy_fields(body)
    catalog = body.get("equipment_catalog") if isinstance(body.get("equipment_catalog"), dict) else {}
    fixed_names = body.get("fixed_equipment_names") or {}
    if not isinstance(fixed_names, dict):
        fixed_names = {}
    fixed_loadout = resolve_fixed_loadout_selection(
        fixed_equipment_names=fixed_names,
        equipment_catalog=catalog,  # type: ignore[arg-type]
        fixed_loadout_raw=body.get("fixed_loadout") if isinstance(body.get("fixed_loadout"), dict) else None,
    )
    use_manual = bool(body.get("use_manual_multi_skill_counts", False))
    calculation_mode = _calculation_mode_from_body(body)
    weapon_sel = _weapon_selection_from_web(weapon_data, body.get("weapon_skill_values"))

    return LoadoutState(
        char_data=char_data,
        weapon_data=weapon_data,
        char_level=int(body.get("char_level", 90)),
        weapon_level=int(body.get("weapon_level", 90)),
        trust_level=int(body.get("trust_level", 0)),
        skill_levels=skill_levels,
        skill_name=skill_name,
        skill_type=skill_type,
        skill_multiplier=skill_multiplier,
        damage_type=damage_type,
        calculation_mode=calculation_mode,
        weapon_scope_label=str(body.get("weapon_scope_label", "当前武器")),
        equipment_scope_label=str(body.get("equipment_scope_label", "全部装备")),
        fixed_loadout=fixed_loadout,
        fixed_equipment_names={
            "chest": fixed_names.get("chest"),
            "gloves": fixed_names.get("gloves"),
            "accessory_a": fixed_names.get("accessory_a"),
            "accessory_b": fixed_names.get("accessory_b"),
        },
        use_manual_multi_skill_counts=use_manual,
        manual_counts=dict(body.get("manual_counts") or {}),
        physical_abnormal_counts=dict(body.get("physical_abnormal_counts") or {}),
        spell_abnormal_counts=dict(body.get("spell_abnormal_counts") or {}),
        damage_component_mode=str(body.get("damage_component_mode", "skill_and_abnormal")),
        use_expected_crit=bool(body.get("use_expected_crit", False)),
        include_conditional_equipment_crit=bool(body.get("include_conditional_equipment_crit", False)),
        extra_crit_rate=float(body.get("extra_crit_rate", 0.0)),
        extra_crit_damage=float(body.get("extra_crit_damage", 0.0)),
        enemy_defense=float(enemy["enemy_defense"]),
        enemy_resistance=float(enemy["enemy_resistance"]),
        ignore_resistance=float(enemy["ignore_resistance"]),
        imbalance_vulnerability_coeff=float(enemy["imbalance_vulnerability_coeff"]),
        is_unbalanced=bool(enemy["is_unbalanced"]),
        is_true_damage=bool(enemy["is_true_damage"]),
        enemy_tier=str(enemy.get("enemy_tier", "普通")),
        combo_stacks=max(0, min(4, int(enemy.get("combo_stacks", 0)))),
        attached_effect_multiplier=float(enemy["attached_effect_multiplier"]),
        corrosion_duration_seconds=float(enemy["corrosion_duration_seconds"]),
        imbalance_efficiency_bonus=float(enemy.get("imbalance_efficiency_bonus", 0.0)),
        break_defense_stacks=max(0, min(4, int(enemy.get("break_defense_stacks", 0)))),
        weapon_specials=_legacy_weapon_specials(weapon_sel),
        manual_buffs=_parse_manual_buffs(body.get("manual_buffs")),
    )


def build_adapter_context_from_loadout(
    loadout: Any,
    *,
    layout_calc_mode: str = "zone_snapshot",
    equipment_catalog: dict[str, list[dict[str, Any]]] | None = None,
) -> dict[str, Any]:
    """LoadoutState → DAG adapter context（ComputeSheet 求值）。"""
    from games.endfield.calc.dag_adapter.adapter import build_dag_context
    from games.endfield.data_loading.web_context_enrich import (
        enrich_adapter_context,
        resolve_equipment_modifiers,
    )

    bonuses = dict(loadout.weapon_skill_kwargs())
    equip_effects, flat_stats, atk_percent = resolve_equipment_modifiers(
        fixed_equipment_names=getattr(loadout, "fixed_equipment_names", None),
        equipment_catalog=equipment_catalog,
    )
    ctx = build_dag_context(
        loadout.char_data,
        loadout.weapon_data,
        char_level=loadout.char_level,
        weapon_level=loadout.weapon_level,
        trust_level=loadout.trust_level,
        bonuses_kwargs=bonuses,
        equipment_stat_bonus=flat_stats or None,
        equipment_attack_percent=atk_percent,
    )
    enrich_adapter_context(ctx, loadout, equip_effects=equip_effects, flat_stats=flat_stats)
    s1, s2, s3 = loadout.skill_levels
    ui = ctx.setdefault("user_input", {})
    ui["skill_1_level"] = s1
    ui["skill_2_level"] = s2
    ui["skill_3_level"] = s3
    ui["calc_mode"] = layout_calc_mode
    ui["敌人防御"] = float(loadout.enemy_defense)
    ui["敌人抗性"] = float(loadout.enemy_resistance)
    ui["无视抗性"] = float(loadout.ignore_resistance)
    ui["失衡易伤系数"] = float(loadout.imbalance_vulnerability_coeff)
    ui["是否失衡"] = bool(loadout.is_unbalanced)
    ui["是否真实伤害"] = bool(loadout.is_true_damage)
    ui["连击层数"] = int(loadout.combo_stacks)
    ui["破防层数"] = int(loadout.break_defense_stacks)
    ui["附带效果倍率"] = float(loadout.attached_effect_multiplier)
    ui["腐蚀计时(秒)"] = float(loadout.corrosion_duration_seconds)
    ctx.setdefault("enemy", {})["防御"] = float(loadout.enemy_defense)
    return ctx


def loadout_state_to_web_preset(state: LoadoutState) -> dict[str, Any]:
    """导出为桌面 ``endfield_loadout_preset_v2`` 兼容 JSON。"""
    preset_view = state.weapon_skill_selection()
    return {
        "schema": "endfield_loadout_preset_v2",
        "char_name": str(state.char_data.get("名称", "")),
        "weapon_name": str(state.weapon_data.get("名称", "")),
        "char_level": state.char_level,
        "weapon_level": state.weapon_level,
        "trust_level": state.trust_level,
        "skill_levels": list(state.skill_levels),
        "calculation_mode": state.calculation_mode,
        "weapon_scope": state.weapon_scope_label,
        "equipment_scope": state.equipment_scope_label,
        "fixed_equipment_names": dict(state.fixed_equipment_names),
        "multi_skill_counts": dict(state.manual_counts),
        "use_manual_multi_skill_counts": state.use_manual_multi_skill_counts,
        "weapon_normal_levels": preset_view["weapon_normal_levels"],
        "weapon_special_states": preset_view["weapon_special_states"],
        "physical_abnormal_counts": dict(state.physical_abnormal_counts),
        "spell_abnormal_counts": dict(state.spell_abnormal_counts),
        "damage_component_mode": state.damage_component_mode,
        "use_expected_crit": state.use_expected_crit,
        "include_conditional_equipment_crit": state.include_conditional_equipment_crit,
        "extra_crit_rate": state.extra_crit_rate,
        "extra_crit_damage": state.extra_crit_damage,
        "manual_buffs": {k: [dict(e) for e in v] for k, v in state.manual_buffs.items()},
        "enemy_params": {
            "enemy_defense": state.enemy_defense,
            "enemy_resistance": state.enemy_resistance,
            "ignore_resistance": state.ignore_resistance,
            "imbalance_vulnerability_coeff": state.imbalance_vulnerability_coeff,
            "is_unbalanced": state.is_unbalanced,
            "is_true_damage": state.is_true_damage,
            "enemy_tier": state.enemy_tier,
            "combo_stacks": state.combo_stacks,
            "attached_effect_multiplier": state.attached_effect_multiplier,
            "corrosion_duration_seconds": state.corrosion_duration_seconds,
            "imbalance_efficiency_bonus": state.imbalance_efficiency_bonus,
            "break_defense_stacks": state.break_defense_stacks,
        },
    }
