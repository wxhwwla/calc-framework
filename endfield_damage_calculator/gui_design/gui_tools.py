#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""向后兼容：请改用 gui_design.display_model。"""

from gui_design.display_model import (
    ChooseTypesStarsNamesLevels,
    confirm_selection,
    gui_settings,
)
from gui_design.property_display import LEVEL_ATTRIBUTES, _get_attribute_value

__all__ = [
    "gui_settings",
    "ChooseTypesStarsNamesLevels",
    "confirm_selection",
    "LEVEL_ATTRIBUTES",
    "_get_attribute_value",
]
