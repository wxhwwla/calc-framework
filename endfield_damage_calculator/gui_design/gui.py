#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""兼容 re-export：实现位于 gui_design.shell.app。"""

from gui_design.shell.app import (  # noqa: F401
    DamageCalculatorApp,
    build_weapon_candidates,
    main,
    mark_loadout_pending,
    schedule_confirm,
)

__all__ = [
    "DamageCalculatorApp",
    "build_weapon_candidates",
    "main",
    "mark_loadout_pending",
    "schedule_confirm",
]

if __name__ == "__main__":
    main()
