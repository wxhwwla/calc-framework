# SPDX-License-Identifier: AGPL-3.0
"""pytest 全局夹具 — 路径设置与样本数据。

TODO: 将 _template 替换为实际游戏名，更新 _ADAPTER_DIR / _GAME_DIR 路径。
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[4] / ".." / ".."
_FRAMEWORK_SRC = _REPO_ROOT / "framework" / "src"
_GAME_DIR = _REPO_ROOT / "games" / "_template"
_ADAPTER_DIR = _REPO_ROOT / "framework" / "adapters" / "_template"

if str(_FRAMEWORK_SRC) not in sys.path:
    sys.path.insert(0, str(_FRAMEWORK_SRC))
if str(_GAME_DIR) not in sys.path:
    sys.path.insert(0, str(_GAME_DIR))


@pytest.fixture
def adapter_dir() -> Path:
    """返回适配器目录路径。"""
    return _ADAPTER_DIR


@pytest.fixture
def game_dir() -> Path:
    """返回游戏包目录路径。"""
    return _GAME_DIR


@pytest.fixture
def sample_character() -> dict:
    """示例角色数据 — 占位用。

    TODO: 替换为实际游戏角色数据结构。
    """
    return {
        "name": "TemplateCharacter",
        "atk": 100,
        "def": 50,
        "hp": 1000,
        "trust_atk": 10,
        "potential_atk": 5,
    }
