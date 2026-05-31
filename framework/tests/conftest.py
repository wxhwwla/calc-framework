#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""framework/ 测试 fixtures。"""

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parents[2]  # conftest → tests/ → framework/ → 仓库根
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


@pytest.fixture
def fixtures_dir() -> Path:
    return FIXTURES_DIR
