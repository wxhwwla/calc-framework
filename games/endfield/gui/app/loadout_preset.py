#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""配装预设 JSON 导入/导出（与 GUI 状态解耦，便于单测）。"""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

from games.endfield.calc.skills.special_fields import (
    migrate_legacy_weapon_special_level,
)
from games.endfield.data_loading.enemy_params import default_enemy_params

PRESET_SCHEMA = "endfield_loadout_preset_v2"


def _parse_enemy_params(raw: Any) -> dict[str, Any]:
    if not isinstance(raw, dict):
        return {}
    allowed = {
        "enemy_id",
        "enemy_defense",
        "enemy_resistance",
        "ignore_resistance",
        "imbalance_vulnerability_coeff",
        "is_unbalanced",
        "is_true_damage",
        "enemy_tier",
        "combo_stacks",
        "attached_effect_multiplier",
        "corrosion_duration_seconds",
        "imbalance_efficiency_bonus",
        "break_defense_stacks",
    }
    result: dict[str, Any] = {}
    for key in allowed:
        if key in raw:
            result[key] = raw[key]
    return result


def _parse_manual_buffs(raw: Any) -> dict[str, list[dict[str, str | float]]]:
    if not isinstance(raw, dict):
        return {}
    result: dict[str, list[dict[str, str | float]]] = {}
    for key, entries in raw.items():
        if not isinstance(entries, list):
            continue
        parsed: list[dict[str, str | float]] = []
        for e in entries:
            if not isinstance(e, dict):
                continue
            parsed.append(
                {
                    "effect_type": str(e.get("effect_type", "")),
                    "value": float(e.get("value", 0.0)),
                }
            )
        if parsed:
            result[str(key)] = parsed
    return result


LEGACY_PRESET_SCHEMA = "endfield_loadout_preset_v1"
BATCH_PRESET_SCHEMA = "endfield_loadout_preset_batch_v1"


