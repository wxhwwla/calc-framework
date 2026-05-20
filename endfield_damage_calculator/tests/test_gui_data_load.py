#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GUI 数据加载失败时的用户提示测试"""

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from data.loader import DataLoadError, fetch_game_data_for_gui


class TestGuiDataLoad(unittest.TestCase):
    @patch("data.loader.get_characters")
    @patch("data.loader.get_weapons")
    def test_fetch_returns_error_without_raising(self, mock_weapons, mock_chars):
        mock_chars.side_effect = DataLoadError("characters.json", "文件不存在")
        chars, weapons, err = fetch_game_data_for_gui()
        self.assertEqual(chars, [])
        self.assertEqual(weapons, [])
        self.assertIsInstance(err, DataLoadError)
        mock_weapons.assert_not_called()

    @patch("data.loader.get_characters", return_value=[{"名称": "测试"}])
    @patch("data.loader.get_weapons", return_value=[{"名称": "武器"}])
    def test_fetch_success(self, _mock_weapons, _mock_chars):
        chars, weapons, err = fetch_game_data_for_gui()
        self.assertEqual(len(chars), 1)
        self.assertEqual(len(weapons), 1)
        self.assertIsNone(err)


if __name__ == "__main__":
    unittest.main()
