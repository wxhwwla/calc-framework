#!/usr/bin/env python3
"""pytest 全局夹具：缓存清理、慢测/集成测分层、收集阶段跳过重型模块。"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_PKG_ROOT = Path(__file__).resolve().parent.parent
_REPO_ROOT = _PKG_ROOT.parent
_TOOLS_ROOT = _REPO_ROOT / "tools"
if str(_TOOLS_ROOT) not in sys.path:
    sys.path.insert(0, str(_TOOLS_ROOT))
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from calculation.core.result_cache import reset_global_result_cache

_INTEGRATION_FILES = frozenset(
    {
        "gui_design/presentation/test_property_display_integration.py",
        "gui_design/controls/test_enhancement_integration.py",
        "gui_design/shell/test_gui_app_integration.py",
        "gui_design/controls/test_fixed_loadout_integration.py",
    }
)

_SLOW_FILES = frozenset(
    {
        "calculation/damage/test_calculation.py",
        "calculation/damage/test_inverse_refactored.py",
        "calculation/damage/test_scaling_mode.py",
        "calculation/damage/test_decimal_scaling.py",
        "tools/test_wiki_sync.py",
    }
)


def _markexpr(config: pytest.Config) -> str:
    return (config.getoption("-m") or "").replace(" ", "").replace("_", "").lower()


def pytest_configure(config: pytest.Config) -> None:
    """带 ``-m 'not integration'`` 等时，收集阶段直接 --ignore 重型文件（避免 import CTk）。"""
    expr = _markexpr(config)
    if not expr:
        return
    tests_dir = Path(__file__).resolve().parent
    ignore: list[str] = list(config.option.ignore or [])
    if "notintegration" in expr:
        ignore.extend(str(tests_dir / name) for name in _INTEGRATION_FILES)
    if "notrealdata" in expr:
        pass
    if "notslow" in expr:
        ignore.extend(str(tests_dir / name) for name in _SLOW_FILES)
    if ignore:
        config.option.ignore = ignore


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """为慢测模块自动打 slow 标记（全量收集时生效）。"""
    for item in items:
        rel = item.path.relative_to(Path(__file__).resolve().parent).as_posix()
        if rel in _SLOW_FILES:
            item.add_marker(pytest.mark.slow)


@pytest.fixture(autouse=True)
def _reset_global_calculation_cache() -> None:
    """每条用例前后清空全局结果缓存，避免跨测堆积大对象。"""
    reset_global_result_cache()
    yield
    reset_global_result_cache()
