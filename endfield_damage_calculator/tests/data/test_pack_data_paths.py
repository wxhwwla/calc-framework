#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""打包/开发模式下游戏数据路径可解析（打包冒烟的轻量替代）。"""

import unittest
from pathlib import Path

from data.loader import CHARACTERS_JSON_PATH, WEAPONS_JSON_PATH, get_characters, get_weapons
from utils.path_utils import get_resource_path


class TestPackDataPaths(unittest.TestCase):
    """确保 PyInstaller 使用的相对路径在开发环境下可解析且非空。"""

    def test_character_json_path_exists(self):
        path = get_resource_path(CHARACTERS_JSON_PATH)
        self.assertTrue(path.is_file(), f"缺少角色数据: {path}")

    def test_weapon_json_path_exists(self):
        path = get_resource_path(WEAPONS_JSON_PATH)
        self.assertTrue(path.is_file(), f"缺少武器数据: {path}")

    def test_loader_returns_data_after_path_resolve(self):
        self.assertGreater(len(get_characters()), 0)
        self.assertGreater(len(get_weapons()), 0)


if __name__ == "__main__":
    unittest.main()
