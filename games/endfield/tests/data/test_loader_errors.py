#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# SPDX-License-Identifier: AGPL-3.0
"""data.loader 严格加载与错误类型测试"""

import unittest
from unittest.mock import patch

from games.endfield.data_loading import loader
from games.endfield.data_loading.loader import DataLoadError, load_json_file


class TestLoaderErrors(unittest.TestCase):
    def tearDown(self):
        loader.reload_characters()

        loader.reload_weapons()

    def test_strict_missing_file_raises(self):
        with self.assertRaises(DataLoadError):
            load_json_file("__missing_game_data_test__.json", strict=True)

    def test_get_weapons_raises_when_file_missing(self):
        loader.reload_weapons()

        with patch.object(loader, "WEAPONS_JSON_PATH", "__missing_weapons_test__.json"):
            with self.assertRaises(DataLoadError):
                loader.get_weapons()


if __name__ == "__main__":
    unittest.main()
