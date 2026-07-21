# -*- coding: utf-8 -*-
"""GUI 控件实例化测试脚本。"""

import os
import sys

os.environ["QT_QPA_PLATFORM"] = "offscreen"
_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", ".."))
sys.path.insert(0, _ROOT)
sys.path.insert(0, os.path.join(_ROOT, "framework", "src"))

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

app = QApplication.instance() or QApplication(sys.argv)

big_font = QFont()
big_font.setPointSize(12)
small_font = QFont()
small_font.setPointSize(10)

results = []


def test(name, func):
    try:
        func()
        results.append((name, True, ""))
        print(f"  [OK] {name}")
    except Exception as e:
        import traceback

        results.append((name, False, str(e)))
        print(f"  [FAIL] {name}: {e}")
        traceback.print_exc()


print("=== GUI 控件实例化测试 ===\n")


# 1. QtEnemyPanel
def test_enemy_panel():
    from games.endfield.gui.controls.enemy.qt_enemy_panel import QtEnemyPanel

    panel = QtEnemyPanel(font=small_font)
    params = panel.get_params()
    assert "enemy_defense" in params, f"Missing 'enemy_defense' in params: {list(params.keys())}"
    assert "enemy_resistance" in params
    print(f"    enemy_defense={params['enemy_defense']}, enemy_resistance={params['enemy_resistance']}")
    print(f"    Keys: {list(params.keys())}")


test("QtEnemyPanel", test_enemy_panel)


# 2. QtSelectionPanel (character)
def test_selection_panel_char():
    # Load character data
    import json

    from games.endfield.gui.panels.selection.qt_panel import QtSelectionPanel

    data_path = os.path.join(_ROOT, "games", "endfield", "data", "characters.json")
    with open(data_path, encoding="utf-8") as f:
        data_list = json.load(f)
    panel = QtSelectionPanel(data_list, big_font, is_weapon_panel=False)
    assert panel is not None
    print(f"    type_combo items: {panel.type_combo.count()}, data_list: {len(data_list)}")


test("QtSelectionPanel (character)", test_selection_panel_char)


# 3. QtSelectionPanel (weapon)
def test_selection_panel_weapon():
    import json

    from games.endfield.gui.panels.selection.qt_panel import QtSelectionPanel

    data_path = os.path.join(_ROOT, "games", "endfield", "data", "weapons.json")
    with open(data_path, encoding="utf-8") as f:
        data_list = json.load(f)
    panel = QtSelectionPanel(data_list, big_font, is_weapon_panel=True)
    assert panel is not None
    print(f"    type_combo items: {panel.type_combo.count()}, data_list: {len(data_list)}")


test("QtSelectionPanel (weapon)", test_selection_panel_weapon)


# 4. QtAttributeColumns
def test_attr_columns():
    from games.endfield.gui.shared.display_view.qt_columns import QtAttributeColumns

    cols = QtAttributeColumns(big_font=big_font, small_font=small_font)
    assert cols is not None


test("QtAttributeColumns", test_attr_columns)


# 5. TotalDamagePanel
def test_total_damage():
    from games.endfield.gui.presentation.total_damage_panel import TotalDamagePanel

    tdp = TotalDamagePanel(big_font=big_font, small_font=small_font)
    assert tdp is not None


test("TotalDamagePanel", test_total_damage)


# 6. QtTrustPanel
def test_trust_panel():
    from games.endfield.gui.panels.selection.qt_subpanels import QtTrustPanel

    panel = QtTrustPanel(font=small_font)
    assert panel is not None


test("QtTrustPanel", test_trust_panel)


# 7. QtSkillLevelPanel
def test_skill_level_panel():
    from games.endfield.gui.panels.selection.qt_subpanels import QtSkillLevelPanel

    panel = QtSkillLevelPanel(font=small_font)
    assert panel is not None


test("QtSkillLevelPanel", test_skill_level_panel)


# 8. QtSpecialAbilityPanel
def test_ability_panel():
    from games.endfield.gui.panels.selection.qt_ability_panel import QtSpecialAbilityPanel

    panel = QtSpecialAbilityPanel(font=small_font)
    assert panel is not None


test("QtSpecialAbilityPanel", test_ability_panel)

# 9. ComputeSheet - skip (needs DAGService + Layout + variables)
print("  [SKIP] ComputeSheet (needs full DAG setup)")

# 10. QtControlDock


# 10. QtControlDock
def test_control_dock():
    from games.endfield.gui.shell.qt_control_dock import QtControlDock

    dock = QtControlDock(big_font=big_font, small_font=small_font)
    assert dock is not None
    # Verify key controls exist
    assert hasattr(dock, "calc_mode_menu")
    assert hasattr(dock, "back_to_main_btn")
    assert hasattr(dock, "confirm_btn")
    print(f"    calc_mode_menu items: {dock.calc_mode_menu.count()}")


test("QtControlDock", test_control_dock)

# Summary
print("\n=== Summary ===")
passed = sum(1 for _, ok, _ in results if ok)
failed = sum(1 for _, ok, _ in results if not ok)
print(f"  Passed: {passed}/{len(results)}")
if failed:
    print(f"  Failed: {failed}")
    for name, ok, err in results:
        if not ok:
            print(f"    - {name}: {err}")
    sys.exit(1)
else:
    print("  All tests passed!")
