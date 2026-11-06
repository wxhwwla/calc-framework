# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""确认计算时 ComputeSheet 使用完整适配器上下文的回归测试。

P0-01 验收要求：点击确认后乘区表必须成功求值。此前的实现传入
``base_context={}``，DAG 在 ``computed.主能力平值加算`` 处直接抛错。
"""

from __future__ import annotations

from unittest.mock import patch

import pytest
from games.endfield.calc.loadout.slot_search import FixedLoadoutSelection
from games.endfield.framework_bridge import ComputeSheet as BridgeComputeSheet
from games.endfield.gui import endfield_actions
from games.endfield.gui.app.loadout_evaluation import build_snapshot_from_loadout
from games.endfield.gui.app.loadout_state import read_loadout_from_panels
from games.endfield.gui.endfield_actions import ActionsMixin
from games.endfield.tests.conftest import (
    MockSelectionPanel,
    load_character_by_name,
    load_weapon_by_name,
)


class _CapturingSheet(BridgeComputeSheet):
    """记录构造参数与最后一次求值结果的真实 ComputeSheet。"""

    captured: _CapturingSheet | None = None

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        type(self).captured = self
        self.last_result = None

    def evaluate(self):
        self.last_result = super().evaluate()
        return self.last_result


class _StubApp(ActionsMixin):
    def __init__(self) -> None:
        from PySide6.QtWidgets import QWidget

        self._compute_sheet_widget = QWidget()
        self._total_damage_panel = QWidget()
        self._equipment_catalog: dict = {}

    def _on_compute_sheet_evaluated(self, result=None) -> None:
        return None


@pytest.fixture(scope="module", autouse=True)
def qapp():
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    yield app


def _loadout():
    loadout = read_loadout_from_panels(
        MockSelectionPanel(load_character_by_name("伊冯"), skills=(8, 8, 8)),
        MockSelectionPanel(load_weapon_by_name("佩科5")),
        calculation_mode="zone_snapshot",
        weapon_scope_label="当前武器",
        equipment_scope_label="全部装备",
        fixed_loadout=FixedLoadoutSelection(),
        use_manual_multi_skill_counts=False,
        manual_counts={"战技": 1, "连携技": 0, "终结技": 0},
        physical_abnormal_counts={},
        spell_abnormal_counts={},
        damage_component_mode="skill_and_abnormal",
        use_expected_crit=False,
        include_conditional_equipment_crit=False,
        extra_crit_rate=0.0,
        extra_crit_damage=0.0,
        enemy_defense=100.0,
        enemy_resistance=0.0,
        ignore_resistance=0.0,
        imbalance_vulnerability_coeff=1.3,
        is_unbalanced=False,
        is_true_damage=False,
        enemy_tier="普通",
        combo_stacks=0,
        attached_effect_multiplier=1.0,
        corrosion_duration_seconds=15.0,
        imbalance_efficiency_bonus=0.0,
    )
    assert loadout is not None
    return loadout


def _refresh(loadout) -> _CapturingSheet:
    _CapturingSheet.captured = None
    app = _StubApp()
    with patch.object(endfield_actions, "ComputeSheet", _CapturingSheet):
        app._refresh_compute_sheet(loadout)
    sheet = _CapturingSheet.captured
    assert sheet is not None
    # 保持宿主窗口存活，否则 QWidget 随 app 被回收后控件句柄失效
    sheet._test_app = app  # type: ignore[attr-defined]
    return sheet


class TestRefreshComputeSheetContext:
    def test_uses_full_adapter_context_and_evaluates(self):
        sheet = _refresh(_loadout())

        assert sheet._base_context["computed"]["主能力平值加算"] > 0
        assert sheet.last_result is not None
        assert sheet.last_result.outputs["最终攻击力"] > 0
        assert sheet.last_result.outputs["最终伤害"] > 0

    def test_final_damage_matches_confirmed_snapshot(self):
        loadout = _loadout()

        sheet = _refresh(loadout)
        snapshot = build_snapshot_from_loadout(loadout)

        assert sheet.last_result.outputs["最终伤害"] == pytest.approx(snapshot.weighted_total_damage)

    def test_input_widgets_seeded_from_confirmed_loadout(self):
        loadout = _loadout()

        sheet = _refresh(loadout)

        values = sheet.read_user_inputs()
        assert values["user_input.敌人防御"] == pytest.approx(loadout.enemy_defense)
        assert values["user_input.敌人抗性"] == pytest.approx(loadout.enemy_resistance)
        assert values["user_input.是否失衡"] == loadout.is_unbalanced

    def test_resistance_widget_drives_dag_zone(self):
        sheet = _refresh(_loadout())

        slider, _spec = sheet._input_widgets["user_input.敌人抗性"]
        slider.setValue(20)

        result = sheet.evaluate()

        assert result.outputs["抗性区"] == pytest.approx(0.8)

    def test_defense_widget_drives_dag_zone(self):
        sheet = _refresh(_loadout())

        spin, _spec = sheet._input_widgets["user_input.敌人防御"]
        spin.setValue(300)

        result = sheet.evaluate()

        assert result.outputs["防御区"] == pytest.approx(0.25)
