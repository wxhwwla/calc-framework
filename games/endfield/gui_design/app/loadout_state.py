#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""
当前配装快照：从选择面板读取一次，供确认签名、预设、全量搜索共用。

减少 gui / enhancement_controls 多处刮取 panel 的重复与漂移。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from games.endfield.calc.loadout.slot_search import FixedLoadoutSelection
from games.endfield.calc.search.plan.controller import SearchJobInputs
from games.endfield.calc.skills.weapon_selection import WeaponSkillSelection
from gui_design.presentation.display_lines import resolve_selected_skill_for_damage

from .confirm_refresh import (
    build_confirm_refresh_signature,
    build_display_pending_signature,
)
from .loadout_preset import LoadoutPreset


def _resolve_selected_skill_for_search(
    char_data: dict[str, Any],
    *,
    skill_1_level: int,
    skill_2_level: int,
    skill_3_level: int,
) -> tuple[str, str, float, str]:
    """与 ``resolve_selected_skill_for_damage`` 一致，供全量搜索使用。"""
    skill = resolve_selected_skill_for_damage(
        char_data,
        skill_1_level=skill_1_level,
        skill_2_level=skill_2_level,
        skill_3_level=skill_3_level,
    )
    return skill.label, skill.skill_type, skill.multiplier, skill.damage_type


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
    damage_type: str
    calculation_mode: str
    weapon_scope_label: str
    equipment_scope_label: str
    fixed_loadout: FixedLoadoutSelection
    fixed_equipment_names: dict[str, str | None]
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
    enemy_resistance: float = 0.0
    ignore_resistance: float = 0.0
    imbalance_vulnerability_coeff: float = 1.3
    is_unbalanced: bool = False
    is_true_damage: bool = False
    enemy_tier: str = "普通"
    combo_stacks: int = 0
    attached_effect_multiplier: float = 1.0
    corrosion_duration_seconds: float = 15.0
    imbalance_efficiency_bonus: float = 0.0
    weapon_specials: tuple[Any, ...] = ("", 1, "", 1, "", 0, "", 1, 0, "", 1, 0)
    manual_buffs: dict[str, list[dict[str, str | float]]] = field(default_factory=dict)

    def weapon_skills(self) -> WeaponSkillSelection:
        """当前武器技能选用状态（深 module 视图）。"""
        return WeaponSkillSelection.from_legacy_tuple(self.weapon_specials)

    def weapon_skill_kwargs(self) -> dict[str, Any]:
        """武器技能参数（新命名：普通技能 / 特殊技能）。"""
        return self.weapon_skills().calculation_kwargs()

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
        return self.weapon_skills().to_preset_view()

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

    def display_pending_signature(self) -> tuple:
        """供「待确认」检测：仅含影响三列/快照的配装字段。"""
        return build_display_pending_signature(
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
            damage_component_mode=self.damage_component_mode,
            use_expected_crit=self.use_expected_crit,
            include_conditional_equipment_crit=self.include_conditional_equipment_crit,
            extra_crit_rate=self.extra_crit_rate,
            extra_crit_damage=self.extra_crit_damage,
            physical_abnormal_counts=self.physical_abnormal_counts,
            spell_abnormal_counts=self.spell_abnormal_counts,
            enemy_defense=self.enemy_defense,
            enemy_resistance=self.enemy_resistance,
            ignore_resistance=self.ignore_resistance,
            imbalance_vulnerability_coeff=self.imbalance_vulnerability_coeff,
            is_unbalanced=self.is_unbalanced,
            is_true_damage=self.is_true_damage,
            enemy_tier=self.enemy_tier,
            combo_stacks=self.combo_stacks,
            attached_effect_multiplier=self.attached_effect_multiplier,
            corrosion_duration_seconds=self.corrosion_duration_seconds,
            imbalance_efficiency_bonus=self.imbalance_efficiency_bonus,
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
            manual_buffs=dict(self.manual_buffs),
            enemy_params={
                "enemy_defense": self.enemy_defense,
                "enemy_resistance": self.enemy_resistance,
                "ignore_resistance": self.ignore_resistance,
                "imbalance_vulnerability_coeff": self.imbalance_vulnerability_coeff,
                "is_unbalanced": self.is_unbalanced,
                "is_true_damage": self.is_true_damage,
                "enemy_tier": self.enemy_tier,
                "combo_stacks": self.combo_stacks,
                "attached_effect_multiplier": self.attached_effect_multiplier,
                "corrosion_duration_seconds": self.corrosion_duration_seconds,
                "imbalance_efficiency_bonus": self.imbalance_efficiency_bonus,
            },
        )

    def to_search_job_inputs(
        self,
        *,
        all_weapons: list[dict[str, Any]],
        equipment_catalog: dict[str, list[dict[str, Any]]],
    ) -> SearchJobInputs:
        preset_skills = self.weapon_skills().to_preset_view()
        return SearchJobInputs(
            char_data=self.char_data,
            char_level=self.char_level,
            weapon_level=self.weapon_level,
            trust_level=self.trust_level,
            skill_name=self.skill_name,
            skill_type=self.skill_type,
            skill_multiplier=self.skill_multiplier,
            damage_type=self.damage_type,
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
            weapon_normal_levels=preset_skills["weapon_normal_levels"],
            weapon_special_states=preset_skills["weapon_special_states"],
            enemy_resistance=self.enemy_resistance,
            ignore_resistance=self.ignore_resistance,
            imbalance_vulnerability_coeff=self.imbalance_vulnerability_coeff,
            is_unbalanced=self.is_unbalanced,
            combo_stacks=self.combo_stacks,
            attached_effect_multiplier=self.attached_effect_multiplier,
            corrosion_duration_seconds=self.corrosion_duration_seconds,
        )


