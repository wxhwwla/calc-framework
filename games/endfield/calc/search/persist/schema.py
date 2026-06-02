#!/usr/bin/env python3

# SPDX-License-Identifier: AGPL-3.0
"""搜索存储的 schema 定义。

包含 CREATE TABLE SQL 语句、dataclass 模型定义，与核心 CRUD 逻辑分离。
"""

from __future__ import annotations

from dataclasses import dataclass

from games.endfield.calc.loadout.optimizer import LoadoutScore

# ── CREATE TABLE SQL ───────────────────────────────────

SCORES_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS scores (
    signature TEXT NOT NULL,
    combo_key TEXT NOT NULL,
    weapon_name TEXT NOT NULL,
    final_damage REAL NOT NULL,
    chest TEXT NOT NULL,
    gloves TEXT NOT NULL,
    accessory_a TEXT NOT NULL,
    accessory_b TEXT NOT NULL,
    PRIMARY KEY (signature, combo_key)
);
"""
"""scores 表 DDL。"""

# ── 数据模型 ────────────────────────────────────────────


@dataclass(frozen=True)
class ResumeExecutionResult:
    """续跑执行结果。"""

    top_results: tuple[LoadoutScore, ...]
    total_combinations: int
    processed_combinations: int
    processed_this_run: int
    skipped_preprocessed: int
    cancelled: bool


@dataclass
class PendingTaskStream:
    """待处理任务流（附带跳过计数）。"""

    skipped_preprocessed: int = 0
