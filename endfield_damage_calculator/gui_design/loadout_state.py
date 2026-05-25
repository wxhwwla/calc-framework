#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
当前配装快照：从选择面板读取一次，供确认签名、预设、全量搜索共用。

减少 gui / enhancement_controls 多处刮取 panel 的重复与漂移。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from character_weapon_equipment.weapon_data.special_fields import migrate_legacy_weapon_special_level
from calculation.loadout_slot_search import FixedLoadoutSelection
from calculation.search_controller import SearchJobInputs
from gui_design.confirm_refresh import build_confirm_refresh_signature
from gui_design.loadout_preset import LoadoutPreset


def _resolve_selected_skill_for_search(
    char_data: dict[str, Any],
    *,
    skill_1_level: int,
    skill_2_level: int,
    skill_3_level: int,
) -> tuple[str, str, float]:
    """与 ``DamageCalculatorApp._resolve_selected_skill`` 一致，供全量搜索使用。"""
    options = (
        ("战技", "战技倍率", skill_1_level),
        ("连携技", "连携技倍率", skill_2_level),
        ("终结技", "终结技倍率", skill_3_level),
    )
    for skill_name, field, level in options:
        if level <= 0:
            continue
        segments = char_data.get(field) or []
        if not isinstance(segments, list) or not segments:
            continue
        first_segment = segments[0] if isinstance(segments[0], list) else []
        index = max(0, min(level - 1, len(first_segment) - 1))
        if isinstance(first_segment, list) and first_segment:
            value = float(first_segment[index] or 0.0)
            return skill_name, skill_name, value / 100.0
    return "战技", "战技", 1.0