@dataclass(frozen=True)
class LoadoutPreset:
    """可分享的配装与计算参数快照（仅存名称，便于跨机器）。

    ``ui_state`` 可选，用于恢复 GUI 折叠与页签（见 ``enhancement_controls.apply_preset_to_app``）：
    ``char_advanced_expanded``、``weapon_advanced_expanded``、``more_settings_expanded``、``current_page``。
    """

    char_name: str
    weapon_name: str
    char_level: int
    weapon_level: int
    trust_level: int
    skill_levels: tuple[int, int, int]
    calculation_mode: str
    weapon_scope: str
    equipment_scope: str
    fixed_equipment_names: dict[str, str | None]
    multi_skill_counts: dict[str, int]
    use_manual_multi_skill_counts: bool
    weapon_normal_levels: list[int] = field(default_factory=list)
    weapon_special_states: list[dict[str, int]] = field(default_factory=list)
    physical_abnormal_counts: dict[str, int] = field(default_factory=dict)
    spell_abnormal_counts: dict[str, int] = field(default_factory=dict)
    damage_component_mode: str = "skill_and_abnormal"
    use_expected_crit: bool = False
    include_conditional_equipment_crit: bool = False
    extra_crit_rate: float = 0.0
    extra_crit_damage: float = 0.0
    manual_buffs: dict[str, list[dict[str, str | float]]] = field(default_factory=dict)
    enemy_params: dict[str, Any] = field(default_factory=dict)
    ui_state: dict[str, Any] | None = None
    note: str = ""

    def merged_enemy_params(self) -> dict[str, Any]:
        """与默认敌参合并后的完整字典（供面板 set_params）。"""
        merged = dict(default_enemy_params())
        merged.update(self.enemy_params or {})
        return merged

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": PRESET_SCHEMA,
            "char_name": self.char_name,
            "weapon_name": self.weapon_name,
            "char_level": self.char_level,
            "weapon_level": self.weapon_level,
            "trust_level": self.trust_level,
            "skill_levels": list(self.skill_levels),
            "calculation_mode": self.calculation_mode,
            "weapon_scope": self.weapon_scope,
            "equipment_scope": self.equipment_scope,
            "fixed_equipment_names": dict(self.fixed_equipment_names),
            "multi_skill_counts": dict(self.multi_skill_counts),
            "use_manual_multi_skill_counts": self.use_manual_multi_skill_counts,
            "weapon_normal_levels": [int(v) for v in self.weapon_normal_levels],
            "weapon_special_states": [
                {"level": int(s.get("level", 1)), "stack": max(0, int(s.get("stack", 0)))}
                for s in self.weapon_special_states
            ],
            "physical_abnormal_counts": dict(self.physical_abnormal_counts),
            "spell_abnormal_counts": dict(self.spell_abnormal_counts),
            "damage_component_mode": self.damage_component_mode,
            "use_expected_crit": self.use_expected_crit,
            "include_conditional_equipment_crit": self.include_conditional_equipment_crit,
            "extra_crit_rate": float(self.extra_crit_rate),
            "extra_crit_damage": float(self.extra_crit_damage),
            "manual_buffs": {k: [dict(e) for e in v] for k, v in self.manual_buffs.items()},
            "enemy_params": dict(self.enemy_params or {}),
            "ui_state": dict(self.ui_state or {}),
            "note": self.note,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> LoadoutPreset:
        schema = str(data.get("schema", ""))
        if schema not in {PRESET_SCHEMA, LEGACY_PRESET_SCHEMA}:
            raise ValueError(f"不支持的预设格式: {data.get('schema')}")
        fixed = data.get("fixed_equipment_names") or {}
        counts = data.get("multi_skill_counts") or {}
        abnormal_counts = data.get("physical_abnormal_counts") or {}
        spell_abnormal_counts = data.get("spell_abnormal_counts") or {}
        weapon_normal_levels = data.get("weapon_normal_levels") or []
        weapon_special_states = data.get("weapon_special_states") or []
        parsed_counts: dict[str, int] = {}
        for key, value in counts.items():
            parsed_counts[str(key)] = max(0, int(value))
        parsed_abnormal_counts: dict[str, int] = {}
        for key, value in abnormal_counts.items():
            parsed_abnormal_counts[str(key)] = max(0, int(value))
        parsed_spell_abnormal_counts: dict[str, int] = {}
        for key, value in spell_abnormal_counts.items():
            parsed_spell_abnormal_counts[str(key)] = max(0, int(value))
        if not any(":" in k for k in parsed_counts):
            parsed_counts.setdefault("战技", int(counts.get("战技", 0)))
            parsed_counts.setdefault("连携技", int(counts.get("连携技", 0)))
            parsed_counts.setdefault("终结技", int(counts.get("终结技", 0)))
        parsed_normal_levels = [max(0, int(v)) for v in weapon_normal_levels]
        if not parsed_normal_levels:
            legacy_normal_levels = [
                int(data.get("special_ability_1_level", 0) or 0),
                int(data.get("special_ability_2_level", 0) or 0),
                int(data.get("special_ability_3_level", 0) or 0),
            ]
            parsed_normal_levels = [v for v in legacy_normal_levels if v > 0]
        parsed_special_states: list[dict[str, int]] = []
        for item in weapon_special_states:
            if not isinstance(item, dict):
                continue
            parsed_special_states.append(
                {
                    "level": max(1, int(item.get("level", 1))),
                    "stack": max(0, int(item.get("stack", 0))),
                }
            )
        if not parsed_special_states:
            ws_level, ws_stack = migrate_legacy_weapon_special_level(
                int(data.get("ws_level", 0) or 0),
                ws_stack=(int(data["ws_stack"]) if "ws_stack" in data and data.get("ws_stack") is not None else None),
            )
            if int(data.get("ws_level", 0) or 0) > 0 or ("ws_stack" in data and int(data.get("ws_stack", 0) or 0) > 0):
                parsed_special_states.append({"level": ws_level, "stack": ws_stack})
            ws2_level, ws2_stack = migrate_legacy_weapon_special_level(
                int(data.get("ws2_level", 0) or 0),
                ws_stack=(
                    int(data["ws2_stack"]) if "ws2_stack" in data and data.get("ws2_stack") is not None else None
                ),
            )
            if int(data.get("ws2_level", 0) or 0) > 0 or (
                "ws2_stack" in data and int(data.get("ws2_stack", 0) or 0) > 0
            ):
                parsed_special_states.append({"level": ws2_level, "stack": ws2_stack})
        levels = data.get("skill_levels") or [0, 0, 0]
        return cls(
            char_name=str(data.get("char_name", "")),
            weapon_name=str(data.get("weapon_name", "")),
            char_level=int(data.get("char_level", 1)),
            weapon_level=int(data.get("weapon_level", 1)),
            trust_level=int(data.get("trust_level", 0)),
            skill_levels=(
                int(levels[0]),
                int(levels[1]) if len(levels) > 1 else 0,
                int(levels[2]) if len(levels) > 2 else 0,
            ),
            calculation_mode=str(data.get("calculation_mode", "zone_snapshot")),
            weapon_scope=str(data.get("weapon_scope", "当前武器")),
            equipment_scope=str(data.get("equipment_scope", "全部装备")),
            fixed_equipment_names={
                "chest": fixed.get("chest"),
                "gloves": fixed.get("gloves"),
                "accessory_a": fixed.get("accessory_a"),
                "accessory_b": fixed.get("accessory_b"),
            },
            multi_skill_counts=parsed_counts,
            use_manual_multi_skill_counts=bool(data.get("use_manual_multi_skill_counts", False)),
            weapon_normal_levels=parsed_normal_levels,
            weapon_special_states=parsed_special_states,
            physical_abnormal_counts=parsed_abnormal_counts,
            spell_abnormal_counts=parsed_spell_abnormal_counts,
            damage_component_mode=str(data.get("damage_component_mode", "skill_and_abnormal")),
            use_expected_crit=bool(data.get("use_expected_crit", False)),
            include_conditional_equipment_crit=bool(data.get("include_conditional_equipment_crit", False)),
            extra_crit_rate=float(data.get("extra_crit_rate", 0.0) or 0.0),
            extra_crit_damage=float(data.get("extra_crit_damage", 0.0) or 0.0),
            manual_buffs=_parse_manual_buffs(data.get("manual_buffs")),
            enemy_params=_parse_enemy_params(data.get("enemy_params")),
            ui_state={
                "char_advanced_expanded": bool((data.get("ui_state") or {}).get("char_advanced_expanded", True)),
                "weapon_advanced_expanded": bool((data.get("ui_state") or {}).get("weapon_advanced_expanded", True)),
                "more_settings_expanded": bool((data.get("ui_state") or {}).get("more_settings_expanded", False)),
                "current_page": str((data.get("ui_state") or {}).get("current_page", "计算页")),
            },
            note=str(data.get("note", "")),
        )


