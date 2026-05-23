#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SQLite 续跑与去重恢复。"""

from __future__ import annotations

import sqlite3
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from calculation.damage_engine import DamageContext
from calculation.loadout_optimizer import (
    LoadoutScore,
    OptimizerConfig,
    WeaponCandidate,
    enumerate_optimizer_tasks,
    evaluate_task,
)
from calculation.search_runner import SearchCancelToken


@dataclass(frozen=True)
class ResumeExecutionResult:
    """续跑执行结果。"""

    top_results: tuple[LoadoutScore, ...]
    total_combinations: int
    processed_combinations: int
    processed_this_run: int
    skipped_preprocessed: int
    cancelled: bool


class SearchRunStore:
    """搜索任务 SQLite 存储。"""

    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        conn = self._connect()
        try:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS runs (
                    signature TEXT PRIMARY KEY,
                    total_combinations INTEGER NOT NULL,
                    status TEXT NOT NULL DEFAULT 'running'
                );

                CREATE TABLE IF NOT EXISTS processed (
                    signature TEXT NOT NULL,
                    combo_key TEXT NOT NULL,
                    PRIMARY KEY (signature, combo_key)
                );

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
            )
            conn.commit()
        finally:
            conn.close()

    def ensure_run(self, signature: str, total_combinations: int) -> None:
        conn = self._connect()
        try:
            conn.execute(
                """
                INSERT INTO runs(signature, total_combinations, status)
                VALUES (?, ?, 'running')
                ON CONFLICT(signature) DO UPDATE SET total_combinations=excluded.total_combinations
                """,
                (signature, total_combinations),
            )
            conn.commit()
        finally:
            conn.close()

    def mark_run_status(self, signature: str, status: str) -> None:
        conn = self._connect()
        try:
            conn.execute("UPDATE runs SET status=? WHERE signature=?", (status, signature))
            conn.commit()
        finally:
            conn.close()

    def get_processed_keys(self, signature: str) -> set[str]:
        conn = self._connect()
        try:
            rows = conn.execute(
                "SELECT combo_key FROM processed WHERE signature=?",
                (signature,),
            ).fetchall()
        finally:
            conn.close()
        return {row["combo_key"] for row in rows}

    def save_processed_score(self, signature: str, combo_key: str, score: LoadoutScore) -> None:
        conn = self._connect()
        try:
            conn.execute(
                """
                INSERT OR IGNORE INTO processed(signature, combo_key)
                VALUES (?, ?)
                """,
                (signature, combo_key),
            )
            conn.execute(
                """
                INSERT OR REPLACE INTO scores(
                    signature, combo_key, weapon_name, final_damage,
                    chest, gloves, accessory_a, accessory_b
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    signature,
                    combo_key,
                    score.weapon_name,
                    float(score.final_damage),
                    score.loadout_names.get("chest", ""),
                    score.loadout_names.get("gloves", ""),
                    score.loadout_names.get("accessory_a", ""),
                    score.loadout_names.get("accessory_b", ""),
                ),
            )
            conn.commit()
        finally:
            conn.close()

    def count_processed(self, signature: str) -> int:
        conn = self._connect()
        try:
            row = conn.execute(
                "SELECT COUNT(*) AS c FROM processed WHERE signature=?",
                (signature,),
            ).fetchone()
        finally:
            conn.close()
        return int(row["c"] if row else 0)

    def load_top_scores(self, signature: str, top_n: int) -> tuple[LoadoutScore, ...]:
        conn = self._connect()
        try:
            rows = conn.execute(
                """
                SELECT weapon_name, final_damage, chest, gloves, accessory_a, accessory_b
                FROM scores
                WHERE signature=?
                ORDER BY final_damage DESC
                LIMIT ?
                """,
                (signature, max(1, int(top_n))),
            ).fetchall()
        finally:
            conn.close()
        return tuple(
            LoadoutScore(
                weapon_name=row["weapon_name"],
                final_damage=float(row["final_damage"]),
                loadout_names={
                    "chest": row["chest"],
                    "gloves": row["gloves"],
                    "accessory_a": row["accessory_a"],
                    "accessory_b": row["accessory_b"],
                },
            )
            for row in rows
        )


def _task_key(task: tuple[WeaponCandidate, tuple[dict, dict, dict, dict]]) -> str:
    weapon, (chest, gloves, acc_a, acc_b) = task
    return "|".join(
        [
            weapon.name,
            str(chest.get("名称", "")),
            str(gloves.get("名称", "")),
            str(acc_a.get("名称", "")),
            str(acc_b.get("名称", "")),
        ]
    )


def execute_search_with_resume(
    *,
    db_path: Path,
    run_signature: str,
    base_context: DamageContext,
    weapons: list[WeaponCandidate],
    equipment_catalog: dict[str, list[dict]],
    config: OptimizerConfig,
    max_workers: int = 1,
    cancel_token: Optional[SearchCancelToken] = None,
) -> ResumeExecutionResult:
    """执行可续跑搜索：自动跳过已处理组合。"""
    store = SearchRunStore(db_path)
    tasks, total_combinations, _pruned, _warnings = enumerate_optimizer_tasks(
        base_context=base_context,
        weapons=weapons,
        equipment_catalog=equipment_catalog,
        config=config,
    )
    store.ensure_run(run_signature, total_combinations)

    existing_keys = store.get_processed_keys(run_signature)
    task_items = [(_task_key(task), task) for task in tasks]
    skipped_preprocessed = sum(1 for key, _ in task_items if key in existing_keys)
    remaining = [(key, task) for key, task in task_items if key not in existing_keys]

    token = cancel_token or SearchCancelToken()
    processed_this_run = 0
    cancelled = False

    with ThreadPoolExecutor(max_workers=max(1, int(max_workers))) as executor:
        futures = {
            executor.submit(
                evaluate_task,
                base_context=base_context,
                crit_mode=config.crit_mode,
                task=task,
            ): key
            for key, task in remaining
        }
        for future in as_completed(futures):
            if token.should_cancel(processed_this_run):
                cancelled = True
                for pending in futures:
                    pending.cancel()
                break
            key = futures[future]
            try:
                score = future.result()
            except Exception:
                continue
            store.save_processed_score(run_signature, key, score)
            processed_this_run += 1

    store.mark_run_status(run_signature, "cancelled" if cancelled else "completed")
    processed_total = store.count_processed(run_signature)
    top_scores = store.load_top_scores(run_signature, config.top_n)
    return ResumeExecutionResult(
        top_results=top_scores,
        total_combinations=total_combinations,
        processed_combinations=processed_total,
        processed_this_run=processed_this_run,
        skipped_preprocessed=skipped_preprocessed,
        cancelled=cancelled,
    )


def get_sqlite_viewer_links() -> tuple[str, ...]:
    """打包说明可展示的 SQLite 查看器链接。"""
    return (
        "https://sqlitebrowser.org/dl/",
        "https://antonz.org/sqlite-gui/",
    )
