#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""
乘区快照 DataClass：展示行、武器选用档位、已确认的选择。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class WeaponBonusSelection:
    """武器潜能 / 特殊能力在乘区中的选用档位。"""

    normal_skill_1_name: str = ""
    normal_skill_1_level: int = 1
    normal_skill_2_name: str = ""
    normal_skill_2_level: int = 1
    normal_skill_3_name: str = ""
    normal_skill_3_level: int = 0
    special_skill_1_name: str = ""
    special_skill_1_level: int = 1
    special_skill_1_stack: int = 0
    special_skill_2_name: str = ""
    special_skill_2_level: int = 1
    special_skill_2_stack: int = 0

    sa1_name: str = ""
    sa1_level: int = 1
    sa2_name: str = ""
    sa2_level: int = 1
    sa3_name: str = ""
    sa3_level: int = 0
    ws_name: str = ""
    ws_level: int = 1
    ws_stack: int = 0
    ws2_name: str = ""
    ws2_level: int = 1
    ws2_stack: int = 0

    def legacy_kwargs(self) -> dict[str, int | str]:
        """兼容旧计算函数参数名。"""
        sa1_name = self.normal_skill_1_name or self.sa1_name
        sa1_level = self.normal_skill_1_level if self.normal_skill_1_name else self.sa1_level
        sa2_name = self.normal_skill_2_name or self.sa2_name
        sa2_level = self.normal_skill_2_level if self.normal_skill_2_name else self.sa2_level
        sa3_name = self.normal_skill_3_name or self.sa3_name
        sa3_level = self.normal_skill_3_level if self.normal_skill_3_name else self.sa3_level
        ws_name = self.special_skill_1_name or self.ws_name
        ws_level = self.special_skill_1_level if self.special_skill_1_name else self.ws_level
        ws_stack = self.special_skill_1_stack if self.special_skill_1_name else self.ws_stack
        ws2_name = self.special_skill_2_name or self.ws2_name
        ws2_level = self.special_skill_2_level if self.special_skill_2_name else self.ws2_level
        ws2_stack = self.special_skill_2_stack if self.special_skill_2_name else self.ws2_stack
        return {
            "sa1_name": sa1_name,
            "sa1_level": sa1_level,
            "sa2_name": sa2_name,
            "sa2_level": sa2_level,
            "sa3_name": sa3_name,
            "sa3_level": sa3_level,
            "ws_name": ws_name,
            "ws_level": ws_level,
            "ws_stack": ws_stack,
            "ws2_name": ws2_name,
            "ws2_level": ws2_level,
            "ws2_stack": ws2_stack,
        }

    def calculation_kwargs(self) -> dict[str, int | str]:
        """统一输出给计算链的新参数名（兼容旧字段输入）。"""
        return {
            "normal_skill_1_name": self.normal_skill_1_name or self.sa1_name,
            "normal_skill_1_level": (self.normal_skill_1_level if self.normal_skill_1_name else self.sa1_level),
            "normal_skill_2_name": self.normal_skill_2_name or self.sa2_name,
            "normal_skill_2_level": (self.normal_skill_2_level if self.normal_skill_2_name else self.sa2_level),
            "normal_skill_3_name": self.normal_skill_3_name or self.sa3_name,
            "normal_skill_3_level": (self.normal_skill_3_level if self.normal_skill_3_name else self.sa3_level),
            "special_skill_1_name": self.special_skill_1_name or self.ws_name,
            "special_skill_1_level": (self.special_skill_1_level if self.special_skill_1_name else self.ws_level),
            "special_skill_1_stack": (self.special_skill_1_stack if self.special_skill_1_name else self.ws_stack),
            "special_skill_2_name": self.special_skill_2_name or self.ws2_name,
            "special_skill_2_level": (self.special_skill_2_level if self.special_skill_2_name else self.ws2_level),
            "special_skill_2_stack": (self.special_skill_2_stack if self.special_skill_2_name else self.ws2_stack),
        }

    @classmethod
    def from_calculation_kwargs(cls, kwargs: dict[str, Any]) -> WeaponBonusSelection:
        """由 ``WeaponSkillSelection.calculation_kwargs()`` 等构建。"""
        return cls(
            normal_skill_1_name=str(kwargs.get("normal_skill_1_name", "")),
            normal_skill_1_level=int(kwargs.get("normal_skill_1_level", 1)),
            normal_skill_2_name=str(kwargs.get("normal_skill_2_name", "")),
            normal_skill_2_level=int(kwargs.get("normal_skill_2_level", 1)),
            normal_skill_3_name=str(kwargs.get("normal_skill_3_name", "")),
            normal_skill_3_level=int(kwargs.get("normal_skill_3_level", 0)),
            special_skill_1_name=str(kwargs.get("special_skill_1_name", "")),
            special_skill_1_level=int(kwargs.get("special_skill_1_level", 1)),
            special_skill_1_stack=int(kwargs.get("special_skill_1_stack", 0)),
            special_skill_2_name=str(kwargs.get("special_skill_2_name", "")),
            special_skill_2_level=int(kwargs.get("special_skill_2_level", 1)),
            special_skill_2_stack=int(kwargs.get("special_skill_2_stack", 0)),
        )


@dataclass(frozen=True)
class MultiplicativeZoneSelection:
    """已确认的角色、武器与等级选择。"""

    character: dict[str, Any]
    weapon: dict[str, Any] | None
    char_level: int
    weapon_level: int
    trust_level: int = 0
    bonuses: WeaponBonusSelection = WeaponBonusSelection()


@dataclass(frozen=True)
class ZoneDisplayLine:
    """右侧乘区一行展示。"""

    text: str
    color: str = "#B8B8B8"
