# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""P3-01 搜索性能基准的固定配置、数据模型与作业组装。

固定基线：伊冯 / 佩科5 / 战技 / 物理 / 90 级 / 信赖 4 / 敌方防御 100 /
当前武器 / 全部装备 / TopN=10。装备剪枝后目录为 24×23×42，
单武器即 973,728 组合。
"""

from __future__ import annotations

import json
import math
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from games.endfield.calc.loadout.optimizer import OptimizerConfig
from games.endfield.calc.loadout.optimizer.plan import build_optimizer_search_plan
from games.endfield.calc.search.evaluate.context import SearchEvalContext
from games.endfield.calc.search.plan.controller import optimizer_config_for_search_job
from games.endfield.calc.search.plan.job import SingleSkillSearchJob, prepare_single_skill_search_job
from games.endfield.data_loading.equipment_catalog import get_equipment_catalog
from games.endfield.data_loading.loader import get_characters, get_weapons
from utils.game_data_paths import ENDFIELD_DATA_VERSION_JSON

__all__ = [
    "ALL_MODES",
    "EXPECTED_COMBINATIONS",
    "EXPECTED_DATA_VERSION",
    "MODE_PYTHON",
    "MODE_RUST_FULL",
    "MODE_RUST_SOA",
    "BenchmarkError",
    "BenchmarkRun",
    "BenchmarkSetup",
    "CancelResumeReport",
    "TopResult",
    "build_setup",
]

EXPECTED_DATA_VERSION = "1.1.0"
EXPECTED_COMBINATIONS = 973_728

MODE_RUST_FULL = "rust_full"
MODE_RUST_SOA = "rust_soa"
MODE_PYTHON = "python"
ALL_MODES = (MODE_RUST_FULL, MODE_RUST_SOA, MODE_PYTHON)

CHARACTER_NAME = "伊冯"
WEAPON_NAME = "佩科5"
SKILL_NAME = "战技"
SKILL_MULTIPLIER = 2.5
DAMAGE_TYPE = "物理"
CHAR_LEVEL = 90
WEAPON_LEVEL = 90
TRUST_LEVEL = 4
ENEMY_DEFENSE = 100.0
WEAPON_SCOPE = "当前武器"
EQUIPMENT_SCOPE = "全部装备"
TOP_N = 10

_TARGET_SECONDS = 10.0


class BenchmarkError(RuntimeError):
    """基准所需的固定数据缺失或数据处理失败。"""


@dataclass(frozen=True)
class BenchmarkSetup:
    """固定基准的作业、评估上下文与组合规模。"""

    job: SingleSkillSearchJob
    search_eval: SearchEvalContext
    config: OptimizerConfig
    data_version: str
    catalog_sizes: dict[str, int]
    total_combinations: int


_ACCESSORY_SLOTS = frozenset({"accessory_a", "accessory_b"})


def _canonical_loadout(pairs: Sequence[tuple[str, str]]) -> tuple[tuple[str, str], ...]:
    """把两个饰品槽合并为同一槽位并排序，消除 accessory_a/b 枚举顺序差异。"""
    normalized = (("accessory" if slot in _ACCESSORY_SLOTS else slot, name) for slot, name in pairs)
    return tuple(sorted(normalized))


@dataclass(frozen=True)
class TopResult:
    """可比较的前 N 结果（饰品槽顺序不敏感）。"""

    weapon_name: str
    final_damage: float
    loadout: tuple[tuple[str, str], ...]

    def matches(self, other: TopResult, *, rel_tol: float = 1e-9) -> bool:
        """武器与配装（饰品槽可互换）相同，且伤害在相对容差内。"""
        return (
            self.weapon_name == other.weapon_name
            and _canonical_loadout(self.loadout) == _canonical_loadout(other.loadout)
            and math.isclose(self.final_damage, other.final_damage, rel_tol=rel_tol)
        )


@dataclass(frozen=True)
class BenchmarkRun:
    """一次基准运行的测量结果。"""

    mode: str
    elapsed_seconds: float
    total_combinations: int
    processed_combinations: int
    cancelled: bool
    peak_rss_mb: float | None
    top_results: tuple[TopResult, ...]
    skipped_preprocessed: int = 0

    @property
    def throughput(self) -> float:
        """组合/秒。"""
        return self.processed_combinations / max(self.elapsed_seconds, 1e-9)

    @property
    def under_target(self) -> bool:
        """是否达到 <10s 目标。"""
        return self.elapsed_seconds < _TARGET_SECONDS


@dataclass(frozen=True)
class CancelResumeReport:
    """取消 + 续跑场景的两阶段结果。"""

    mode: str
    cancelled_run: BenchmarkRun
    resumed_run: BenchmarkRun


def _read_data_version() -> str:
    with open(ENDFIELD_DATA_VERSION_JSON, encoding="utf-8") as handle:
        payload = json.load(handle)
    return str(payload.get("version", "unknown"))


def _require_by_name(rows: list[dict[str, Any]], name: str, kind: str) -> dict[str, Any]:
    for row in rows:
        if row.get("名称") == name:
            return row
    raise BenchmarkError(f"{kind}数据中找不到 {name!r}")


def _build_search_eval(job: SingleSkillSearchJob) -> SearchEvalContext:
    return SearchEvalContext(
        char_data=job.char_data,
        char_level=job.char_level,
        weapon_level=job.weapon_level,
        trust_level=job.trust_level,
        weapon_data_by_name=job.weapon_data_by_name,
        damage_component_mode=job.damage_component_mode,
        use_expected_crit=job.use_expected_crit,
        include_conditional_equipment_crit=job.include_conditional_equipment_crit,
        extra_crit_rate=job.extra_crit_rate,
        extra_crit_damage=job.extra_crit_damage,
        physical_abnormal_counts=dict(job.physical_abnormal_counts or {}),
        spell_abnormal_counts=dict(job.spell_abnormal_counts or {}),
        weapon_normal_levels=tuple(job.weapon_normal_levels),
        weapon_special_states=tuple(dict(s) for s in job.weapon_special_states),
    )


def build_setup() -> BenchmarkSetup:
    """按固定配置组装基准；数据版本或组合规模由调用方校验。"""
    char_data = _require_by_name(get_characters(), CHARACTER_NAME, "角色")
    all_weapons = get_weapons()
    current_weapon = _require_by_name(all_weapons, WEAPON_NAME, "武器")
    catalog = get_equipment_catalog(scope_label=EQUIPMENT_SCOPE)

    job, error = prepare_single_skill_search_job(
        char_data=char_data,
        char_level=CHAR_LEVEL,
        weapon_level=WEAPON_LEVEL,
        trust_level=TRUST_LEVEL,
        skill_name=SKILL_NAME,
        skill_type=SKILL_NAME,
        skill_multiplier=SKILL_MULTIPLIER,
        damage_type=DAMAGE_TYPE,
        weapon_scope_label=WEAPON_SCOPE,
        equipment_scope_label=EQUIPMENT_SCOPE,
        all_weapons=all_weapons,
        current_weapon=current_weapon,
        equipment_catalog=catalog,
        enemy_defense=ENEMY_DEFENSE,
    )
    if job is None or error:
        raise BenchmarkError(error or "组装基准搜索作业失败")

    config = optimizer_config_for_search_job(job, top_n=TOP_N)
    plan = build_optimizer_search_plan(
        weapons=list(job.weapon_candidates),
        equipment_catalog=job.equipment_catalog,
        config=config,
    )
    catalog_sizes = {
        "chest": len(plan.equipment_catalog.get("chest", [])),
        "gloves": len(plan.equipment_catalog.get("gloves", [])),
        "accessories": len(plan.equipment_catalog.get("accessories", [])),
    }
    return BenchmarkSetup(
        job=job,
        search_eval=_build_search_eval(job),
        config=config,
        data_version=_read_data_version(),
        catalog_sizes=catalog_sizes,
        total_combinations=plan.total_combinations,
    )


def run_from_payload(payload: dict[str, Any]) -> BenchmarkRun:
    """从子进程 JSON 还原 ``BenchmarkRun``。"""
    return BenchmarkRun(
        mode=str(payload["mode"]),
        elapsed_seconds=float(payload["elapsed_seconds"]),
        total_combinations=int(payload["total_combinations"]),
        processed_combinations=int(payload["processed_combinations"]),
        cancelled=bool(payload["cancelled"]),
        peak_rss_mb=None if payload.get("peak_rss_mb") is None else float(payload["peak_rss_mb"]),
        top_results=tuple(
            TopResult(
                weapon_name=str(item["weapon_name"]),
                final_damage=float(item["final_damage"]),
                loadout=tuple((str(slot), str(name)) for slot, name in item["loadout"]),
            )
            for item in payload["top_results"]
        ),
        skipped_preprocessed=int(payload.get("skipped_preprocessed", 0)),
    )


def cancel_report_from_payload(payload: dict[str, Any]) -> CancelResumeReport:
    return CancelResumeReport(
        mode=str(payload["mode"]),
        cancelled_run=run_from_payload(payload["cancelled_run"]),
        resumed_run=run_from_payload(payload["resumed_run"]),
    )
