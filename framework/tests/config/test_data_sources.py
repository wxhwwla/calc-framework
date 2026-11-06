# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""实体来源与数据文件名的共享映射测试。"""

from calc_framework.data import DATA_STEM_SOURCE, SOURCE_DATA_STEMS, SOURCE_DISPLAY_NAMES


def test_source_data_stems() -> None:
    assert SOURCE_DATA_STEMS == {
        "character": "characters",
        "weapon": "weapons",
        "equipment": "equipments",
        "enemy": "enemies",
    }


def test_data_stem_source_is_reverse_mapping() -> None:
    for source, stem in SOURCE_DATA_STEMS.items():
        assert DATA_STEM_SOURCE[stem] == source


def test_display_names_cover_all_sources() -> None:
    assert SOURCE_DISPLAY_NAMES == {
        "character": "角色",
        "weapon": "武器",
        "equipment": "装备",
        "enemy": "敌人",
    }