def _fixed_equipment_names(fixed: FixedLoadoutSelection) -> dict[str, str | None]:
    def _name(item: dict | None) -> str | None:
        if not item:
            return None
        return str(item.get("名称") or "") or None

    return {
        "chest": _name(fixed.chest),
        "gloves": _name(fixed.gloves),
        "accessory_a": _name(fixed.accessory_a),
        "accessory_b": _name(fixed.accessory_b),
    }


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
    enemy_resistance: float = 0.0,
    ignore_resistance: float = 0.0,
    imbalance_vulnerability_coeff: float = 1.3,
    is_unbalanced: bool = False,
    is_true_damage: bool = False,
    enemy_tier: str = "普通",
    combo_stacks: int = 0,
    attached_effect_multiplier: float = 1.0,
    corrosion_duration_seconds: float = 15.0,
    imbalance_efficiency_bonus: float = 0.0,
    manual_buffs: dict[str, list[dict[str, str | float]]] | None = None,
) -> LoadoutState | None:
    """从角色/武器面板读取配装快照；无效选择时返回 None。"""
    char_data = char_panel.get_selected_data()
    weapon_data = weapon_panel.get_selected_data()
    if not char_data or not weapon_data:
        return None

    skill_name, skill_type, skill_multiplier, damage_type = _resolve_selected_skill_for_search(
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
        damage_type=damage_type,
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
        enemy_resistance=float(enemy_resistance),
        ignore_resistance=float(ignore_resistance),
        imbalance_vulnerability_coeff=float(imbalance_vulnerability_coeff),
        is_unbalanced=bool(is_unbalanced),
        is_true_damage=bool(is_true_damage),
        enemy_tier=str(enemy_tier),
        combo_stacks=max(0, min(4, int(combo_stacks))),
        attached_effect_multiplier=float(attached_effect_multiplier),
        corrosion_duration_seconds=float(corrosion_duration_seconds),
        imbalance_efficiency_bonus=float(imbalance_efficiency_bonus),
        weapon_specials=_read_weapon_specials_from_panel(weapon_panel),
        manual_buffs=dict(manual_buffs or {}),
    )


