#!/usr/bin/env python3
"""
武器技能选用状态：与配装预设 v2 同形，供 LoadoutState / 乘区 / 全量搜索共用。

legacy 12 元组仅作导入 adapter；新代码应优先使用本 module 的 interface。
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from character_weapon_equipment.weapon_data.special_fields import read_weapon_skills_schema


def normalize_weapon_specials_tuple(raw: tuple[Any, ...]) -> tuple[Any, ...]:
    """将旧版 10 元组迁移为 (技能/叠加)×2 + 三附加技能。"""
    from character_weapon_equipment.weapon_data.special_fields import (
        migrate_legacy_weapon_special_level,
    )

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


@dataclass(frozen=True)
class WeaponSkillSelection:
    """普通技能三槽 + 特殊技能两槽的选用状态。"""

    normal_skills: tuple[tuple[str, int], tuple[str, int], tuple[str, int]]
    special_skills: tuple[tuple[str, int, int], tuple[str, int, int]]

    @classmethod
    def from_legacy_tuple(cls, raw: tuple[Any, ...]) -> WeaponSkillSelection:
        t = normalize_weapon_specials_tuple(raw)
        return cls(
            normal_skills=(
                (str(t[0]), int(t[1])),
                (str(t[2]), int(t[3])),
                (str(t[4]), int(t[5])),
            ),
            special_skills=(
                (str(t[6]), int(t[7]), int(t[8])),
                (str(t[9]), int(t[10]), int(t[11])),
            ),
        )

    @classmethod
    def from_preset_view(
        cls,
        weapon_data: Mapping[str, Any],
        *,
        weapon_normal_levels: Sequence[int],
        weapon_special_states: Sequence[Mapping[str, int]],
    ) -> WeaponSkillSelection:
        """将预设 v2 紧凑字段映射回武器 schema 槽位（名称来自 JSON）。"""
        schema = read_weapon_skills_schema(dict(weapon_data))
        normal_defs = list(schema.get("normal_skills") or [])[:3]
        while len(normal_defs) < 3:
            normal_defs.append({})
        special_defs = list(schema.get("special_skills") or [])[:2]
        while len(special_defs) < 2:
            special_defs.append({})

        normal_iter = iter(int(v) for v in weapon_normal_levels)
        normal_slots: list[tuple[str, int]] = []
        for item in normal_defs:
            effect = str(item.get("effect", "")).strip()
            if effect:
                normal_slots.append((effect, next(normal_iter, 0)))
            else:
                normal_slots.append(("", 0))
        while len(normal_slots) < 3:
            normal_slots.append(("", 0))

        special_slots: list[tuple[str, int, int]] = []
        for idx, item in enumerate(special_defs):
            name = str(item.get("name", "")).strip()
            if name and idx < len(weapon_special_states):
                state = weapon_special_states[idx]
                special_slots.append(
                    (
                        name,
                        max(0, int(state.get("level", 0))),
                        max(0, int(state.get("stack", 0))),
                    )
                )
            else:
                special_slots.append(("", 0, 0))
        while len(special_slots) < 2:
            special_slots.append(("", 0, 0))

        return cls(
            normal_skills=(normal_slots[0], normal_slots[1], normal_slots[2]),
            special_skills=(special_slots[0], special_slots[1]),
        )

    def to_legacy_tuple(self) -> tuple[Any, ...]:
        """供 confirm_refresh 签名等仍使用元组的 call site。"""
        n1, n2, n3 = self.normal_skills
        s1, s2 = self.special_skills
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

    def to_preset_view(self) -> dict[str, Any]:
        """与 ``endfield_loadout_preset_v2`` 的 weapon_* 字段同形。"""
        normal_levels: list[int] = []
        for name, level in self.normal_skills:
            if str(name).strip() and int(level) > 0:
                normal_levels.append(int(level))
        special_states: list[dict[str, int]] = []
        for name, level, stack in self.special_skills:
            if str(name).strip() and int(level) > 0:
                special_states.append({"level": int(level), "stack": max(0, int(stack))})
        return {
            "weapon_normal_levels": normal_levels,
            "weapon_special_states": special_states,
        }

    def calculation_kwargs(self) -> dict[str, Any]:
        """乘区/GUI/搜索优先使用的 normal_skill_* / special_skill_* 参数。"""
        n1, n2, n3 = self.normal_skills
        s1, s2 = self.special_skills
        return {
            "normal_skill_1_name": n1[0],
            "normal_skill_1_level": n1[1],
            "normal_skill_2_name": n2[0],
            "normal_skill_2_level": n2[1],
            "normal_skill_3_name": n3[0],
            "normal_skill_3_level": n3[1],
            "special_skill_1_name": s1[0],
            "special_skill_1_level": s1[1],
            "special_skill_1_stack": s1[2],
            "special_skill_2_name": s2[0],
            "special_skill_2_level": s2[1],
            "special_skill_2_stack": s2[2],
        }

    def signature_token(self) -> str:
        """供 run_signature 等哈希用的稳定 token。"""
        preset = self.to_preset_view()
        normal = ",".join(str(v) for v in preset["weapon_normal_levels"])
        special = ",".join(f"{s['level']}:{s['stack']}" for s in preset["weapon_special_states"])
        return f"n[{normal}]|s[{special}]"
