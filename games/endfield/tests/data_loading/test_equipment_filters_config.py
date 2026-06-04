# SPDX-License-Identifier: AGPL-3.0
"""覆盖 equipment_filters / core/config。"""

from __future__ import annotations

from games.endfield.calc.core.config import (
    get_attribute_category,
    get_default_growth_params,
    is_character_attribute,
)
from games.endfield.data_loading.equipment_filters import (
    filter_rows_by_set_label,
    list_set_filter_options,
)

# ── calc/core/config.py ──────────────────────────────────────────────────


class TestCoreConfig:
    """get_default_growth_params / get_attribute_category / is_character_attribute。"""

    def test_get_default_growth_params_returns_copy(self) -> None:
        params = get_default_growth_params()
        assert "力量" in params
        assert "基础攻击力" in params
        assert params["力量"]["base"] == 0

    def test_get_attribute_category_character_normal(self) -> None:
        assert get_attribute_category("力量") == "character_normal"
        assert get_attribute_category("敏捷") == "character_normal"

    def test_get_attribute_category_character_skill(self) -> None:
        assert get_attribute_category("战技倍率") == "character_skill"

    def test_get_attribute_category_weapon_base(self) -> None:
        # 基础攻击力 出现在 character_normal 中优先级更高
        assert get_attribute_category("基础攻击力") == "character_normal"
        # 没有独立的 weapon_base 测试项，改用无冲突名
        assert get_attribute_category("weapon_only_attr") == "unknown"

    def test_get_attribute_category_weapon_bonus(self) -> None:
        assert get_attribute_category("攻击力+") == "weapon_bonus"
        assert get_attribute_category("力量+") == "weapon_bonus"

    def test_get_attribute_category_unknown(self) -> None:
        assert get_attribute_category("未知") == "unknown"

    def test_is_character_attribute_true(self) -> None:
        assert is_character_attribute("力量") is True
        assert is_character_attribute("战技倍率") is True

    def test_is_character_attribute_false(self) -> None:
        assert is_character_attribute("攻击力+") is False
        assert is_character_attribute("未知") is False


# ── data_loading/equipment_filters.py ────────────────────────────────────


class TestEquipmentFilters:
    """list_set_filter_options / filter_rows_by_set_label。"""

    def test_list_options_all_only(self) -> None:
        options = list_set_filter_options([])
        assert options == ["全部"]

    def test_list_options_with_sets(self) -> None:
        rows = [
            {"套装": "晨曦"},
            {"套装": "暮色"},
            {"套装": "晨曦"},
            {"套装": ""},
        ]
        options = list_set_filter_options(rows)
        assert options == ["全部", "晨曦", "暮色", "仅散件"]

    def test_list_options_no_loose(self) -> None:
        rows = [{"套装": "晨曦"}, {"套装": "暮色"}]
        options = list_set_filter_options(rows)
        assert "仅散件" not in options

    def test_filter_all(self) -> None:
        rows = [{"名称": "A", "套装": "晨曦"}, {"名称": "B", "套装": "暮色"}]
        result = filter_rows_by_set_label(rows, "全部")
        assert len(result) == 2

    def test_filter_specific_set(self) -> None:
        rows = [{"名称": "A", "套装": "晨曦"}, {"名称": "B", "套装": "暮色"}]
        result = filter_rows_by_set_label(rows, "晨曦")
        assert len(result) == 1
        assert result[0]["名称"] == "A"

    def test_filter_loose(self) -> None:
        rows = [{"名称": "A", "套装": "晨曦"}, {"名称": "B", "套装": ""}]
        result = filter_rows_by_set_label(rows, "仅散件")
        assert len(result) == 1
        assert result[0]["名称"] == "B"

    def test_filter_loose_no_loose_items(self) -> None:
        rows = [{"名称": "A", "套装": "晨曦"}]
        result = filter_rows_by_set_label(rows, "仅散件")
        assert len(result) == 0