def export_preset_json(preset: LoadoutPreset, *, indent: int = 2) -> str:
    return json.dumps(preset.to_dict(), ensure_ascii=False, indent=indent)


def import_preset_json(text: str) -> LoadoutPreset:
    data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError("预设必须是 JSON 对象")
    return LoadoutPreset.from_dict(data)


def import_presets_from_json_text(text: str) -> list[LoadoutPreset]:
    """解析单条预设或批量预设 JSON。"""
    data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError("预设必须是 JSON 对象")
    if data.get("schema") == BATCH_PRESET_SCHEMA:
        raw_list = data.get("presets") or []
        if not isinstance(raw_list, list) or not raw_list:
            raise ValueError("批量预设缺少 presets 数组")
        return [LoadoutPreset.from_dict(item) for item in raw_list]
    return [LoadoutPreset.from_dict(data)]


def export_preset_batch_json(presets: Sequence[LoadoutPreset], *, indent: int = 2) -> str:
    payload = {
        "schema": BATCH_PRESET_SCHEMA,
        "presets": [p.to_dict() for p in presets],
    }
    return json.dumps(payload, ensure_ascii=False, indent=indent)


_DAMAGE_COMPONENT_LABELS: dict[str, str] = {
    "skill_only": "仅技能",
    "abnormal_only": "仅异常",
    "skill_and_abnormal": "技能+异常",
}


