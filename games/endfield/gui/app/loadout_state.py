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

from .confirm_refresh import (
    build_confirm_refresh_signature,
    build_display_pending_signature,
)
from .loadout_preset import LoadoutPreset


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
    break_defense_stacks: int = 0
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
            break_defense_stacks=self.break_defense_stacks,
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
                "break_defense_stacks": self.break_defense_stacks,
            },
        )
        """to loadout preset。"""

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
            is_true_damage=self.is_true_damage,
            combo_stacks=self.combo_stacks,
            attached_effect_multiplier=self.attached_effect_multiplier,
            corrosion_duration_seconds=self.corrosion_duration_seconds,
            break_defense_stacks=self.break_defense_stacks,
        )
        """to search job inputs。"""

    def to_compute_sheet_inputs(self) -> dict[str, Any]:
        """转换为 DAG context 键值对，供 ComputeSheet.set() 逐项设置。"""
        char = self.char_data
        weapon = self.weapon_data
        return {
            "character.基础攻击": char.get("攻击力", 0),
            "character.暴击率": char.get("基础暴击率", 0.05),
            "character.暴击伤害": char.get("基础暴伤", char.get("基础暴击伤害", 0.5)),
            "character.力量": char.get("力量", 0),
            "character.敏捷": char.get("敏捷", 0),
            "character.智识": char.get("智识", 0),
            "character.意志": char.get("意志", 0),
            "character.基础生命值": char.get("生命值", char.get("基础生命值", 0)),
            "character.基础防御力": char.get("防御力", char.get("基础防御力", 0)),
            "weapon.基础攻击": weapon.get("攻击力", 0),
            "weapon.攻击力+": weapon.get("攻击力+", 0),
            "weapon.附加攻击力+": weapon.get("附加攻击力+", 0),
            "weapon.精炼等级": weapon.get("精炼等级", 1),
            "weapon.法术伤害+": weapon.get("法术伤害+", 0),
            "weapon.攻击力+平值": weapon.get("攻击力+平值", 0),
            "weapon.最大生命值+": weapon.get("最大生命值+", 0),
            "enemy.防御": self.enemy_defense,
            "computed.技能倍率": self.skill_multiplier,
        }


# ── Re-exports from loadout_serialize (API 兼容) ──────────────────────────
from .loadout_serialize import (  # noqa: F401  # isort: skip  # re-exports
    _resolve_selected_skill_for_search,
    read_loadout_from_app,
    read_loadout_from_panels,
)
