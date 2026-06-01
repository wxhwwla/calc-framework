# SPDX-License-Identifier: AGPL-3.0
"""统一启动器 GUI 包。"""

from calc_framework.ui.launcher.runtime import (
    AdapterEntry,
    argv_for_adapter,
    list_adapter_entries,
    repo_root,
    spawn_detached,
)
from calc_framework.ui.launcher.window import GameLauncherWindow, run_gui_launcher

__all__ = [
    "AdapterEntry",
    "GameLauncherWindow",
    "argv_for_adapter",
    "list_adapter_entries",
    "repo_root",
    "run_gui_launcher",
    "spawn_detached",
]