def apply_preset_to_panels(
    *,
    preset: LoadoutPreset,
    char_panel: Any,
    weapon_panel: Any,
    control_dock: Any,
    equipment_catalog: dict[str, list[dict[str, Any]]],
    shell: Any | None = None,
) -> None:
    """将 LoadoutPreset 写入 Qt 角色/武器/控制栏面板（导入预设与历史恢复共用）。"""
    from gui.shared.calc_mode_labels import calculation_mode_label

    if preset.char_name:
        char_panel.select_by_name(preset.char_name)
    if preset.weapon_name:
        weapon_panel.select_by_name(preset.weapon_name)

    char_panel.level_slider.setValue(int(preset.char_level))
    weapon_panel.level_slider.setValue(int(preset.weapon_level))
    if char_panel.trust_panel:
        char_panel.trust_panel.set_level(min(int(preset.trust_level), 4))
    if char_panel.skill_panel:
        s1, s2, s3 = preset.skill_levels
        char_panel.skill_panel.apply_levels(int(s1), int(s2), int(s3))
    if weapon_panel.special_panel:
        weapon_panel.special_panel.apply_weapon_skill_state(
            normal_levels=list(preset.weapon_normal_levels),
            special_states=list(preset.weapon_special_states),
        )

    mode_label = calculation_mode_label(preset.calculation_mode)
    idx = control_dock.calc_mode_menu.findText(mode_label)
    if idx >= 0:
        control_dock.calc_mode_menu.setCurrentIndex(idx)

    scope_idx = control_dock.single_skill_scope_combo.findText(preset.weapon_scope)
    if scope_idx >= 0:
        control_dock.single_skill_scope_combo.setCurrentIndex(scope_idx)
    equip_idx = control_dock.equipment_scope_combo.findText(preset.equipment_scope)
    if equip_idx >= 0:
        control_dock.equipment_scope_combo.setCurrentIndex(equip_idx)

    control_dock.populate_fixed_loadout_slots(equipment_catalog)
    fixed = preset.fixed_equipment_names
    slot_keys = ("chest", "gloves", "accessory_a", "accessory_b")
    for i, slot_key in enumerate(slot_keys):
        name = fixed.get(slot_key)
        cb = control_dock.fixed_loadout_slots[i]
        if name:
            cb.setCurrentText(str(name))
        else:
            from gui.shell.qt_control_dock_builders import _FIXED_SLOT_NONE_LABEL

            cb.setCurrentText(_FIXED_SLOT_NONE_LABEL)

    control_dock.use_manual_skill_counts_cb.setChecked(bool(preset.use_manual_multi_skill_counts))
    dc_label = _DAMAGE_COMPONENT_LABELS.get(preset.damage_component_mode, "技能+异常")
    dc_idx = control_dock.damage_component_combo.findText(dc_label)
    if dc_idx >= 0:
        control_dock.damage_component_combo.setCurrentIndex(dc_idx)
    control_dock.use_expected_crit_cb.setChecked(bool(preset.use_expected_crit))
    control_dock.include_conditional_crit_cb.setChecked(bool(preset.include_conditional_equipment_crit))
    control_dock.extra_crit_rate_edit.setText(str(float(preset.extra_crit_rate)))
    control_dock.extra_crit_damage_edit.setText(str(float(preset.extra_crit_damage)))

    char_data = char_panel.get_selected_data()
    if char_data and char_panel.skill_panel:
        s1 = char_panel.get_skill_1_level()
        s2 = char_panel.get_skill_2_level()
        s3 = char_panel.get_skill_3_level()
        control_dock.rebuild_segment_rows(char_data, s1, s2, s3)
        edits = getattr(control_dock, "_segment_count_edits_dict", None) or {}
        for key, count in preset.multi_skill_counts.items():
            if key in edits:
                edits[key].setText(str(max(0, int(count))))

    enemy_panel = getattr(control_dock, "_enemy_panel", None)
    if enemy_panel is not None and hasattr(enemy_panel, "set_params"):
        enemy_panel.set_params(preset.merged_enemy_params())

    from games.endfield.calc.manual_buff.abnormal_matrix import apply_abnormal_matrix_counts

    apply_abnormal_matrix_counts(
        control_dock._physical_abnormal_edits,
        getattr(control_dock, "_physical_abnormal_specs", ()),
        preset.physical_abnormal_counts,
    )
    apply_abnormal_matrix_counts(
        control_dock._spell_abnormal_edits,
        getattr(control_dock, "_spell_abnormal_specs", ()),
        preset.spell_abnormal_counts,
    )

    if shell is not None and preset.manual_buffs:
        shell._manual_buff_store = {k: [dict(e) for e in v] for k, v in preset.manual_buffs.items()}
