# SPDX-License-Identifier: AGPL-3.0
"""覆盖 zone_snapshot/types.py 数据类及其方法。"""

from __future__ import annotations

from games.endfield.calc.zone_snapshot.types import (
    MultiplicativeZoneSelection,
    WeaponBonusSelection,
    ZoneDisplayLine,
)


class TestWeaponBonusSelection:
    """WeaponBonusSelection 数据类方法。"""

    def test_defaults(self) -> None:
        sel = WeaponBonusSelection()
        assert sel.normal_skill_1_name == ""
        assert sel.normal_skill_1_level == 1
        assert sel.normal_skill_3_level == 0

    def test_legacy_kwargs_new_names(self) -> None:
        """使用新参数名时 legacy_kwargs 映射正确。"""
        sel = WeaponBonusSelection(
            normal_skill_1_name="攻击力+",
            normal_skill_1_level=3,
        )
        kwargs = sel.legacy_kwargs()
        assert kwargs["sa1_name"] == "攻击力+"
        assert kwargs["sa1_level"] == 3

    def test_legacy_kwargs_fallback(self) -> None:
        """仅使用旧参数名时 legacy_kwargs 直接返回。"""
        sel = WeaponBonusSelection(
            sa1_name="攻击力+",
            sa1_level=5,
        )
        kwargs = sel.legacy_kwargs()
        assert kwargs["sa1_name"] == "攻击力+"
        assert kwargs["sa1_level"] == 5

    def test_legacy_kwargs_new_overrides_old(self) -> None:
        """新旧同时存在时新参数优先。"""
        sel = WeaponBonusSelection(
            normal_skill_1_name="敏捷+",
            normal_skill_1_level=7,
            sa1_name="攻击力+",
            sa1_level=3,
        )
        kwargs = sel.legacy_kwargs()
        assert kwargs["sa1_name"] == "敏捷+"
        assert kwargs["sa1_level"] == 7

    def test_calculation_kwargs_new_names(self) -> None:
        sel = WeaponBonusSelection(
            normal_skill_1_name="攻击力+",
            normal_skill_1_level=3,
        )
        kwargs = sel.calculation_kwargs()
        assert kwargs["normal_skill_1_name"] == "攻击力+"
        assert kwargs["normal_skill_1_level"] == 3

    def test_calculation_kwargs_fallback(self) -> None:
        sel = WeaponBonusSelection(
            sa1_name="攻击力+",
            sa1_level=5,
        )
        kwargs = sel.calculation_kwargs()
        assert kwargs["normal_skill_1_name"] == "攻击力+"
        assert kwargs["normal_skill_1_level"] == 5

    def test_calculation_kwargs_new_overrides_old(self) -> None:
        sel = WeaponBonusSelection(
            normal_skill_1_name="敏捷+",
            normal_skill_1_level=7,
            sa1_name="攻击力+",
            sa1_level=3,
        )
        kwargs = sel.calculation_kwargs()
        assert kwargs["normal_skill_1_name"] == "敏捷+"
        assert kwargs["normal_skill_1_level"] == 7

    def test_from_calculation_kwargs(self) -> None:
        kwargs = {
            "normal_skill_1_name": "攻击力+",
            "normal_skill_1_level": 3,
            "normal_skill_2_name": "敏捷+",
            "normal_skill_2_level": 5,
            "special_skill_1_name": "ws_name",
            "special_skill_1_level": 2,
            "special_skill_1_stack": 1,
        }
        sel = WeaponBonusSelection.from_calculation_kwargs(kwargs)
        assert sel.normal_skill_1_name == "攻击力+"
        assert sel.normal_skill_1_level == 3
        assert sel.special_skill_1_name == "ws_name"
        assert sel.special_skill_1_stack == 1

    def test_from_calculation_kwargs_empty(self) -> None:
        sel = WeaponBonusSelection.from_calculation_kwargs({})
        assert sel.normal_skill_1_name == ""
        assert sel.normal_skill_1_level == 1
        assert sel.normal_skill_3_level == 0


class TestMultiplicativeZoneSelection:
    """MultiplicativeZoneSelection 数据类。"""

    def test_defaults(self) -> None:
        sel = MultiplicativeZoneSelection(
            character={"名称": "测试"},
            weapon=None,
            char_level=1,
            weapon_level=1,
        )
        assert sel.trust_level == 0
        assert isinstance(sel.bonuses, WeaponBonusSelection)
        assert sel.character["名称"] == "测试"

    def test_with_bonuses(self) -> None:
        bonuses = WeaponBonusSelection(normal_skill_1_name="攻击力+")
        sel = MultiplicativeZoneSelection(
            character={"名称": "测试"},
            weapon={"名称": "武器"},
            char_level=50,
            weapon_level=50,
            trust_level=4,
            bonuses=bonuses,
        )
        assert sel.char_level == 50
        assert sel.trust_level == 4
        assert sel.bonuses.normal_skill_1_name == "攻击力+"


class TestZoneDisplayLine:
    """ZoneDisplayLine 数据类。"""

    def test_default_color(self) -> None:
        line = ZoneDisplayLine(text="测试行")
        assert line.text == "测试行"
        assert line.color == "#B8B8B8"

    def test_custom_color(self) -> None:
        line = ZoneDisplayLine(text="高亮行", color="#FF0000")
        assert line.color == "#FF0000"
