# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""装备系统拆分结构测试（P2-07）。"""

from __future__ import annotations

from pathlib import Path

_MODULE_NAMES = (
    "games.endfield.calc.equipment.system",
    "games.endfield.calc.equipment.equipment_kinds",
    "games.endfield.calc.equipment.equipment_effects",
)


def _line_count(module_name: str) -> int:
    module = __import__(module_name, fromlist=["__file__"])
    return len(Path(module.__file__).read_text(encoding="utf-8").splitlines())


def test_equipment_modules_stay_within_target() -> None:
    for module_name in _MODULE_NAMES:
        assert _line_count(module_name) <= 400, module_name


def test_system_reexports_kind_and_effect_helpers() -> None:
    from games.endfield.calc.equipment import equipment_effects, equipment_kinds, system

    assert system.equipment_kind is equipment_kinds.equipment_kind
    assert system.infer_equipment_slot is equipment_kinds.infer_equipment_slot
    assert system._normalize_slot is equipment_kinds._normalize_slot
    assert system._parse_percent_value is equipment_effects._parse_percent_value
    assert system._parse_effect_text is equipment_effects._parse_effect_text
    assert system.EQUIPMENT_KIND_ARMOR is equipment_kinds.EQUIPMENT_KIND_ARMOR


def test_system_behavior_smoke() -> None:
    from games.endfield.calc.equipment.system import equipment_kind, infer_equipment_slot

    assert equipment_kind({"装备种类": "胸甲"}) == "护甲"
    assert infer_equipment_slot({"名称": "轻甲-测试"}) == "护甲"
