# SPDX-License-Identifier: AGPL-3.0
from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from games.endfield.gui_design.controls.search.qt_search_browser import (
    RunInfo,
    ScoreInfo,
    format_clipboard_text,
    format_loadout_line,
    list_runs,
    list_scores,
    scan_search_output,
)


def _make_test_db(path: Path) -> None:
    """创建带测试数据的 SQLite 数据库。"""
    conn = sqlite3.connect(str(path))
    conn.execute(
        "CREATE TABLE IF NOT EXISTS runs ("
        "signature TEXT PRIMARY KEY, total_combinations INTEGER NOT NULL, status TEXT NOT NULL DEFAULT 'running')"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS processed ("
        "signature TEXT NOT NULL, combo_key TEXT NOT NULL, PRIMARY KEY (signature, combo_key))"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS scores ("
        "signature TEXT NOT NULL, combo_key TEXT NOT NULL, weapon_name TEXT NOT NULL, "
        "final_damage REAL NOT NULL, chest TEXT NOT NULL, gloves TEXT NOT NULL, "
        "accessory_a TEXT NOT NULL, accessory_b TEXT NOT NULL, "
        "PRIMARY KEY (signature, combo_key))"
    )
    conn.execute(
        "INSERT INTO runs (signature, total_combinations, status) VALUES (?, ?, ?)",
        ("sig-001", 1000, "completed"),
    )
    conn.execute(
        "INSERT INTO runs (signature, total_combinations, status) VALUES (?, ?, ?)",
        ("sig-002", 500, "cancelled"),
    )
    conn.execute("INSERT INTO processed (signature, combo_key) VALUES ('sig-001', 'k1')")
    conn.execute("INSERT INTO processed (signature, combo_key) VALUES ('sig-001', 'k2')")

    conn.execute(
        "INSERT INTO scores (signature, combo_key, weapon_name, final_damage, chest, gloves, accessory_a, accessory_b) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        ("sig-001", "top-0", "测试剑", 5000.0, "甲", "手", "A", "B"),
    )
    conn.execute(
        "INSERT INTO scores (signature, combo_key, weapon_name, final_damage, chest, gloves, accessory_a, accessory_b) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        ("sig-002", "top-0", "短刀", 3000.0, "轻甲", "快手", "C", "D"),
    )
    conn.commit()
    conn.close()


class TestScanSearchOutput(unittest.TestCase):
    def test_no_directory(self) -> None:
        result = scan_search_output(Path("/nonexistent/path"))
        self.assertEqual(result, [])

    def test_empty_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = scan_search_output(Path(tmp))
            self.assertEqual(result, [])

    def test_finds_db_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "full_search_20260529"
            run_dir.mkdir()
            db_path = run_dir / "search_runs.db"
            _make_test_db(db_path)
            result = scan_search_output(Path(tmp))
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0], db_path)

    def test_multiple_dirs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            for name in ["run_a", "run_b"]:
                d = Path(tmp) / name
                d.mkdir()
                _make_test_db(d / "search_runs.db")
            result = scan_search_output(Path(tmp))
            self.assertEqual(len(result), 2)


class TestListRuns(unittest.TestCase):
    def test_empty_db(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "empty.db"
            conn = sqlite3.connect(str(db))
            conn.execute(
                "CREATE TABLE IF NOT EXISTS runs ("
                "signature TEXT PRIMARY KEY, total_combinations INTEGER NOT NULL, status TEXT NOT NULL)"
            )
            conn.commit()
            conn.close()
            runs = list_runs(db)
            self.assertEqual(len(runs), 0)

    def test_no_file(self) -> None:
        runs = list_runs(Path("/nonexistent.db"))
        self.assertEqual(runs, [])

    def test_returns_run_info(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "test.db"
            _make_test_db(db)
            runs = list_runs(db)
            self.assertEqual(len(runs), 2)
            self.assertEqual(runs[0].signature, "sig-002")
            self.assertEqual(runs[0].status, "cancelled")
            self.assertEqual(runs[1].signature, "sig-001")
            self.assertEqual(runs[1].status, "completed")
            self.assertEqual(runs[1].processed_combinations, 2)
            self.assertEqual(runs[1].total_combinations, 1000)

    def test_bad_db_no_crash(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "bad.db"
            db.write_text("not a database")
            runs = list_runs(db)
            self.assertEqual(runs, [])


class TestListScores(unittest.TestCase):
    def test_no_file(self) -> None:
        scores = list_scores(Path("/nonexistent.db"), "sig-001")
        self.assertEqual(scores, [])

    def test_returns_scores(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "test.db"
            _make_test_db(db)
            scores = list_scores(db, "sig-001")
            self.assertEqual(len(scores), 1)
            self.assertEqual(scores[0].weapon_name, "测试剑")
            self.assertEqual(scores[0].final_damage, 5000.0)
            self.assertEqual(scores[0].chest, "甲")

    def test_bad_db_no_crash(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "bad.db"
            db.write_text("not a database")
            scores = list_scores(db, "sig-x")
            self.assertEqual(scores, [])


class TestScoreInfo(unittest.TestCase):
    def test_dataclass(self) -> None:
        si = ScoreInfo(weapon_name="剑", final_damage=100.0, chest="甲", gloves="手", accessory_a="A", accessory_b="B")
        self.assertEqual(si.weapon_name, "剑")

    def test_empty_loadout(self) -> None:
        si = ScoreInfo(weapon_name="", final_damage=0.0, chest="", gloves="", accessory_a="", accessory_b="")
        self.assertEqual(si.final_damage, 0.0)


class TestRunInfo(unittest.TestCase):
    def test_dataclass(self) -> None:
        ri = RunInfo(signature="sig", total_combinations=100, processed_combinations=50, status="completed", db_path="/p")
        self.assertEqual(ri.signature, "sig")
        self.assertEqual(ri.status, "completed")


class TestFormatLoadoutLine(unittest.TestCase):
    def test_full_line(self) -> None:
        si = ScoreInfo(weapon_name="剑", final_damage=5000.0, chest="甲", gloves="手", accessory_a="A", accessory_b="B")
        line = format_loadout_line(si)
        self.assertIn("剑", line)
        self.assertIn("5000.0", line)
        self.assertIn("甲", line)

    def test_empty_slots_omitted(self) -> None:
        si = ScoreInfo(weapon_name="剑", final_damage=100.0, chest="", gloves="手", accessory_a="", accessory_b="")
        line = format_loadout_line(si)
        self.assertIn("剑", line)
        self.assertIn("手", line)
        self.assertNotIn("配件A:", line)


class TestFormatClipboardText(unittest.TestCase):
    def test_empty(self) -> None:
        text = format_clipboard_text()
        self.assertEqual(text, "")

    def test_with_runs_and_scores(self) -> None:
        runs = [RunInfo("sig-1", 100, 50, "completed", "/p")]
        scores = [ScoreInfo("剑", 5000.0, "甲", "手", "A", "B")]
        text = format_clipboard_text(run_infos=runs, score_infos=scores, db_path="/p/test.db")
        self.assertIn("sig-1", text)
        self.assertIn("剑", text)
        self.assertIn("5000.0", text)
        self.assertIn("test.db", text)

    def test_with_db_path_only(self) -> None:
        text = format_clipboard_text(db_path="/tmp/db")
        self.assertIn("/tmp/db", text)
