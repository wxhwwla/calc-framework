from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from games.endfield.gui_design.shared.ui_preferences import (
    STARTUP_MODE_ALWAYS_MAIN,
    STARTUP_MODE_REMEMBER_LAST,
    _default_preferences,
    _preferences_path,
    load_ui_preferences,
    record_char_advanced_expanded,
    record_last_page,
    record_weapon_advanced_expanded,
    resolve_startup_page,
    save_ui_preferences,
)


class TestPreferencesPath:
    def test_with_base_dir(self) -> None:
        path = _preferences_path(base_dir=Path("/tmp/test"))
        assert "ui_preferences.json" in str(path)


class TestDefaultPreferences:
    def test_returns_dict(self) -> None:
        d = _default_preferences()
        assert d["startup_page_mode"] == STARTUP_MODE_ALWAYS_MAIN


class TestSaveLoadRoundTrip:
    def test_save_then_load(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pref = {"startup_page_mode": STARTUP_MODE_REMEMBER_LAST, "last_page": "高级页", "char_advanced_expanded": False, "weapon_advanced_expanded": True}
            save_ui_preferences(pref, base_dir=Path(tmp))
            loaded = load_ui_preferences(base_dir=Path(tmp))
            assert loaded["startup_page_mode"] == STARTUP_MODE_REMEMBER_LAST
            assert loaded["last_page"] == "高级页"

    def test_load_corrupted_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "ui_preferences.json"
            p.write_text("{invalid")
            loaded = load_ui_preferences(base_dir=Path(tmp))
            assert loaded == _default_preferences()

    def test_load_non_dict_data(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "ui_preferences.json"
            p.write_text('"string"')
            loaded = load_ui_preferences(base_dir=Path(tmp))
            assert loaded == _default_preferences()

    def test_load_invalid_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "ui_preferences.json"
            p.write_text(json.dumps({"startup_page_mode": "invalid", "last_page": "计算页"}))
            loaded = load_ui_preferences(base_dir=Path(tmp))
            assert loaded["startup_page_mode"] == STARTUP_MODE_ALWAYS_MAIN

    def test_load_invalid_page(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "ui_preferences.json"
            p.write_text(json.dumps({"startup_page_mode": STARTUP_MODE_ALWAYS_MAIN, "last_page": "不存在"}))
            loaded = load_ui_preferences(base_dir=Path(tmp))
            assert loaded["last_page"] == "计算页"

    def test_load_missing_expanded_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "ui_preferences.json"
            p.write_text(json.dumps({"startup_page_mode": STARTUP_MODE_ALWAYS_MAIN, "last_page": "计算页"}))
            loaded = load_ui_preferences(base_dir=Path(tmp))
            assert loaded["char_advanced_expanded"] is True

    def test_save_write_error_silent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "subdir" / "ui_preferences.json"
            with patch("games.endfield.gui_design.shared.ui_preferences._preferences_path", return_value=path):
                save_ui_preferences({"startup_page_mode": "always_main"})


class TestResolveStartupPage:
    def test_always_main(self) -> None:
        pref = {"startup_page_mode": STARTUP_MODE_ALWAYS_MAIN, "last_page": "高级页"}
        assert resolve_startup_page(pref) == "计算页"

    def test_remember_last_valid(self) -> None:
        pref = {"startup_page_mode": STARTUP_MODE_REMEMBER_LAST, "last_page": "高级页"}
        assert resolve_startup_page(pref) == "高级页"

    def test_remember_last_invalid(self) -> None:
        pref = {"startup_page_mode": STARTUP_MODE_REMEMBER_LAST, "last_page": "不存在"}
        assert resolve_startup_page(pref) == "计算页"


class TestRecordLastPage:
    def test_valid_page(self) -> None:
        pref = {"startup_page_mode": "x", "last_page": "计算页"}
        updated = record_last_page(pref, page="高级页")
        assert updated["last_page"] == "高级页"
        assert pref["last_page"] == "计算页"

    def test_invalid_page_normalizes(self) -> None:
        pref = {"startup_page_mode": "x", "last_page": "计算页"}
        updated = record_last_page(pref, page="不存在")
        assert updated["last_page"] == "计算页"


class TestRecordCharAdvancedExpanded:
    def test_updates(self) -> None:
        pref = {"char_advanced_expanded": True}
        updated = record_char_advanced_expanded(pref, expanded=False)
        assert updated["char_advanced_expanded"] is False


class TestRecordWeaponAdvancedExpanded:
    def test_updates(self) -> None:
        pref = {"weapon_advanced_expanded": False}
        updated = record_weapon_advanced_expanded(pref, expanded=True)
        assert updated["weapon_advanced_expanded"] is True
