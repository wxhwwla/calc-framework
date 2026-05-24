#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""配装预设 JSON 导入/导出（与 GUI 状态解耦，便于单测）。"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Optional, Sequence

PRESET_SCHEMA = "endfield_loadout_preset_v1"
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
    fixed_equipment_names: dict[str, Optional[str]]
    multi_skill_counts: dict[str, int]
    use_manual_multi_skill_counts: bool
    ui_state: dict[str, Any] | None = None
    note: str = ""

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
            "ui_state": dict(self.ui_state or {}),
            "note": self.note,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LoadoutPreset":
        if data.get("schema") != PRESET_SCHEMA:
            raise ValueError(f"不支持的预设格式: {data.get('schema')}")
        fixed = data.get("fixed_equipment_names") or {}
        counts = data.get("multi_skill_counts") or {}
        parsed_counts: dict[str, int] = {}
        for key, value in counts.items():
            parsed_counts[str(key)] = max(0, int(value))
        if not any(":" in k for k in parsed_counts):
            parsed_counts.setdefault("战技", int(counts.get("战技", 0)))
            parsed_counts.setdefault("连携技", int(counts.get("连携技", 0)))
            parsed_counts.setdefault("终结技", int(counts.get("终结技", 0)))
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
            use_manual_multi_skill_counts=bool(
                data.get("use_manual_multi_skill_counts", False)
            ),
            ui_state={
                "char_advanced_expanded": bool(
                    (data.get("ui_state") or {}).get("char_advanced_expanded", False)
                ),
                "weapon_advanced_expanded": bool(
                    (data.get("ui_state") or {}).get("weapon_advanced_expanded", False)
                ),
                "more_settings_expanded": bool(
                    (data.get("ui_state") or {}).get("more_settings_expanded", False)
                ),
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
