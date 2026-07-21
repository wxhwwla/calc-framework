# -*- coding: utf-8 -*-
"""GUI 主应用创建测试。"""

import os
import sys

os.environ["QT_QPA_PLATFORM"] = "offscreen"
_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", ".."))
sys.path.insert(0, _ROOT)
sys.path.insert(0, os.path.join(_ROOT, "framework", "src"))

from PySide6.QtWidgets import QApplication

app = QApplication.instance() or QApplication(sys.argv)

print("=== EndfieldApp 创建测试 ===\n")

try:
    from games.endfield.gui.endfield_app import EndfieldApp

    print("[OK] EndfieldApp imported")

    # Try to create the app
    main_app = EndfieldApp()
    print("[OK] EndfieldApp created")

    # Check key attributes
    checks = [
        ("calc_page", "计算页"),
        ("adv_page", "高级页"),
        ("char_panel", "角色选择面板"),
        ("weapon_panel", "武器选择面板"),
        ("attr_columns", "属性列"),
        ("control_dock", "高级页控制栏"),
    ]

    for attr, desc in checks:
        if hasattr(main_app, attr):
            val = getattr(main_app, attr)
            if val is not None:
                print(f"  [OK] {desc} ({attr})")
            else:
                print(f"  [WARN] {desc} ({attr}) is None")
        else:
            print(f"  [MISS] {desc} ({attr}) not found")

    # Check if compute sheet exists
    if hasattr(main_app, "_compute_sheet"):
        cs = main_app._compute_sheet
        if cs is not None:
            print("  [OK] ComputeSheet")
        else:
            print("  [WARN] ComputeSheet is None")

    print("\n=== EndfieldApp 测试完成 ===")

except Exception as e:
    import traceback

    print(f"[FAIL] EndfieldApp: {e}")
    traceback.print_exc()
