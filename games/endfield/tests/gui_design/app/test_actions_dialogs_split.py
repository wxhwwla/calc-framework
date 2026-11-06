# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""P2-07：``endfield_actions`` 拆分后的结构门禁与对话框行为契约。

对话框/工具方法抽到 ``ActionsDialogsMixin`` 后，``ActionsMixin`` 必须继续
暴露原有方法；这些测试同时锁定行数预算，防止结构债回流。
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from games.endfield.gui import endfield_actions
from games.endfield.gui.endfield_actions import ActionsMixin


class _StubApp(ActionsMixin):
    """最小应用桩：只提供对话框方法读取的属性。"""

    def __init__(self) -> None:
        self.control_dock = MagicMock()
        self.char_panel = MagicMock()
        self.weapon_panel = MagicMock()
        self._current_calc_mode = "zone_snapshot"
        self._equipment_catalog: dict = {}
        self._enemy_defense = 100.0
        self._enemy_resistance = 0.0
        self._ignore_resistance = 0.0
        self._imbalance_vulnerability_coeff = 1.3
        self._is_unbalanced = False
        self._is_true_damage = False
        self.status_label = MagicMock()


def test_endfield_actions_stays_within_line_budget() -> None:
    """拆分后主模块回到 400 行目标以内。"""
    path = Path(endfield_actions.__file__)
    assert len(path.read_text(encoding="utf-8").splitlines()) <= 400


def test_actions_mixin_inherits_dialogs_mixin() -> None:
    """对话框方法抽到独立 mixin 后仍由 ActionsMixin 统一暴露。"""
    from games.endfield.gui.endfield_actions_dialogs import ActionsDialogsMixin

    assert issubclass(ActionsMixin, ActionsDialogsMixin)


def test_attribution_uses_shared_summary_text() -> None:
    from games.endfield.gui import endfield_actions_dialogs

    app = _StubApp()
    with patch.object(endfield_actions_dialogs, "QMessageBox") as message_box:
        app._on_attribution()

    message_box.about.assert_called_once()
    assert message_box.about.call_args.args[2] == endfield_actions_dialogs.SUMMARY_TEXT


def test_donation_opens_shared_dialog() -> None:
    from games.endfield.gui import endfield_actions_dialogs

    app = _StubApp()
    with patch.object(endfield_actions_dialogs, "open_donation_dialog") as opener:
        app._on_donation()

    opener.assert_called_once_with(app)


def test_export_preset_writes_file_and_reports_success(tmp_path: Path) -> None:
    from games.endfield.gui import endfield_actions_dialogs

    app = _StubApp()
    loadout = SimpleNamespace(to_loadout_preset=lambda: object())
    target = tmp_path / "preset.json"

    with (
        patch.object(endfield_actions_dialogs, "read_loadout_from_panels", return_value=loadout),
        patch.object(endfield_actions_dialogs, "QFileDialog") as file_dialog,
        patch(
            "games.endfield.gui.app.loadout_preset.export_preset_json",
            return_value='{"ok": true}',
        ),
    ):
        file_dialog.getSaveFileName.return_value = (str(target), "JSON (*.json)")
        app._on_export_preset()

    assert target.read_text(encoding="utf-8") == '{"ok": true}'
    app.status_label.setText.assert_called_once()
