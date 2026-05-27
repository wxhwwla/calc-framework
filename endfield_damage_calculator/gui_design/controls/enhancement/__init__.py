#!/usr/bin/env python3
"""工具与分享控件。"""

from .dialogs import (
    get_app_calculation_history,
    record_calculation_history,
    refresh_damage_snapshot,
    show_calculation_history_dialog,
    show_damage_dashboard_dialog,
    show_preset_compare_dialog,
)
from .preset import apply_preset_to_app, build_preset_from_app
from .section import place_enhancement_section

__all__ = [
    "apply_preset_to_app",
    "build_preset_from_app",
    "get_app_calculation_history",
    "place_enhancement_section",
    "record_calculation_history",
    "refresh_damage_snapshot",
    "show_calculation_history_dialog",
    "show_damage_dashboard_dialog",
    "show_preset_compare_dialog",
]
