# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""Wiki Scout provider 注册表。"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

importlib.import_module("tools.wiki_scout.providers")
from tools.wiki_scout.providers.base import BaseProvider
from tools.wiki_scout.registry import get_provider, list_providers


def test_builtin_providers_are_registered() -> None:
    names = set(list_providers())
    assert {"warfarin", "wjdlglr"} <= names


def test_get_provider_returns_base_provider_instance() -> None:
    provider = get_provider("warfarin")
    assert isinstance(provider, BaseProvider)
    assert provider.name == "warfarin"


def test_get_provider_rejects_unknown_name() -> None:
    with pytest.raises(KeyError):
        get_provider("does-not-exist")
