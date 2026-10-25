#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""Web GET /api/search/enemies 与 EnemyEvalParams 字段对齐。"""

import unittest

from web.backend.api.search import get_enemy_choices


class TestWebEnemyChoices(unittest.TestCase):
    """GET /api/search/enemies 端点测试。"""

    def test_default_enemy_has_full_eval_fields(self) -> None:
        rows = get_enemy_choices()
        self.assertGreaterEqual(len(rows), 1)
        default = rows[0]
        self.assertEqual(default["id"], "")
        for key in (
            "enemy_defense",
            "enemy_resistance",
            "ignore_resistance",
            "imbalance_vulnerability_coeff",
            "is_unbalanced",
            "is_true_damage",
            "combo_stacks",
            "break_defense_stacks",
            "attached_effect_multiplier",
            "corrosion_duration_seconds",
        ):
            self.assertIn(key, default)


if __name__ == "__main__":
    unittest.main()
