"""ComputeSheet 接入终末地 GUI — 集成测试。

验证 build_endfield_sheet 能正确加载 DAG + EndfieldContextLoader + layout.json，
求值结果与现有引擎一致。
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
_PKG_ROOT = _REPO_ROOT / "endfield_damage_calculator"
_CHARS = _PKG_ROOT / "character_weapon_equipment" / "character_data" / "characters.json"
_WEAPONS = _PKG_ROOT / "character_weapon_equipment" / "weapon_data" / "weapons.json"


def _load_by_name(path: Path, name: str) -> dict:
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    for item in data:
        if item.get("名称") == name:
            return item
    raise KeyError(name)


@pytest.fixture(scope="module")
def qapp():
    import sys

    from PySide6.QtWidgets import QApplication

    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


class TestEndfieldSheetIntegration:
    def test_builds_widget(self, qapp):
        from gui_design.shared.display_view.endfield_sheet import build_endfield_sheet

        char = _load_by_name(_CHARS, "秋栗")
        weapon = _load_by_name(_WEAPONS, "逐鳞3.0")
        sheet = build_endfield_sheet(char, weapon, char_level=80, weapon_level=80, trust_level=0)

        w = sheet.widget
        assert w is not None

    def test_evaluates_attack_chain(self, qapp):
        from calculation.multiplicative_zones.final_attack_zone import (
            calculate_final_attack_with_details,
        )
        from gui_design.shared.display_view.endfield_sheet import build_endfield_sheet

        char = _load_by_name(_CHARS, "秋栗")
        weapon = _load_by_name(_WEAPONS, "逐鳞3.0")
        existing = calculate_final_attack_with_details(
            char, weapon, char_level=80, weapon_level=80, trust_level=0,
        )

        sheet = build_endfield_sheet(char, weapon, char_level=80, weapon_level=80, trust_level=0)
        result = sheet.evaluate()

        dag_final = result.outputs.get("最终攻击力", 0.0)
        assert dag_final == pytest.approx(existing["final_attack"], rel=1e-9), (
            f"ComputeSheet 最终攻击力: {dag_final}, 现有引擎: {existing['final_attack']}"
        )

    def test_evaluates_full_damage_chain(self, qapp):
        from gui_design.shared.display_view.endfield_sheet import build_endfield_sheet

        char = _load_by_name(_CHARS, "秋栗")
        weapon = _load_by_name(_WEAPONS, "逐鳞3.0")

        sheet = build_endfield_sheet(char, weapon, char_level=80, weapon_level=80, trust_level=0)
        result1 = sheet.evaluate()

        final_atk = result1.outputs["最终攻击力"]
        assert final_atk > 0

        sheet._base_context["computed"]["最终攻击力"] = final_atk
        sheet._base_context["computed"]["技能倍率"] = 1.5
        result2 = sheet.evaluate()

        assert result2.outputs.get("最终伤害", 0.0) > 0
