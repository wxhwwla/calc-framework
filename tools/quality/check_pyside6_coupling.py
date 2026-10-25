#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""PySide6 耦合检查工具 — CI 中检测框架层新增 PySide6 导入。

用法:
    python tools/check_pyside6_coupling.py [--fix]

退出码:
    0 — 无违规
    1 — 发现新增 PySide6 导入
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

# 允许 PySide6 导入的目录（白名单）
ALLOWED_DIRS = {
    "framework/src/calc_framework/ui/viewer.py",
    "framework/src/calc_framework/ui/viewer_events.py",
    "framework/src/calc_framework/ui/viewer_render.py",
    "framework/src/calc_framework/ui/log_widget.py",
    "framework/src/calc_framework/ui/launcher/",
    "framework/src/calc_framework/ui/sheet_widgets.py",
    "framework/src/calc_framework/ui/sheet_evaluator.py",
    "framework/src/calc_framework/ui/_qt_backend.py",
    "framework/src/calc_framework/graph_editor/",
    "framework/src/calc_framework/dag/debugger_gui.py",
    "framework/src/calc_framework/editor/gui.py",
    "framework/src/calc_framework/dev_toolkit/",
    "tools/",
    "games/endfield/gui/",
    "games/arknights/gui/",
    "games/endfield/tests/",
    "games/arknights/tests/",
    "framework/tests/",
}

# 不应有 PySide6 导入的模块（已解耦的纯逻辑模块）
DECOUPLED_MODULES = {
    "framework/src/calc_framework/ui/sheet_evaluator_core.py",
    "framework/src/calc_framework/ui/theme.py",
    "framework/src/calc_framework/ui/controls.py",
    "framework/src/calc_framework/ui/layout.py",
    "framework/src/calc_framework/ui/viewer_evaluator.py",
    "framework/src/calc_framework/dev_toolkit/adapter_creator.py",
    "games/endfield/gui/app/compute_sheet_variables.py",
    "games/endfield/gui/app/enemy_params_state.py",
    "games/endfield/gui/app/loadout_serialize.py",
    "games/endfield/gui/app/loadout_reader.py",
    "games/endfield/gui/app/search_controller.py",
    "games/endfield/gui/controls/search/search_history_data.py",
    "games/endfield/gui/controls/search/search_worker_logic.py",
    "games/endfield/gui/controls/survival/survival_estimator.py",
    "games/endfield/gui/controls/enemy/enemy_panel_model.py",
    "games/endfield/gui/controls/enhancement/preset_compare_service.py",
    "games/endfield/gui/shared/weapon_filter.py",
    "games/endfield/gui/shared/display_view/zone_display_builder.py",
    "games/endfield/gui/presentation/total_damage_display_data.py",
    "games/endfield/gui/panels/selection/selection_model.py",
    "games/endfield/gui/shell/fixed_loadout_slots.py",
    "games/arknights/gui/arknights_sheet_config.py",
    "games/endfield/gui/shared/weapon_data_model.py",
    "games/endfield/gui/controls/ocr/ocr_pipeline.py",
    # 以下为 PySide6-free 但未在阶段 1-3 中显式提取的业务逻辑模块
    "games/endfield/gui/app/loadout_state.py",
    "games/endfield/gui/app/loadout_preset.py",
    "games/endfield/gui/app/loadout_evaluation.py",
    "games/endfield/gui/app/display_request.py",
    "games/endfield/gui/app/confirm_refresh.py",
    "games/endfield/gui/shared/preset_batch_compare.py",
    "games/endfield/gui/shared/damage_visualization.py",
    "games/endfield/gui/shared/weapon_display_text.py",
    "games/endfield/gui/presentation/display/format.py",
    "games/endfield/gui/controls/search/search_settings.py",
}


def _has_pyside6_import(filepath: Path) -> bool:
    """检查文件是否包含 PySide6 导入。"""
    try:
        source = filepath.read_text(encoding="utf-8")
        tree = ast.parse(source)
    except (SyntaxError, UnicodeDecodeError):
        return False

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith("PySide6"):
                    return True
        elif isinstance(node, ast.ImportFrom):
            if node.module and node.module.startswith("PySide6"):
                return True
    return False


def check_decoupled_modules(root: Path) -> list[str]:
    """检查已解耦模块是否意外引入了 PySide6。"""
    violations = []
    for rel_path in DECOUPLED_MODULES:
        filepath = root / rel_path
        if filepath.exists() and _has_pyside6_import(filepath):
            violations.append(rel_path)
    return violations


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    violations = check_decoupled_modules(root)

    if violations:
        print("[FAIL] Found PySide6 imports in decoupled modules:")
        for v in violations:
            print(f"  - {v}")
        return 1

    print("[OK] All decoupled modules are PySide6-free")
    return 0


if __name__ == "__main__":
    sys.exit(main())
