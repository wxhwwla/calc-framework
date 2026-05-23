#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""向后兼容：请直接从 gui_settings / property_display / selection_components 导入。"""

from gui_design.gui_settings import gui_settings
from gui_design.property_display import confirm_selection
from gui_design.selection_panel import ChooseTypesStarsNamesLevels

__all__ = ("gui_settings", "confirm_selection", "ChooseTypesStarsNamesLevels")
