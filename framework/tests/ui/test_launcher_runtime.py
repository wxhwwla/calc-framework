# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""启动器 runtime 单元测试。"""

from __future__ import annotations

from pathlib import Path

from calc_framework.ui.launcher.runtime import (
    _restore_launcher_after_game_closed,
    argv_for_adapter,
    argv_for_calcpack,
    argv_for_tool,
    list_adapter_entries,
    repo_root,
)


class TestLauncherRuntime:
    def test_repo_root_exists(self) -> None:
        root = repo_root()
        assert (root / "scripts" / "main_launcher.py").is_file()
        assert (root / "framework" / "adapters").is_dir()

    def test_list_adapter_entries_non_empty(self) -> None:
        entries = list_adapter_entries()
        assert len(entries) >= 2
        ids = {e.adapter_id for e in entries}
        assert "endfield" in ids
        assert "arknights" in ids
        assert "wjdlglr" in ids

    def test_argv_for_full_app(self) -> None:
        entries = {e.adapter_id: e for e in list_adapter_entries()}
        root = repo_root()
        argv = argv_for_adapter(entries["endfield"], root)
        assert argv[-1].replace("\\", "/").endswith("games/endfield/main.py")

    def test_wjdlglr_registered_as_full_app(self) -> None:
        entries = {e.adapter_id: e for e in list_adapter_entries()}
        entry = entries["wjdlglr"]

        assert entry.has_full_app
        argv = argv_for_adapter(entry, repo_root())
        assert argv[-1].replace("\\", "/").endswith("games/wjdlglr/main.py")

    def test_argv_for_generic_adapter(self) -> None:
        entries = {e.adapter_id: e for e in list_adapter_entries()}
        if "card_rpg" not in entries:
            return
        argv = argv_for_adapter(entries["card_rpg"])
        assert "-m" in argv
        assert "calc_framework.launcher" in argv

    def test_argv_for_tools(self) -> None:
        root = repo_root()
        designer = argv_for_tool("designer", root)
        assert "main_dev_toolkit.py" in designer[-1]
        graph = argv_for_tool("graph_editor", root)
        assert graph[-1] == "calc_framework.graph_editor"

    def test_argv_for_calcpack(self, tmp_path: Path) -> None:
        pack = tmp_path / "demo.calcpack"
        pack.write_text("{}", encoding="utf-8")
        argv = argv_for_calcpack(pack)
        assert argv[-1] == str(pack.resolve())


class TestRestoreLauncherAfterGameClosed:
    def test_restores_live_launcher(self) -> None:
        class _LiveLauncher:
            _embedded_game_window = object()

            def __init__(self) -> None:
                self.raised = False
                self.activated = False

            def raise_(self) -> None:
                self.raised = True

            def activateWindow(self) -> None:
                self.activated = True

        launcher = _LiveLauncher()

        _restore_launcher_after_game_closed(launcher)

        assert launcher._embedded_game_window is None
        assert launcher.raised
        assert launcher.activated

    def test_ignores_already_deleted_qt_object(self) -> None:
        class _DeletedLauncher:
            _embedded_game_window = object()

            def raise_(self) -> None:
                raise RuntimeError("libshiboken: Internal C++ object (GameLauncherWindow) already deleted.")

            def activateWindow(self) -> None:
                raise AssertionError("已销毁的窗口不应再被激活")

        launcher = _DeletedLauncher()

        _restore_launcher_after_game_closed(launcher)

        assert launcher._embedded_game_window is None
