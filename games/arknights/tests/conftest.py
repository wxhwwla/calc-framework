# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""pytest 全局夹具：路径设置、样本干员数据。"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest


def pytest_configure(config: pytest.Config) -> None:
    """注册自定义标记。"""
    config.addinivalue_line("markers", "integration: 依赖外部系统（文件 I/O、DB）的测试")
    config.addinivalue_line("markers", "real_data: 使用真实游戏 JSON 数据的测试")


_REPO_ROOT = Path(__file__).resolve().parents[3]
_FRAMEWORK_SRC = _REPO_ROOT / "framework" / "src"
_GAMES_ARKNIGHTS = _REPO_ROOT / "games" / "arknights"
_ADAPTER_DIR = _REPO_ROOT / "framework" / "adapters" / "arknights"
_PARSED_DIR = _REPO_ROOT / "tools" / "arknights_scout" / "output" / "parsed"

if str(_FRAMEWORK_SRC) not in sys.path:
    sys.path.insert(0, str(_FRAMEWORK_SRC))
if str(_GAMES_ARKNIGHTS) not in sys.path:
    sys.path.insert(0, str(_GAMES_ARKNIGHTS))


@pytest.fixture
def adapter_dir() -> Path:
    return _ADAPTER_DIR


@pytest.fixture
def parsed_dir() -> Path:
    return _PARSED_DIR


@pytest.fixture
def amiya_operator() -> dict:
    return {
        "名称": "阿米娅",
        "星级": 5,
        "职业": "术师",
        "分支": "中坚术师",
        "基础属性": {
            "hp": 958,
            "atk": 390,
            "def": 81,
            "res": 10,
            "attack_interval": 1.6,
            "block": 1,
            "deploy_cost": 18,
        },
        "信赖加成": {"攻击": 70, "生命": 200},
        "天赋": [],
        "技能": [],
        "潜能": ["生命上限+200", "部署费用-1", "攻击力+30"],
    }


@pytest.fixture
def minimal_operator() -> dict:
    return {
        "名称": "Test",
        "星级": 1,
        "职业": "先锋",
        "基础属性": {"atk": 100, "def": 50},
    }
