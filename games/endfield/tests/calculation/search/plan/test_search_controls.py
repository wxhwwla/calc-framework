#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# SPDX-License-Identifier: AGPL-3.0
"""search_controls 纯逻辑与预估文案测试。"""

import unittest

from games.endfield.gui.controls.search.search_estimate_message import compose_search_estimate_message


class TestSearchControls(unittest.TestCase):
    def test_compose_message_requires_selection(self) -> None:
        text = compose_search_estimate_message(
            has_char=False,
            has_weapon=True,
            catalog_err=None,
            weapons_empty=False,
            job_error=None,
            estimate_text=None,
        )

        self.assertIn("请先选择角色和武器", text)

    def test_compose_message_catalog_error_truncates_at_period(self) -> None:
        text = compose_search_estimate_message(
            has_char=True,
            has_weapon=True,
            catalog_err="装备数据损坏。请检查 JSON。",
            weapons_empty=False,
            job_error=None,
            estimate_text=None,
        )

        self.assertEqual(text, "预计组合数：装备数据损坏")

    def test_compose_message_uses_estimate_when_ready(self) -> None:
        line = "预计组合数：1,234 组 · 约 2 分钟"

        text = compose_search_estimate_message(
            has_char=True,
            has_weapon=True,
            catalog_err=None,
            weapons_empty=False,
            job_error=None,
            estimate_text=line,
        )

        self.assertEqual(text, line)

    def test_compose_message_weapons_empty(self) -> None:
        text = compose_search_estimate_message(
            has_char=True,
            has_weapon=True,
            catalog_err=None,
            weapons_empty=True,
            job_error=None,
            estimate_text=None,
        )

        self.assertIn("武器候选为空", text)


if __name__ == "__main__":
    unittest.main()
