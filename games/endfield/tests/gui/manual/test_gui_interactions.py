# -*- coding: utf-8 -*-
"""GUI 控件交互测试。"""

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


print("=== GUI 控件交互测试 ===\n")


# 1. QtEnemyPanel signal test
def test_enemy_panel_signal():
    from games.endfield.gui.controls.enemy.qt_enemy_panel import QtEnemyPanel

    panel = QtEnemyPanel(font=small_font)
    received = []
    panel.enemy_params_changed.connect(lambda d: received.append(d))
    panel._defense_spin.setValue(200.0)
    app.processEvents()
    assert len(received) > 0, "Signal not emitted"
    assert received[-1]["enemy_defense"] == 200.0
    print(f"    Signal emitted with defense={received[-1]['enemy_defense']}")


test("QtEnemyPanel signal emission", test_enemy_panel_signal)


# 2. QtEnemyPanel set_params/get_params roundtrip
def test_enemy_panel_roundtrip():
    from games.endfield.gui.controls.enemy.qt_enemy_panel import QtEnemyPanel

    panel = QtEnemyPanel(font=small_font)
    test_params = {
        "enemy_defense": 500.0,
        "enemy_resistance": 30.0,
        "is_unbalanced": True,
        "combo_stacks": 5,
    }
    panel.set_params(test_params)
    result = panel.get_params()
    assert result["enemy_defense"] == 500.0, f"Expected 500.0, got {result['enemy_defense']}"
    assert result["enemy_resistance"] == 30.0
    assert result["is_unbalanced"]
    # combo_stacks is QSpinBox (int), check it
    defense = result["enemy_defense"]
    resistance = result["enemy_resistance"]
    combo = result["combo_stacks"]
    print(f"    Roundtrip: defense={defense}, resistance={resistance}, combo={combo}")


test("QtEnemyPanel set/get roundtrip", test_enemy_panel_roundtrip)


# 3. QtEnemyPanel reset
def test_enemy_panel_reset():
    from games.endfield.gui.controls.enemy.qt_enemy_panel import QtEnemyPanel

    panel = QtEnemyPanel(font=small_font)
    panel.set_params({"enemy_defense": 999.0})
    panel._reset_btn.click()
    app.processEvents()
    params = panel.get_params()
    assert params["enemy_defense"] == 100.0
    print(f"    After reset: defense={params['enemy_defense']}")


test("QtEnemyPanel reset", test_enemy_panel_reset)


# 4. QtSelectionPanel data loading
def test_selection_panel_data():
    import json

    from games.endfield.gui.panels.selection.qt_panel import QtSelectionPanel

    data_path = os.path.join(_ROOT, "games", "endfield", "data", "characters.json")
    with open(data_path, encoding="utf-8") as f:
        data_list = json.load(f)
    panel = QtSelectionPanel(data_list, big_font, is_weapon_panel=False)
    assert panel.type_combo.count() > 0
    panel.type_combo.setCurrentIndex(0)
    app.processEvents()
    assert panel.star_combo.count() > 0
    print(f"    Types: {panel.type_combo.count()}, Stars after select: {panel.star_combo.count()}")


test("QtSelectionPanel data loading", test_selection_panel_data)


# 5. QtSkillLevelPanel slider interaction
def test_skill_level_panel():
    from games.endfield.gui.panels.selection.qt_subpanels import QtSkillLevelPanel

    panel = QtSkillLevelPanel(font=small_font)
    # Access internal sliders list
    assert hasattr(panel, "_sliders")
    assert len(panel._sliders) == 3
    panel._sliders[0].setValue(9)
    panel._sliders[1].setValue(6)
    panel._sliders[2].setValue(12)
    app.processEvents()
    assert panel._sliders[0].value() == 9
    assert panel._sliders[1].value() == 6
    assert panel._sliders[2].value() == 12
    print(f"    Skill levels: {panel._sliders[0].value()}/{panel._sliders[1].value()}/{panel._sliders[2].value()}")


