# -*- coding: utf-8 -*-
"""GUI 主应用详细检查。"""

import os
import sys

os.environ["QT_QPA_PLATFORM"] = "offscreen"
_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", ".."))
sys.path.insert(0, _ROOT)
sys.path.insert(0, os.path.join(_ROOT, "framework", "src"))

from PySide6.QtWidgets import QApplication

app = QApplication.instance() or QApplication(sys.argv)

print("=== EndfieldApp 详细检查 ===\n")

from games.endfield.gui.endfield_app import EndfieldApp

main_app = EndfieldApp()
print("[OK] EndfieldApp created\n")

# List all non-private attributes
print("--- 公开属性 ---")
attrs = [a for a in dir(main_app) if not a.startswith("_") and not callable(getattr(main_app, a, None))]
for a in sorted(attrs):
    val = getattr(main_app, a, None)
    if val is not None and not isinstance(val, int | float | str | bool):
        print(f"  {a}: {type(val).__name__}")

# Check specific controls
print("\n--- 关键控件检查 ---")
checks = {
    "char_panel": "角色选择面板",
    "weapon_panel": "武器选择面板",
    "control_dock": "高级页控制栏",
    "_compute_sheet": "ComputeSheet",
    "_attr_columns": "属性列",
    "_total_damage_panel": "总伤面板",
}

for attr, desc in checks.items():
    val = getattr(main_app, attr, None)
    status = "OK" if val is not None else "MISS"
    print(f"  [{status}] {desc} ({attr}): {type(val).__name__ if val else 'None'}")

# Check control_dock sub-controls
print("\n--- 高级页控件检查 ---")
cd = getattr(main_app, "control_dock", None)
if cd:
    dock_checks = {
        "calc_mode_menu": "计算模式下拉",
        "back_to_main_btn": "返回按钮",
        "confirm_btn": "确认按钮",
        "help_btn": "帮助按钮",
        "search_history_btn": "搜索历史按钮",
        "single_skill_scope_combo": "武器候选范围",
        "equipment_scope_combo": "装备范围",
        "full_search_btn": "全量遍历按钮",
        "mvp_search_btn": "MVP搜索按钮",
        "use_manual_skill_counts_cb": "手动次数开关",
    }
    for attr, desc in dock_checks.items():
        val = getattr(cd, attr, None)
        status = "OK" if val is not None else "MISS"
        print(f"  [{status}] {desc} ({attr})")

# Check char_panel sub-controls
print("\n--- 角色选择面板控件检查 ---")
cp = getattr(main_app, "char_panel", None)
if cp:
    panel_checks = {
        "type_combo": "类型下拉",
        "star_combo": "星级下拉",
        "name_combo": "名称下拉",
        "level_slider": "等级滑块",
    }
    for attr, desc in panel_checks.items():
        val = getattr(cp, attr, None)
        status = "OK" if val is not None else "MISS"
        if val is not None:
            if hasattr(val, "count"):
                print(f"  [{status}] {desc} ({attr}): count={val.count()}")
            elif hasattr(val, "minimum"):
                print(f"  [{status}] {desc} ({attr}): min={val.minimum()}, max={val.maximum()}")
            else:
                print(f"  [{status}] {desc} ({attr})")
        else:
            print(f"  [{status}] {desc} ({attr})")

print("\n=== 检查完成 ===")
