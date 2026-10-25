#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""shared 子包：共享工具与纯 Python 模型。"""

from .weapon_data_model import extract_bonus_attributes, read_special_slots
from .weapon_filter import filter_weapons_for_character, resolve_weapon_type

__all__ = [
    "extract_bonus_attributes",
    "filter_weapons_for_character",
    "read_special_slots",
    "resolve_weapon_type",
]