@dataclass(frozen=True)
class LoadoutState:
    """角色+武器+范围+固定配装+次数+敌人防御的统一快照。"""

    char_data: dict[str, Any]
    weapon_data: dict[str, Any]
    char_level: int
    weapon_level: int
    trust_level: int
    skill_levels: tuple[int, int, int]
    skill_name: str
    skill_type: str
    skill_multiplier: float
    calculation_mode: str
    weapon_scope_label: str
    equipment_scope_label: str
    fixed_loadout: FixedLoadoutSelection
    fixed_equipment_names: dict[str, Optional[str]]
    use_manual_multi_skill_counts: bool
    manual_counts: dict[str, int]
    physical_abnormal_counts: dict[str, int] = field(default_factory=dict)
    spell_abnormal_counts: dict[str, int] = field(default_factory=dict)
    damage_component_mode: str = "skill_and_abnormal"
    use_expected_crit: bool = False
    include_conditional_equipment_crit: bool = False
    extra_crit_rate: float = 0.0
    extra_crit_damage: float = 0.0
    enemy_defense: float = 100.0
    weapon_specials: tuple[Any, ...] = ("", 1, "", 1, "", 0, "", 1, 0, "", 1, 0)

    def weapon_skill_kwargs(self) -> dict[str, Any]:
        """武器技能参数（新命名：普通技能 / 特殊技能）。"""
        t = normalize_weapon_specials_tuple(self.weapon_specials)
        return {
            "normal_skill_1_name": t[0],
            "normal_skill_1_level": int(t[1]),
            "normal_skill_2_name": t[2],
            "normal_skill_2_level": int(t[3]),
            "normal_skill_3_name": t[4],
            "normal_skill_3_level": int(t[5]),
            "special_skill_1_name": t[6],
            "special_skill_1_level": int(t[7]),
            "special_skill_1_stack": int(t[8]),
            "special_skill_2_name": t[9],
            "special_skill_2_level": int(t[10]),
            "special_skill_2_stack": int(t[11]),
        }

    def weapon_special_kwargs(self) -> dict[str, Any]:
        """兼容旧命名字段，供既有调用方继续使用。"""
        new = self.weapon_skill_kwargs()
        return {
            "sa1_name": new["normal_skill_1_name"],
            "sa1_level": new["normal_skill_1_level"],
            "sa2_name": new["normal_skill_2_name"],
            "sa2_level": new["normal_skill_2_level"],
            "sa3_name": new["normal_skill_3_name"],
            "sa3_level": new["normal_skill_3_level"],
            "ws_name": new["special_skill_1_name"],
            "ws_level": new["special_skill_1_level"],
            "ws_stack": new["special_skill_1_stack"],
            "ws2_name": new["special_skill_2_name"],
            "ws2_level": new["special_skill_2_level"],
            "ws2_stack": new["special_skill_2_stack"],
        }

    def weapon_skill_selection(self) -> dict[str, Any]:
        """
        武器技能选择（新 schema 视图）。

        返回：
        - ``weapon_normal_levels``: 按顺序启用的普通技能等级列表
        - ``weapon_special_states``: 启用的特殊技能状态列表（level/stack）
        """
        t = normalize_weapon_specials_tuple(self.weapon_specials)
        normal_levels: list[int] = []
        for name, level in ((t[0], t[1]), (t[2], t[3]), (t[4], t[5])):
            if str(name).strip() and int(level) > 0:
                normal_levels.append(int(level))
        special_states: list[dict[str, int]] = []
        for name, level, stack in ((t[6], t[7], t[8]), (t[9], t[10], t[11])):
            if str(name).strip() and int(level) > 0:
                special_states.append(
                    {"level": int(level), "stack": max(0, int(stack))}
                )
        return {
            "weapon_normal_levels": normal_levels,
            "weapon_special_states": special_states,
        }

    def effective_skill_counts(self) -> dict[str, int]:
        """未开手动次数时仅战技计 1 次（与仪表盘一致）。"""
        if self.use_manual_multi_skill_counts:
            return dict(self.manual_counts)
        return {"战技": 1, "连携技": 0, "终结技": 0}

    def confirm_refresh_signature(self) -> tuple:
        """供 confirm_refresh 去重使用的可哈希签名。"""
        return build_confirm_refresh_signature(
            calculation_mode=self.calculation_mode,
            char_name=str(self.char_data.get("名称", "")),
            char_level=self.char_level,
            weapon_name=str(self.weapon_data.get("名称", "")),
            weapon_level=self.weapon_level,
            trust_level=self.trust_level,
            skill_levels=self.skill_levels,
            weapon_specials=self.weapon_specials,
            use_manual_multi_skill_counts=self.use_manual_multi_skill_counts,
            multi_skill_manual_counts=self.manual_counts,
            preview_scope_label=self.weapon_scope_label,
            preview_equipment_scope_label=self.equipment_scope_label,
            fixed_loadout_token=self.fixed_loadout.signature_token(),
            damage_component_mode=self.damage_component_mode,
            use_expected_crit=self.use_expected_crit,
            include_conditional_equipment_crit=self.include_conditional_equipment_crit,
            extra_crit_rate=self.extra_crit_rate,
            extra_crit_damage=self.extra_crit_damage,
            physical_abnormal_counts=self.physical_abnormal_counts,
            spell_abnormal_counts=self.spell_abnormal_counts,
        )

    def to_loadout_preset(self) -> LoadoutPreset:
        return LoadoutPreset(
            char_name=str(self.char_data.get("名称", "")),
            weapon_name=str(self.weapon_data.get("名称", "")),
            char_level=self.char_level,
            weapon_level=self.weapon_level,
            trust_level=self.trust_level,
            skill_levels=self.skill_levels,
            calculation_mode=self.calculation_mode,
            weapon_scope=self.weapon_scope_label,
            equipment_scope=self.equipment_scope_label,
            fixed_equipment_names=dict(self.fixed_equipment_names),
            multi_skill_counts=dict(self.manual_counts),
            use_manual_multi_skill_counts=self.use_manual_multi_skill_counts,
            weapon_normal_levels=self.weapon_skill_selection()["weapon_normal_levels"],
            weapon_special_states=self.weapon_skill_selection()["weapon_special_states"],
            physical_abnormal_counts=dict(self.physical_abnormal_counts),
            spell_abnormal_counts=dict(self.spell_abnormal_counts),
            damage_component_mode=self.damage_component_mode,
            use_expected_crit=self.use_expected_crit,
            include_conditional_equipment_crit=self.include_conditional_equipment_crit,
            extra_crit_rate=self.extra_crit_rate,
            extra_crit_damage=self.extra_crit_damage,
        )

    def to_search_job_inputs(
        self,
        *,
        all_weapons: list[dict[str, Any]],
        equipment_catalog: dict[str, list[dict[str, Any]]],
    ) -> SearchJobInputs:
        return SearchJobInputs(
            char_data=self.char_data,
            char_level=self.char_level,
            weapon_level=self.weapon_level,
            trust_level=self.trust_level,
            skill_name=self.skill_name,
            skill_type=self.skill_type,
            skill_multiplier=self.skill_multiplier,
            weapon_scope_label=self.weapon_scope_label,
            equipment_scope_label=self.equipment_scope_label,
            all_weapons=all_weapons,
            current_weapon=self.weapon_data,
            equipment_catalog=equipment_catalog,
            fixed_loadout=self.fixed_loadout,
            enemy_defense=self.enemy_defense,
            use_manual_multi_skill_counts=self.use_manual_multi_skill_counts,
            skill_1_level=self.skill_levels[0],
            skill_2_level=self.skill_levels[1],
            skill_3_level=self.skill_levels[2],
            manual_counts=dict(self.manual_counts),
            physical_abnormal_counts=dict(self.physical_abnormal_counts),
            spell_abnormal_counts=dict(self.spell_abnormal_counts),
            damage_component_mode=self.damage_component_mode,
            use_expected_crit=self.use_expected_crit,
            include_conditional_equipment_crit=self.include_conditional_equipment_crit,
            extra_crit_rate=self.extra_crit_rate,
            extra_crit_damage=self.extra_crit_damage,
        )


