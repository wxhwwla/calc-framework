#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GUI 数据加载失败时的用户提示测试"""

import unittest
from unittest.mock import patch

from data.game_data_facade import GameDataFacade
from data.loader import DataLoadError, fetch_game_data_for_gui


class TestGuiDataLoad(unittest.TestCase):
    @patch("data.game_data_facade.get_equipments", return_value=[])
    @patch("data.game_data_facade.get_weapons")
    @patch("data.game_data_facade.get_characters")
    def test_fetch_returns_error_without_raising(
        self, mock_chars, mock_weapons, _mock_equip
    ) -> None:
        mock_chars.side_effect = DataLoadError("characters.json", "文件不存在")
        mock_weapons.return_value = []
        chars, weapons, err = fetch_game_data_for_gui()
        self.assertEqual(chars, [])
        self.assertEqual(weapons, [])
        self.assertIsInstance(err, DataLoadError)

    @patch("data.game_data_facade.get_equipments", return_value=[])
    @patch("data.game_data_facade.get_characters", return_value=[{"名称": "测试"}])
    @patch("data.game_data_facade.get_weapons", return_value=[{"名称": "武器"}])
    def test_fetch_success(self, _mock_weapons, _mock_chars, _mock_equip) -> None:
        chars, weapons, err = fetch_game_data_for_gui()
        self.assertEqual(len(chars), 1)
        self.assertEqual(len(weapons), 1)
        self.assertIsNone(err)

    def test_facade_create_matches_fetch_lists(self) -> None:
        with patch(
            "data.game_data_facade.get_characters", return_value=[{"名称": "A"}]
        ), patch(
            "data.game_data_facade.get_weapons", return_value=[{"名称": "W"}]
        ), patch("data.game_data_facade.get_equipments", return_value=[]):
            facade = GameDataFacade.create()
            chars, weapons, err = fetch_game_data_for_gui()
        self.assertEqual(chars, facade.characters)
        self.assertEqual(weapons, facade.weapons)
        self.assertIsNone(err)


if __name__ == "__main__":
    unittest.main()
