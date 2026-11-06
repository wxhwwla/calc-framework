# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""P2-07：``SearchRunStore`` 拆分后的结构与身份门禁。"""

from __future__ import annotations

import importlib
from pathlib import Path

_STORE_MODULES = (
    "games.endfield.calc.search.persist.store",
    "games.endfield.calc.search.persist.store_records",
)


def _line_count(module_name: str) -> int:
    module = importlib.import_module(module_name)
    module_file = module.__file__
    assert module_file is not None
    return len(Path(module_file).read_text(encoding="utf-8").splitlines())


def test_store_module_stays_within_target() -> None:
    for module_name in _STORE_MODULES:
        assert _line_count(module_name) <= 400, module_name


def test_store_reexports_the_records_class() -> None:
    from games.endfield.calc.search.persist import store, store_records

    assert store.SearchRunStore is store_records.SearchRunStore
    assert store_records.SearchRunStore.__module__ == store_records.__name__