def _fixed_equipment_names(fixed: FixedLoadoutSelection) -> dict[str, Optional[str]]:
    def _name(item: Optional[dict]) -> Optional[str]:
        if not item:
            return None
        return str(item.get("名称") or "") or None

    return {
        "chest": _name(fixed.chest),
        "gloves": _name(fixed.gloves),
        "accessory_a": _name(fixed.accessory_a),
        "accessory_b": _name(fixed.accessory_b),
    }


def normalize_weapon_specials_tuple(raw: tuple[Any, ...]) -> tuple[Any, ...]:
    """将旧版 10 元组迁移为 (技能/叠加)×2 + 三附加技能。"""
    if len(raw) >= 12:
        return tuple(raw[:12])
    if len(raw) == 10:
        ws_level, ws_stack = migrate_legacy_weapon_special_level(int(raw[7]))
        ws2_level, ws2_stack = migrate_legacy_weapon_special_level(int(raw[9]))
        return (
            raw[0],
            raw[1],
            raw[2],
            raw[3],
            raw[4],
            raw[5],
            raw[6],
            ws_level,
            ws_stack,
            raw[8],
            ws2_level,
            ws2_stack,
        )
    raise ValueError(f"weapon_specials 长度无效: {len(raw)}")


def _weapon_specials_tuple(weapon_panel: Any) -> tuple[Any, ...]:
    def _call(name: str, fallback: str) -> Any:
        getter = getattr(weapon_panel, name, None)
        if callable(getter):
            return getter()
        return getattr(weapon_panel, fallback)()

    return (
        _call("get_normal_skill_1_name", "get_special_ability_1_name"),
        _call("get_normal_skill_1_level", "get_special_ability_1_level"),
        _call("get_normal_skill_2_name", "get_special_ability_2_name"),
        _call("get_normal_skill_2_level", "get_special_ability_2_level"),
        _call("get_normal_skill_3_name", "get_special_ability_3_name"),
        _call("get_normal_skill_3_level", "get_special_ability_3_level"),
        _call("get_special_skill_1_name", "get_weapon_special_name"),
        _call("get_special_skill_1_level", "get_weapon_special_level"),
        _call("get_special_skill_1_stack", "get_weapon_special_stack"),
        _call("get_special_skill_2_name", "get_weapon_special_2_name"),
        _call("get_special_skill_2_level", "get_weapon_special_2_level"),
        _call("get_special_skill_2_stack", "get_weapon_special_2_stack"),
    )


