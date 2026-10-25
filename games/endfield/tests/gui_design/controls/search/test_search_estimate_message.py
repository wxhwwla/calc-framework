# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""compose_search_estimate_message 全覆盖测试。"""

from __future__ import annotations

from calc_framework.ui.i18n import set_locale
from games.endfield.gui.controls.search.search_estimate_message import compose_search_estimate_message


class TestComposeSearchEstimateMessage:
    def setup_method(self) -> None:
        set_locale("zh-CN")

    def test_no_char(self) -> None:
        msg = compose_search_estimate_message(
            has_char=False,
            has_weapon=True,
            catalog_err=None,
            weapons_empty=False,
            job_error=None,
            estimate_text=None,
        )

        assert "请先选择角色和武器" in msg

    def test_no_weapon(self) -> None:
        msg = compose_search_estimate_message(
            has_char=True,
            has_weapon=False,
            catalog_err=None,
            weapons_empty=False,
            job_error=None,
            estimate_text=None,
        )

        assert "请先选择角色和武器" in msg

    def test_catalog_err(self) -> None:
        msg = compose_search_estimate_message(
            has_char=True,
            has_weapon=True,
            catalog_err="装备目录加载失败。请检查数据文件。",
            weapons_empty=False,
            job_error=None,
            estimate_text=None,
        )

        assert "装备目录加载失败" in msg

    def test_weapons_empty(self) -> None:
        msg = compose_search_estimate_message(
            has_char=True,
            has_weapon=True,
            catalog_err=None,
            weapons_empty=True,
            job_error=None,
            estimate_text=None,
        )

        assert "武器候选为空" in msg

    def test_job_error(self) -> None:
        msg = compose_search_estimate_message(
            has_char=True,
            has_weapon=True,
            catalog_err=None,
            weapons_empty=False,
            job_error="技能数据缺失",
            estimate_text=None,
        )

        assert "技能数据缺失" in msg

    def test_estimate_text(self) -> None:
        msg = compose_search_estimate_message(
            has_char=True,
            has_weapon=True,
            catalog_err=None,
            weapons_empty=False,
            job_error=None,
            estimate_text="预计组合数：42,000",
        )

        assert msg == "预计组合数：42,000"

    def test_fallback_no_estimate(self) -> None:
        msg = compose_search_estimate_message(
            has_char=True,
            has_weapon=True,
            catalog_err=None,
            weapons_empty=False,
            job_error=None,
            estimate_text=None,
        )

        assert msg == "预计组合数：无法预估"
