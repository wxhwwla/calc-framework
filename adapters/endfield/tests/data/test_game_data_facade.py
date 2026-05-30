#!/usr/bin/env python3
"""GameDataFacade 统一数据门面测试。"""

import unittest
from unittest.mock import patch

from adapters.endfield.data_loading.game_data_facade import GameDataFacade
from adapters.endfield.data_loading.loader import DataLoadError


def _equip_row(name: str, slot: str) -> dict:
    return {
        "名称": name,
        "部位": slot,
        "效果": [],
        "三件套效果": [],
        "套装": "",
    }


class TestGameDataFacade(unittest.TestCase):
    @patch("adapters.endfield.data_loading.game_data_facade.get_equipments")
    @patch("adapters.endfield.data_loading.game_data_facade.get_weapons", return_value=[{"名称": "剑"}])
    @patch("adapters.endfield.data_loading.game_data_facade.get_characters", return_value=[{"名称": "人"}])
    def test_create_loads_three_lists(self, _c, _w, mock_equip) -> None:
        mock_equip.return_value = [
            _equip_row("甲", "护甲"),
            _equip_row("手", "护手"),
            _equip_row("饰", "配件"),
        ]
        facade = GameDataFacade.create()
        self.assertEqual(len(facade.characters), 1)
        self.assertEqual(len(facade.weapons), 1)
        self.assertEqual(len(facade.equipment_rows), 3)
        self.assertIsNone(facade.load_error)

    @patch("adapters.endfield.data_loading.game_data_facade.get_equipments", return_value=[])
    @patch("adapters.endfield.data_loading.game_data_facade.get_weapons")
    @patch("adapters.endfield.data_loading.game_data_facade.get_characters")
    def test_create_records_character_load_error(self, mock_c, mock_w, _e) -> None:
        mock_c.side_effect = DataLoadError("characters.json", "损坏")
        mock_w.return_value = []
        facade = GameDataFacade.create()
        self.assertEqual(facade.characters, [])
        self.assertIsInstance(facade.load_error, DataLoadError)

    @patch("adapters.endfield.data_loading.game_data_facade.get_equipment_catalog")
    @patch("adapters.endfield.data_loading.game_data_facade.get_equipments")
    @patch("adapters.endfield.data_loading.game_data_facade.get_weapons", return_value=[])
    @patch("adapters.endfield.data_loading.game_data_facade.get_characters", return_value=[])
    def test_equipment_catalog_passes_cached_rows(
        self,
        _c,
        _w,
        mock_equip,
        mock_catalog,
    ) -> None:
        rows = [_equip_row("甲", "护甲")]
        mock_equip.return_value = rows
        mock_catalog.return_value = {"chest": rows, "gloves": [], "accessories": []}
        facade = GameDataFacade.create()
        mock_equip.reset_mock()
        facade.equipment_catalog("仅散件装备")
        mock_equip.assert_not_called()
        mock_catalog.assert_called_once()
        _args, kwargs = mock_catalog.call_args
        self.assertIs(kwargs.get("equipment_rows"), facade.equipment_rows)
        self.assertEqual(kwargs.get("scope_label"), "仅散件装备")

    def test_manual_facade_catalog_search_error_when_incomplete(self) -> None:
        facade = GameDataFacade(
            characters=[],
            weapons=[],
            equipment_rows=[_equip_row("仅甲", "护甲")],
        )
        err = facade.catalog_search_error("全部装备")
        self.assertIsNotNone(err)
        self.assertIn("不完整", err)


if __name__ == "__main__":
    unittest.main()