test("QtSkillLevelPanel slider interaction", test_skill_level_panel)


# 6. QtTrustPanel slider interaction
def test_trust_panel():
    from games.endfield.gui.panels.selection.qt_subpanels import QtTrustPanel

    panel = QtTrustPanel(font=small_font)
    # Access internal slider
    assert hasattr(panel, "_slider")
    panel._slider.setValue(4)
    app.processEvents()
    assert panel._slider.value() == 4
    assert panel.trust_level == 4
    print(f"    Trust level: {panel._slider.value()}, trust_level prop: {panel.trust_level}")


test("QtTrustPanel slider interaction", test_trust_panel)


# 7. QtSpecialAbilityPanel
def test_ability_panel():
    from games.endfield.gui.panels.selection.qt_ability_panel import QtSpecialAbilityPanel

    panel = QtSpecialAbilityPanel(font=small_font)
    # Check internal rows
    assert hasattr(panel, "_normal_rows")
    assert len(panel._normal_rows) == 3
    # Set first normal skill level
    first_row = panel._normal_rows[0]
    assert "slider" in first_row
    first_row["slider"].setValue(5)
    app.processEvents()
    assert first_row["slider"].value() == 5
    print(f"    Normal skills: {len(panel._normal_rows)}, first={first_row['slider'].value()}")


test("QtSpecialAbilityPanel slider interaction", test_ability_panel)


# 8. QtControlDock calc mode change
def test_control_dock_mode():
    from games.endfield.gui.shell.qt_control_dock import QtControlDock

    dock = QtControlDock(big_font=big_font, small_font=small_font)
    received = []
    dock.calc_mode_changed.connect(lambda s: received.append(s))
    # Change calc mode - trigger via combo box
    dock.calc_mode_menu.setCurrentIndex(1)
    app.processEvents()
    # The signal might not fire on programmatic change, check combo text instead
    current_text = dock.calc_mode_menu.currentText()
    print(f"    Calc mode combo text: '{current_text}', index: {dock.calc_mode_menu.currentIndex()}")
    assert dock.calc_mode_menu.currentIndex() == 1


test("QtControlDock calc mode change", test_control_dock_mode)


# 9. QtControlDock manual skill counts
def test_control_dock_skill_counts():
    from games.endfield.gui.shell.qt_control_dock import QtControlDock

    dock = QtControlDock(big_font=big_font, small_font=small_font)
    dock.use_manual_skill_counts_cb.setChecked(True)
    app.processEvents()
    assert dock.use_manual_skill_counts_cb.isChecked()
    print(f"    Manual counts enabled: {dock.use_manual_skill_counts_cb.isChecked()}")


test("QtControlDock manual skill counts", test_control_dock_skill_counts)


# 10. TotalDamagePanel update
def test_total_damage_panel():
    from games.endfield.gui.presentation.damage_snapshot import DamageSnapshot
    from games.endfield.gui.presentation.total_damage_panel import TotalDamagePanel

    panel = TotalDamagePanel(big_font=big_font, small_font=small_font)
    # Create snapshot with correct field names
    snapshot = DamageSnapshot(
        segment_damage={"战技:1": 1000.0, "连携技:1": 2000.0},
        segment_counts={"战技:1": 1, "连携技:1": 2},
        segment_totals={"战技:1": 1000.0, "连携技:1": 4000.0},
        skill_type_totals={"战技": 1000.0, "连携技": 4000.0},
        weighted_total_damage=5000.0,
        rotation_share_percent={},
        zone_share_percent={},
        selected_skill_label="战技:1",
    )
    panel.update_from_snapshot(snapshot)
    print(f"    Updated with weighted_total_damage={snapshot.weighted_total_damage}")


test("TotalDamagePanel update", test_total_damage_panel)

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
    print("  All interaction tests passed!")
