#!/usr/bin/env python3
"""pytest 全局夹具：缓存清理、慢测/集成测分层、收集阶段跳过重型模块。"""

from __future__ import annotations

import sys
from collections.abc import Generator
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

_INTEGRATION_FILES: frozenset[str] = frozenset()

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


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:  # noqa: ARG001
    """为慢测模块自动打 slow 标记（全量收集时生效）。"""
    for item in items:
        rel = item.path.relative_to(Path(__file__).resolve().parent).as_posix()
        if rel in _SLOW_FILES:
            item.add_marker(pytest.mark.slow)


@pytest.fixture(autouse=True)
def _reset_global_calculation_cache() -> Generator[None, None, None]:
    """每条用例前后清空全局结果缓存，避免跨测堆积大对象。"""
    reset_global_result_cache()
    yield
    reset_global_result_cache()


# === from fixtures/path_roots.py ===
"""测试用仓库路径（任意深度子目录均可 import）。"""

PKG_ROOT = _PKG_ROOT
REPO_ROOT = _REPO_ROOT
TOOLS_ROOT = _TOOLS_ROOT


# === from fixtures/gui_fixtures.py ===
"""GUI 测试夹具：MockSelectionPanel（CTk 已移除）。"""

import json
from types import SimpleNamespace
from typing import Any

_CHARACTERS_JSON = PKG_ROOT / "character_weapon_equipment" / "character_data" / "characters.json"
_WEAPONS_JSON = PKG_ROOT / "character_weapon_equipment" / "weapon_data" / "weapons.json"


def load_character_by_name(name: str) -> dict[str, Any]:
    with _CHARACTERS_JSON.open(encoding="utf-8") as f:
        for row in json.load(f):
            if row.get("名称") == name:
                return row
    raise KeyError(name)


def load_weapon_by_name(name: str) -> dict[str, Any]:
    with _WEAPONS_JSON.open(encoding="utf-8") as f:
        for row in json.load(f):
            if row.get("名称") == name:
                return row
    raise KeyError(name)


class MockSelectionPanel:
    """模拟 ChooseTypesStarsNamesLevels 的最小接口。"""

    def __init__(
        self,
        data: dict[str, Any],
        *,
        level: int = 1,
        trust: int = 0,
        skills: tuple[int, int, int] = (1, 0, 0),
    ) -> None:
        self._data = data
        self.selected_level = _StrVar(str(level))
        self.selected_type = _StrVar(str(data.get("类型", "")))
        self.selected_star = _StrVar(str(data.get("星级", "")))
        self.selected_name = _StrVar(str(data.get("名称", "")))
        self.trust_panel = SimpleNamespace(trust_level=_StrVar(str(trust)))
        self._show_advanced_params_var = _BoolVar(False)
        self.skill_level_panel = SimpleNamespace(
            skill_1_level=_StrVar(str(skills[0])),
            skill_2_level=_StrVar(str(skills[1])),
            skill_3_level=_StrVar(str(skills[2])),
        )
        self.list_c_w = [data]

    def get_selected_data(self) -> dict[str, Any] | None:
        name = (self.selected_name.get() or "").strip()
        for row in self.list_c_w:
            if str(row.get("名称", "")) == name:
                return row
        return self._data

    def get_level(self) -> int:
        return int(self.selected_level.get())

    def get_trust_level(self) -> int:
        return int(self.trust_panel.trust_level.get())

    def get_skill_1_level(self) -> int:
        return int(self.skill_level_panel.skill_1_level.get())

    def get_skill_2_level(self) -> int:
        return int(self.skill_level_panel.skill_2_level.get())

    def get_skill_3_level(self) -> int:
        return int(self.skill_level_panel.skill_3_level.get())

    def get_special_ability_1_name(self) -> str:
        return ""

    def get_special_ability_1_level(self) -> int:
        return 0

    def get_special_ability_2_name(self) -> str:
        return ""

    def get_special_ability_2_level(self) -> int:
        return 0

    def get_special_ability_3_name(self) -> str:
        return ""

    def get_special_ability_3_level(self) -> int:
        return 0

    def get_weapon_special_name(self) -> str:
        return ""

    def get_weapon_special_level(self) -> int:
        return 1

    def get_weapon_special_stack(self) -> int:
        return 0

    def get_weapon_special_2_name(self) -> str:
        return ""

    def get_weapon_special_2_level(self) -> int:
        return 1

    def get_weapon_special_2_stack(self) -> int:
        return 0

    def _refresh_advanced_params_visibility(self) -> None:
        """测试替身：真实面板会刷新折叠显隐，这里无需动作。"""
        return None


class _StrVar:
    def __init__(self, value: str) -> None:
        self._value = value

    def get(self) -> str:
        return self._value

    def set(self, value: str) -> None:
        self._value = value


class _BoolVar:
    def __init__(self, value: bool) -> None:
        self._value = bool(value)

    def get(self) -> bool:
        return self._value

    def set(self, value: bool) -> None:
        self._value = bool(value)




def ctk_available() -> bool:
    """CTk 已移除，始终返回 False。"""
    return False
