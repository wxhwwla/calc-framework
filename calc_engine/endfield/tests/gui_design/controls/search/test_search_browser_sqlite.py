# SPDX-License-Identifier: AGPL-3.0
"""list_runs / list_scores SQLite 测试。"""

from __future__ import annotations

import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from games.endfield.gui_design.controls.search.qt_search_browser import (
    list_runs,
    list_scores,
    scan_search_output,
)


def _make_db(path: Path) -> None:
    conn = sqlite3.connect(str(path))
    conn.executescript("""
        CREATE TABLE runs (
            signature TEXT PRIMARY KEY,
            total_combinations INTEGER,
            status TEXT
        );
        CREATE TABLE processed (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            signature TEXT
        );
        CREATE TABLE scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            signature TEXT,
            weapon_name TEXT,
            final_damage REAL,
            chest TEXT,
            gloves TEXT,
            accessory_a TEXT,
            accessory_b TEXT
        );
        INSERT INTO runs VALUES ('sig-001', 1000, 'completed');
        INSERT INTO runs VALUES ('sig-002', 500, 'running');
        INSERT INTO processed (signature) VALUES ('sig-001');
        INSERT INTO processed (signature) VALUES ('sig-001');
        INSERT INTO scores VALUES (1, 'sig-001', '剑A', 5000.0, '甲1', '手1', 'A1', 'B1');
        INSERT INTO scores VALUES (2, 'sig-001', '剑B', 3000.0, '甲2', '手2', 'A2', 'B2');
    """)
    conn.commit()
    conn.close()


class TestListRuns:
    def test_file_not_found(self) -> None:
        result = list_runs(Path("/nonexistent/test.db"))
        assert result == []

    def test_empty_db(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "empty.db"
            sqlite3.connect(str(db)).close()
            result = list_runs(db)
            assert result == []

    def test_with_data(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "test.db"
            _make_db(db)
            result = list_runs(db)
            assert len(result) >= 1

    def test_sqlite_error_returns_empty(self) -> None:
        result = list_runs(Path(__file__))
        assert result == []


class TestListScores:
    def test_with_data(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "test.db"
            _make_db(db)
            result = list_scores(db, "sig-001")
            assert len(result) == 2
            assert result[0].weapon_name == "剑A"

    def test_no_scores(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "test.db"
            _make_db(db)
            result = list_scores(db, "sig-nonexistent")
            assert result == []

    def test_file_not_found(self) -> None:
        result = list_scores(Path("/nonexistent/test.db"), "sig")
        assert result == []

    def test_sqlite_error_returns_empty(self) -> None:
        result = list_scores(Path(__file__), "sig")
        assert result == []


class TestScanSearchOutput:
    def test_nonexistent_dir(self) -> None:
        result = scan_search_output(root=Path("/nonexistent"))
        assert result == []

    def test_with_db_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_dir = Path(tmp) / "run_001"
            db_dir.mkdir()
            db = db_dir / "search_runs.db"
            _make_db(db)
            result = scan_search_output(root=Path(tmp))
            assert len(result) >= 1
