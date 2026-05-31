# SPDX-License-Identifier: AGPL-3.0
from __future__ import annotations

from unittest.mock import MagicMock

from games.endfield.gui_design.shared.calc_history import (
    CalculationHistory,
    HistoryEntry,
    get_app_calculation_history,
)


class TestCalculationHistory:
    def test_empty_history(self) -> None:
        h = CalculationHistory(max_entries=5)
        assert h.list_entries() == ()

    def test_push_and_list(self) -> None:
        h = CalculationHistory(max_entries=5)
        e1 = HistoryEntry(label="a", summary="s1", preset_snapshot={"x": 1})
        e2 = HistoryEntry(label="b", summary="s2", preset_snapshot={"y": 2})
        h.push(e1)
        h.push(e2)
        entries = h.list_entries()
        assert len(entries) == 2
        assert entries[0].label == "b"
        assert entries[1].label == "a"

    def test_max_entries_enforced(self) -> None:
        h = CalculationHistory(max_entries=2)
        for i in range(5):
            h.push(HistoryEntry(label=str(i), summary="", preset_snapshot={}))
        assert len(h.list_entries()) == 2
        assert h.list_entries()[0].label == "4"
        assert h.list_entries()[1].label == "3"

    def test_get_snapshot_out_of_bounds(self) -> None:
        h = CalculationHistory(max_entries=3)
        assert h.get_snapshot(0) is None
        assert h.get_snapshot(-1) is None
        assert h.get_snapshot(99) is None

    def test_get_snapshot_valid(self) -> None:
        h = CalculationHistory(max_entries=3)
        h.push(HistoryEntry(label="x", summary="s", preset_snapshot={"key": "val"}))
        snap = h.get_snapshot(0)
        assert snap == {"key": "val"}

    def test_get_snapshot_returns_copy(self) -> None:
        h = CalculationHistory(max_entries=3)
        inner = {"mutable": [1, 2]}
        h.push(HistoryEntry(label="x", summary="s", preset_snapshot=inner))
        snap = h.get_snapshot(0)
        snap["new"] = "added"
        assert "new" not in inner


class TestGetAppCalculationHistory:
    def test_creates_if_missing(self) -> None:
        app = MagicMock(spec=[])
        history = get_app_calculation_history(app)
        assert history is not None
        assert history.list_entries() == ()

    def test_returns_existing(self) -> None:
        app = MagicMock(spec=[])
        h1 = get_app_calculation_history(app)
        h2 = get_app_calculation_history(app)
        assert h1 is h2
