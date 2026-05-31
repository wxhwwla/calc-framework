#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""GUI 数据加载失败时的用户提示测试"""

import unittestfrom unittest.mock import patchfrom games.endfield.data_loading.game_data_facade import GameDataFacadefrom games.endfield.data_loading.loader import DataLoadError, fetch_game_data_for_guiclass TestGuiDataLoad(unittest.TestCase):
    @patch("games.endfield.data_loading.game_data_facade.get_equipments", return_value=[])
    @patch("games.endfield.data_loading.game_data_facade.get_weapons")
    @patch("games.endfield.data_loading.game_data_facade.get_characters")
    def test_fetch_returns_error_without_raising(self, mock_chars, mock_weapons, _mock_equip) -> None:
        mock_chars.side_effect = DataLoadError("characters.json", "文件不存在")
        mock_weapons.return_value = []
        chars, weapons, err = fetch_game_data_for_gui()
        self.assertEqual(chars, [])
        self.assertEqual(weapons, [])
        self.assertIsInstance(err, DataLoadError)

    @patch("games.endfield.data_loading.game_data_facade.get_equipments", return_value=[])
    @patch("games.endfield.data_loading.game_data_facade.get_characters", return_value=[{"名称": "测试"}])
    @patch("games.endfield.data_loading.game_data_facade.get_weapons", return_value=[{"名称": "武器"}])
    def test_fetch_success(self, _mock_weapons, _mock_chars, _mock_equip) -> None:
        chars, weapons, err = fetch_game_data_for_gui()
        self.assertEqual(len(chars), 1)
        self.assertEqual(len(weapons), 1)
        self.assertIsNone(err)

    def test_facade_create_matches_fetch_lists(self) -> None:
        with (
            patch("games.endfield.data_loading.game_data_facade.get_characters", return_value=[{"名称": "A"}]),
            patch("games.endfield.data_loading.game_data_facade.get_weapons", return_value=[{"名称": "W"}]),
            patch("games.endfield.data_loading.game_data_facade.get_equipments", return_value=[]),
        ):
            facade = GameDataFacade.create()
            chars, weapons, err = fetch_game_data_for_gui()
        self.assertEqual(chars, facade.characters)
        self.assertEqual(weapons, facade.weapons)
        self.assertIsNone(err)


if __name__ == "__main__":
    unittest.main()
