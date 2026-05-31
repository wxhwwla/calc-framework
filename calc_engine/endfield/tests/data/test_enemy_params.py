#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""插件敌人参数解析测试。"""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from calc_engine.endfield.data_loading.enemy_params import resolve_enemy_defense
from calc_engine.endfield.data_loading.plugin_registry import PluginRegistry


class TestEnemyParams(unittest.TestCase):
    def test_resolve_default_when_missing(self) -> None:
        reg = PluginRegistry()
        with patch("calc_engine.endfield.data_loading.enemy_params.get_plugin_registry", return_value=reg):
            self.assertEqual(resolve_enemy_defense(""), 100.0)

    def test_resolve_from_plugin_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "enemies").mkdir()
            (root / "enemies" / "boss.json").write_text(
                json.dumps(
                    {"id": "test_boss", "名称": "测试首领", "enemy_defense": 420.0},
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            reg = PluginRegistry()
            reg.load_from_directory(root)
            with patch("calc_engine.endfield.data_loading.enemy_params.get_plugin_registry", return_value=reg):
                self.assertEqual(resolve_enemy_defense("test_boss"), 420.0)


if __name__ == "__main__":
    unittest.main()
