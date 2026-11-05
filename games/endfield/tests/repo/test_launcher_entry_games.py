# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""统一启动器 exe 的游戏路由（endfield / arknights / wjdlglr）。"""

from __future__ import annotations

import pytest
from release_bundle.launcher_entry import _build_parser
from release_bundle.release_layout import _launcher_readme


class TestLauncherEntryGames:
    def test_parser_accepts_all_three_games(self) -> None:
        parser = _build_parser()

        for game in ("endfield", "arknights", "wjdlglr"):
            args, _ = parser.parse_known_args(["--game", game])
            assert args.game == game

    def test_parser_rejects_unknown_game(self) -> None:
        parser = _build_parser()

        with pytest.raises(SystemExit):
            parser.parse_known_args(["--game", "unknown"])

    def test_release_readme_lists_wjdlglr(self) -> None:
        text = _launcher_readme(exe_version="0.0.0", package_version="0.0.0")

        assert "--game wjdlglr" in text
        assert "无尽的拉格朗日" in text
