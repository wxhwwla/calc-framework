# SPDX-License-Identifier: AGPL-3.0
from __future__ import annotations

from unittest.mock import MagicMock

from games.endfield.gui.app.loadout_preset import LoadoutPreset
from games.endfield.gui.shared.preset_batch_compare import (
    _empty_equipment,
    _find_by_name,
    _preset_label,
    _resolve_equipment,
)


class TestFindByName:

    def test_finds_matching(self) -> None:

        rows = [{"名称": "角色A"}, {"名称": "角色B"}]

        result = _find_by_name(rows, "角色A")

        assert result == {"名称": "角色A"}



    def test_returns_none_on_no_match(self) -> None:

        rows = [{"名称": "角色A"}]

        result = _find_by_name(rows, "角色C")

        assert result is None



    def test_empty_name(self) -> None:

        rows = [{"名称": "角色A"}]

        result = _find_by_name(rows, "")

        assert result is None



    def test_whitespace_name(self) -> None:

        rows = [{"名称": "角色A"}]

        result = _find_by_name(rows, "  ")

        assert result is None



    def test_empty_rows(self) -> None:

        result = _find_by_name([], "角色A")

        assert result is None



    def test_strip_target(self) -> None:

        rows = [{"名称": "角色A"}]

        result = _find_by_name(rows, "  角色A  ")

        assert result == {"名称": "角色A"}





class TestEmptyEquipment:

    def test_returns_correct_slot(self) -> None:

        eq = _empty_equipment(slot_kind="护甲")

        assert eq["名称"] == "（空）"

        assert eq["装备种类"] == "护甲"

        assert eq["部位"] == "护甲"



    def test_empty_effect_lists(self) -> None:

        eq = _empty_equipment(slot_kind="配件")

        assert eq["效果"] == []

        assert eq["三件套效果"] == []

        assert eq["属性词条"] == []





class TestResolveEquipment:

    def test_with_valid_name(self) -> None:

        equipments = [{"名称": "甲", "装备种类": "护甲", "部位": "护甲", "效果": [], "三件套效果": [], "属性词条": []}]

        result = _resolve_equipment("甲", equipments, slot_kind="护甲")

        assert result["名称"] == "甲"



    def test_with_none(self) -> None:

        result = _resolve_equipment(None, [], slot_kind="护甲")

        assert result["名称"] == "（空）"



    def test_with_empty_string(self) -> None:

        result = _resolve_equipment("", [], slot_kind="配件")

        assert result["名称"] == "（空）"



    def test_raises_on_not_found(self) -> None:

        import pytest

        equipments = [{"名称": "甲", "装备种类": "护甲", "部位": "护甲", "效果": [], "三件套效果": [], "属性词条": []}]

        with pytest.raises(ValueError, match="未找到装备"):

            _resolve_equipment("不存在", equipments, slot_kind="护甲")





class TestPresetLabel:

    def test_without_note(self) -> None:

        preset = MagicMock(spec=LoadoutPreset)

        preset.char_name = "角色A"

        preset.weapon_name = "武器B"

        preset.note = ""

        label = _preset_label(preset)

        assert label == "角色A / 武器B"



    def test_with_note(self) -> None:

        preset = MagicMock(spec=LoadoutPreset)

        preset.char_name = "角色A"

        preset.weapon_name = "武器B"

        preset.note = "测试配置"

        label = _preset_label(preset)

        assert "测试配置" in label

        assert "角色A" in label



    def test_whitespace_note_only(self) -> None:

        preset = MagicMock(spec=LoadoutPreset)

        preset.char_name = "角色A"

        preset.weapon_name = "武器B"

        preset.note = "  "

        label = _preset_label(preset)

        assert "  " not in label

