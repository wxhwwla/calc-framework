#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""敌方参数面板子包。"""

from .enemy_panel_model import EnemyResolvedParams, default_enemy_params, resolve_enemy_params
from .qt_enemy_panel import QtEnemyPanel

__all__ = [
    "EnemyResolvedParams",
    "QtEnemyPanel",
    "default_enemy_params",
    "resolve_enemy_params",
]
