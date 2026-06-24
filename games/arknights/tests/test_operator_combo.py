# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""干员搜索 helper 测试。"""

from __future__ import annotations

from games.arknights.gui.operator_combo import filter_operator_names


class TestFilterOperatorNames:
    def test_empty_query_returns_all(self) -> None:
        names = ["能天使", "阿米娅", "12F"]
        assert filter_operator_names(names, "") == names

    def test_substring_match(self) -> None:
        names = ["能天使", "阿米娅", "12F"]
        assert filter_operator_names(names, "能") == ["能天使"]

    def test_no_match(self) -> None:
        assert filter_operator_names(["能天使"], "xyz") == []
