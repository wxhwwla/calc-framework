# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""无尽的拉格朗日适配器测试共用常量与 DAG 上下文构造。

测试文件拆分后由 ``test_wjdlglr_adapter.py``（结构/数据契约）与
``test_wjdlglr_calc.py``（乘区求值）共享；本模块不以 ``test_`` 开头，
pytest 不会收集。
"""

from __future__ import annotations

from pathlib import Path

_ADAPTER_DIR = Path(__file__).resolve().parents[2] / "adapters" / "wjdlglr"

_TARGETS: tuple[tuple[str, str], ...] = (
    ("fighter", "战机"),
    ("escort", "护航艇"),
    ("drone", "无人机"),
    ("landing", "登陆舰(作业态)"),
    ("frigate", "护卫舰"),
    ("destroyer", "驱逐舰"),
    ("cruiser", "巡洋舰"),
    ("battlecruiser", "战列巡洋舰"),
    ("battleship", "战列舰"),
    ("carrier", "航空母舰"),
    ("support", "支援舰"),
    ("engineering_small", "小型工程舰"),
    ("engineering_medium", "中型工程舰"),
    ("engineering_large", "大型工程舰"),
    ("base_ship", "大本营船"),
    ("base", "基地"),
)

_WEAPON_FIELDS = {
    "weapon_count",
    "ammo_count",
    "attack_runs",
    "base_cooldown",
    "base_duration",
    "outbound",
    "inbound",
    "base_damage",
    "needs_mothership",
    "friendly",
    "is_energy",
    "crit_rate",
    "crit_damage",
    "crit_vs_air",
    *(f"hit_{key}" for key, _ in _TARGETS),
}

_DPM_KEYS = {f"最终每分钟伤害_{label}" for _, label in _TARGETS}


def _weapon(**overrides: float) -> dict[str, float]:
    base = {
        "weapon_count": 3.0,
        "ammo_count": 4.0,
        "attack_runs": 5.0,
        "base_cooldown": 10.0,
        "base_duration": 20.0,
        "outbound": 3.0,
        "inbound": 2.0,
        "base_damage": 100.0,
        "needs_mothership": 1.0,
        "friendly": 0.0,
        "is_energy": 0.0,
        "crit_rate": 50.0,
        "crit_damage": 200.0,
        "crit_vs_air": 0.0,
        **{f"hit_{key}": 0.0 for key, _ in _TARGETS},
        "hit_fighter": 22.0,
        "hit_frigate": 85.0,
    }
    base.update(overrides)
    return base


def _user(**overrides: float) -> dict[str, float]:
    base = {
        "fleet_count": 2.0,
        "self_flight_bonus": 10.0,
        "mothership_flight_bonus": 20.0,
        "self_cooldown_bonus": 10.0,
        "mothership_cooldown_bonus": 20.0,
        "self_duration_bonus": 5.0,
        "mothership_duration_bonus": 15.0,
        "bonus_crit_rate": 20.0,
        "crit_multiplier_bonus": 10.0,
        "damage_bonus": 20.0,
        "physical_armor": 30.0,
        "energy_armor": 50.0,
    }
    base.update(overrides)
    return base


def _context(
    weapon: dict[str, float] | None = None,
    user: dict[str, float] | None = None,
) -> dict[str, dict[str, float]]:
    return {"weapon": _weapon(**(weapon or {})), "user_input": _user(**(user or {}))}
