# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""Wiki Scout CLI — 数据源列表与错误路径。"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from tools.wiki_scout.cli import main


def test_cli_list_prints_registered_providers(capsys) -> None:
    assert main(["list"]) == 0

    out = capsys.readouterr().out
    assert "warfarin" in out
    assert "wjdlglr" in out


def test_cli_unknown_provider_returns_error(tmp_path: Path, capsys) -> None:
    assert main(["run", "not-a-provider", "--out-dir", str(tmp_path)]) == 1

    err = capsys.readouterr().err
    assert "未知 provider" in err
