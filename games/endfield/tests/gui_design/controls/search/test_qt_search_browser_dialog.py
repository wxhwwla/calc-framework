# SPDX-License-Identifier: AGPL-3.0
"""SearchHistoryDialog Qt 控件测试。"""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from games.endfield.gui.controls.search.qt_search_browser import SearchHistoryDialog, _human_size
from PySide6.QtCore import QCoreApplication
from PySide6.QtWidgets import QApplication


def _app() -> QApplication | QCoreApplication:
    inst = QApplication.instance()

    if inst is None:
        inst = QApplication([])

    return inst


class TestHumanSize:
    def test_bytes(self) -> None:
        assert _human_size(Path(__file__)).endswith("B")

    def test_kilobytes(self) -> None:
        size = _human_size(Path(__file__))

        assert "KB" in size or "B" in size


class TestSearchHistoryDialog:
    def test_create_empty(self) -> None:
        _app()

        with patch("games.endfield.gui.controls.search.qt_search_browser.scan_search_output", return_value=[]):
            dialog = SearchHistoryDialog(big_font=MagicMock(), small_font=MagicMock())

            assert "搜索历史" in dialog.windowTitle()

            dialog.close()

    def test_create_with_db(self) -> None:
        _app()

        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "search_runs.db"

            db_path.write_text("")

            def fake_scan() -> list[Path]:
                return [db_path]

            def fake_list_runs(p: Path) -> list:
                from games.endfield.gui.controls.search.qt_search_browser import RunInfo

                return [RunInfo("sig-001", 1000, 500, "completed", str(p))]

            def fake_list_scores(p: Path, sig: str) -> list:
                from games.endfield.gui.controls.search.qt_search_browser import ScoreInfo

                return [ScoreInfo("测试剑", 5000.0, "甲", "手", "A", "B")]

            _MOD = "games.endfield.gui.controls.search.qt_search_browser"
            with (
                patch(f"{_MOD}.scan_search_output", side_effect=fake_scan),
                patch(f"{_MOD}.list_runs", side_effect=fake_list_runs),
                patch(f"{_MOD}.list_scores", side_effect=fake_list_scores),
            ):
                dialog = SearchHistoryDialog(big_font=MagicMock(), small_font=MagicMock())

                assert dialog._tree.topLevelItemCount() >= 1

                dialog.close()
