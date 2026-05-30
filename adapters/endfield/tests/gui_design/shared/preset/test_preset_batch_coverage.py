from __future__ import annotations

from unittest.mock import MagicMock, patch

from games.endfield.gui_design.shared.preset_batch_compare import (
    PresetCompareRow,
    _empty_equipment,
    _find_by_name,
    _preset_label,
    _resolve_equipment,
    compare_presets_parallel,
)


class TestFindByName:
    def test_found(self) -> None:
        rows = [{"名称": "角色A"}, {"名称": "角色B"}]
        result = _find_by_name(rows, "角色A")
        assert result is not None
        assert result["名称"] == "角色A"

    def test_not_found(self) -> None:
        assert _find_by_name([{"名称": "A"}], "B") is None

    def test_empty_name(self) -> None:
        assert _find_by_name([{"名称": "A"}], "") is None
        assert _find_by_name([{"名称": "A"}], "  ") is None

    def test_empty_list(self) -> None:
        assert _find_by_name([], "A") is None


class TestEmptyEquipment:
    def test_creates_empty_dict(self) -> None:
        eq = _empty_equipment(slot_kind="护甲")
        assert eq["名称"] == "（空）"
        assert eq["装备种类"] == "护甲"
        assert eq["属性词条"] == []


class TestResolveEquipment:
    def test_resolves_found(self) -> None:
        equipments = [{"名称": "甲"}, {"名称": "乙"}]
        result = _resolve_equipment("甲", equipments, slot_kind="护甲")
        assert result["名称"] == "甲"

    def test_none_returns_empty(self) -> None:
        result = _resolve_equipment(None, [{"名称": "甲"}], slot_kind="护甲")
        assert result["名称"] == "（空）"

    def test_empty_string_returns_empty(self) -> None:
        result = _resolve_equipment("", [{"名称": "甲"}], slot_kind="护甲")
        assert result["名称"] == "（空）"

    def test_not_found_raises(self) -> None:
        import pytest
        with pytest.raises(ValueError, match="未找到装备"):
            _resolve_equipment("不存在", [{"名称": "甲"}], slot_kind="护甲")


class TestPresetLabel:
    def test_no_note(self) -> None:
        preset = MagicMock()
        preset.char_name = "角色A"
        preset.weapon_name = "武器B"
        preset.note = ""
        assert _preset_label(preset) == "角色A / 武器B"

    def test_with_note(self) -> None:
        preset = MagicMock()
        preset.char_name = "角色A"
        preset.weapon_name = "武器B"
        preset.note = "测试备注"
        assert "测试备注" in _preset_label(preset)

    def test_whitespace_note(self) -> None:
        preset = MagicMock()
        preset.char_name = "C"
        preset.weapon_name = "W"
        preset.note = "  "
        assert _preset_label(preset) == "C / W"


class TestPresetCompareRow:
    def test_create_with_error(self) -> None:
        row = PresetCompareRow(label="L", final_damage=0.0, loadout_summary="", error="错误信息")
        assert row.error == "错误信息"

    def test_create_ok(self) -> None:
        row = PresetCompareRow(label="L", final_damage=5000.0, loadout_summary="武器:A")
        assert row.final_damage == 5000.0


class TestComparePresetsParallel:
    def test_empty_input(self) -> None:
        result = compare_presets_parallel([], characters=[], weapons=[], equipments=[])
        assert result == []
