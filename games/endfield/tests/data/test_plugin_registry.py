#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""插件化数据热加载测试。"""

import json
import tempfile
import unittest
from pathlib import Path

from games.endfield.data_loading.plugin_registry import PluginRegistry


class TestPluginRegistry(unittest.TestCase):
    def test_loads_json_enemy_from_plugins_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "enemies").mkdir()
            (root / "enemies" / "test_boss.json").write_text(
                json.dumps(
                    {
                        "id": "test_boss",
                        "名称": "测试首领",
                        "enemy_defense": 500.0,
                        "enemy_resistance": 0.2,
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            reg = PluginRegistry()
            reg.load_from_directory(root)
            enemy = reg.get_enemy("test_boss")
            self.assertIsNotNone(enemy)
            assert enemy is not None
            self.assertEqual(enemy["enemy_defense"], 500.0)

    def test_reload_clears_previous_entries(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            reg = PluginRegistry()
            reg.load_from_directory(root)
            self.assertEqual(reg.enemy_count(), 0)


if __name__ == "__main__":
    unittest.main()