def _read_weapon_specials_from_panel(panel: Any) -> tuple[Any, ...]:
    """从选择面板读取武器技能选择并序列化为旧版 12 元组。"""
    return WeaponSkillSelection.from_legacy_tuple(
        (
            str(getattr(panel, "get_normal_skill_1_name", lambda: "")() or ""),
            int(getattr(panel, "get_normal_skill_1_level", lambda: 0)() or 0),
            str(getattr(panel, "get_normal_skill_2_name", lambda: "")() or ""),
            int(getattr(panel, "get_normal_skill_2_level", lambda: 0)() or 0),
            str(getattr(panel, "get_normal_skill_3_name", lambda: "")() or ""),
            int(getattr(panel, "get_normal_skill_3_level", lambda: 0)() or 0),
            str(getattr(panel, "get_special_skill_1_name", lambda: "")() or ""),
            int(getattr(panel, "get_special_skill_1_level", lambda: 1)() or 1),
            int(getattr(panel, "get_special_skill_1_stack", lambda: 0)() or 0),
            str(getattr(panel, "get_special_skill_2_name", lambda: "")() or ""),
            int(getattr(panel, "get_special_skill_2_level", lambda: 1)() or 1),
            int(getattr(panel, "get_special_skill_2_stack", lambda: 0)() or 0),
        )
    ).to_legacy_tuple()


def read_loadout_from_app(app: Any, *, ensure_segment_rows: bool = True) -> LoadoutState | None:
    """从 DamageCalculatorApp 实例读取配装快照。"""
    char_panel = getattr(app, "char_panel", None)
    weapon_panel = getattr(app, "weapon_panel", None)
    if char_panel is None or weapon_panel is None:
        return None
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
            app._manual_physical_abnormal_counts() if hasattr(app, "_manual_physical_abnormal_counts") else {}
        ),
        spell_abnormal_counts=(
            app._manual_spell_abnormal_counts() if hasattr(app, "_manual_spell_abnormal_counts") else {}
        ),
        damage_component_mode=(
            app._current_damage_component_mode()
            if hasattr(app, "_current_damage_component_mode")
            else "skill_and_abnormal"
        ),
        use_expected_crit=bool(getattr(getattr(app, "use_expected_crit_var", None), "get", lambda: False)()),
        include_conditional_equipment_crit=bool(
            getattr(
                getattr(app, "include_conditional_equipment_crit_var", None),
                "get",
                lambda: False,
            )()
        ),
        extra_crit_rate=float(app._extra_crit_rate() if hasattr(app, "_extra_crit_rate") else 0.0),
        extra_crit_damage=float(app._extra_crit_damage() if hasattr(app, "_extra_crit_damage") else 0.0),
        enemy_defense=float(getattr(app, "_enemy_defense", 100.0)),
        enemy_resistance=float(getattr(app, "_enemy_resistance", 0.0)),
        ignore_resistance=float(getattr(app, "_ignore_resistance", 0.0)),
        imbalance_vulnerability_coeff=float(getattr(app, "_imbalance_vulnerability_coeff", 1.3)),
        is_unbalanced=bool(getattr(app, "_is_unbalanced", False)),
        is_true_damage=bool(getattr(app, "_is_true_damage", False)),
        enemy_tier=str(getattr(app, "_enemy_tier", "普通")),
        combo_stacks=int(getattr(app, "_combo_stacks", 0)),
        attached_effect_multiplier=float(getattr(app, "_attached_effect_multiplier", 1.0)),
        corrosion_duration_seconds=float(getattr(app, "_corrosion_duration_seconds", 15.0)),
        imbalance_efficiency_bonus=float(getattr(app, "_imbalance_efficiency_bonus", 0.0)),
        manual_buffs=getattr(app, "_manual_buff_store", None),
    )
