# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""P2-07：``ArknightsDamageApp`` 拆分后的结构门禁。

UI 构建与信号处理分别抽到两个 mixin 后，主类必须继续暴露原有方法；
行数门禁防止结构债回流。
"""

from __future__ import annotations

import importlib
from pathlib import Path


def test_damage_app_module_stays_within_line_budget() -> None:
    module = importlib.import_module("games.arknights.gui.ArknightsDamageApp")

    module_file = module.__file__
    assert module_file is not None
    path = Path(module_file)
    assert len(path.read_text(encoding="utf-8").splitlines()) <= 400


def test_damage_app_composes_ui_and_events_mixins() -> None:
    from games.arknights.gui.arknights_app_events import ArknightsAppEventsMixin
    from games.arknights.gui.arknights_app_ui import ArknightsAppUIMixin
    from games.arknights.gui.ArknightsDamageApp import ArknightsDamageApp

    assert issubclass(ArknightsDamageApp, ArknightsAppUIMixin)
    assert issubclass(ArknightsDamageApp, ArknightsAppEventsMixin)


def test_split_keeps_key_methods_on_main_class() -> None:
    from games.arknights.gui.arknights_app_events import ArknightsAppEventsMixin
    from games.arknights.gui.arknights_app_ui import ArknightsAppUIMixin
    from games.arknights.gui.ArknightsDamageApp import ArknightsDamageApp

    assert ArknightsDamageApp._build_left is ArknightsAppUIMixin._build_left
    assert ArknightsDamageApp._build_right is ArknightsAppUIMixin._build_right
    assert ArknightsDamageApp._on_skill_changed is ArknightsAppEventsMixin._on_skill_changed
    assert ArknightsDamageApp._update_detail is ArknightsAppEventsMixin._update_detail
    assert callable(ArknightsDamageApp._on_compute)