def read_loadout_from_panels(
    char_panel: Any,
    weapon_panel: Any,
    *,
    calculation_mode: str,
    weapon_scope_label: str,
    equipment_scope_label: str,
    fixed_loadout: FixedLoadoutSelection,
    use_manual_multi_skill_counts: bool,
    manual_counts: dict[str, int],
    physical_abnormal_counts: dict[str, int] | None = None,
    spell_abnormal_counts: dict[str, int] | None = None,
    damage_component_mode: str = "skill_and_abnormal",
    use_expected_crit: bool = False,
    include_conditional_equipment_crit: bool = False,
    extra_crit_rate: float = 0.0,
    extra_crit_damage: float = 0.0,
    enemy_defense: float,
) -> Optional[LoadoutState]:
    """从角色/武器面板读取配装快照；无效选择时返回 None。"""
    char_data = char_panel.get_selected_data()
    weapon_data = weapon_panel.get_selected_data()
    if not char_data or not weapon_data:
        return None

    skill_name, skill_type, skill_multiplier = _resolve_selected_skill_for_search(
        char_data,
        skill_1_level=int(char_panel.get_skill_1_level()),
        skill_2_level=int(char_panel.get_skill_2_level()),
        skill_3_level=int(char_panel.get_skill_3_level()),
    )

    return LoadoutState(
        char_data=char_data,
        weapon_data=weapon_data,
        char_level=int(char_panel.get_level()),
        weapon_level=int(weapon_panel.get_level()),
        trust_level=int(char_panel.get_trust_level()),
        skill_levels=(
            int(char_panel.get_skill_1_level()),
            int(char_panel.get_skill_2_level()),
            int(char_panel.get_skill_3_level()),
        ),
        skill_name=skill_name,
        skill_type=skill_type,
        skill_multiplier=float(skill_multiplier),
        calculation_mode=calculation_mode,
        weapon_scope_label=weapon_scope_label,
        equipment_scope_label=equipment_scope_label,
        fixed_loadout=fixed_loadout,
        fixed_equipment_names=_fixed_equipment_names(fixed_loadout),
        use_manual_multi_skill_counts=use_manual_multi_skill_counts,
        manual_counts=dict(manual_counts),
        physical_abnormal_counts=dict(physical_abnormal_counts or {}),
        spell_abnormal_counts=dict(spell_abnormal_counts or {}),
        damage_component_mode=str(damage_component_mode),
        use_expected_crit=bool(use_expected_crit),
        include_conditional_equipment_crit=bool(include_conditional_equipment_crit),
        extra_crit_rate=float(extra_crit_rate),
        extra_crit_damage=float(extra_crit_damage),
        enemy_defense=float(enemy_defense),
        weapon_specials=_weapon_specials_tuple(weapon_panel),
    )


def read_loadout_from_app(app: Any, *, ensure_segment_rows: bool = True) -> Optional[LoadoutState]:
    """从 DamageCalculatorApp 实例读取配装快照。"""
    char_panel = getattr(app, "char_panel", None)
    weapon_panel = getattr(app, "weapon_panel", None)
    if char_panel is None or weapon_panel is None:
        return None
    if ensure_segment_rows:
        from gui_design.multi_skill_controls import ensure_multi_skill_segment_rows

        ensure_multi_skill_segment_rows(app)
    fixed = app._build_fixed_loadout_selection()
    return read_loadout_from_panels(
        char_panel,
        weapon_panel,
        calculation_mode=app._current_calculation_mode(),
        weapon_scope_label=str(app.single_skill_scope_var.get()),
        equipment_scope_label=str(app.single_skill_equipment_scope_var.get()),
        fixed_loadout=fixed,
        use_manual_multi_skill_counts=bool(app.use_manual_skill_counts_var.get()),
        manual_counts=app._manual_multi_skill_counts(),
        physical_abnormal_counts=(
            app._manual_physical_abnormal_counts()
            if hasattr(app, "_manual_physical_abnormal_counts")
            else {}
        ),
        spell_abnormal_counts=(
            app._manual_spell_abnormal_counts()
            if hasattr(app, "_manual_spell_abnormal_counts")
            else {}
        ),
        damage_component_mode=(
            app._current_damage_component_mode()
            if hasattr(app, "_current_damage_component_mode")
            else "skill_and_abnormal"
        ),
        use_expected_crit=bool(
            getattr(getattr(app, "use_expected_crit_var", None), "get", lambda: False)()
        ),
        include_conditional_equipment_crit=bool(
            getattr(
                getattr(app, "include_conditional_equipment_crit_var", None),
                "get",
                lambda: False,
            )()
        ),
        extra_crit_rate=float(app._extra_crit_rate() if hasattr(app, "_extra_crit_rate") else 0.0),
        extra_crit_damage=float(
            app._extra_crit_damage() if hasattr(app, "_extra_crit_damage") else 0.0
        ),
        enemy_defense=float(getattr(app, "_enemy_defense", 100.0)),
    )
