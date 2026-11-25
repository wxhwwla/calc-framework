# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""通用 SQLite 搜索持久化 — 续跑与去重恢复。



用法::



    from .persist import SearchRunStore



    store = SearchRunStore(Path("search_runs.db"))

    store.ensure_run("abc123", total_combinations=1000)



    processed = store.get_processed_keys("abc123")

    store.mark_processed_batch("abc123", ["key1", "key2"])

    store.mark_run_status("abc123", "completed")

"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from ..logging import get_logger

logger = get_logger(__name__)


PROCESSED_BATCH_SIZE = 500


class SearchRunStore:
    """通用搜索任务 SQLite 存储。



    提供 ``runs``、``processed`` 和通用 ``result_scores`` 基础表，适用于任何需要
    中断续跑、去重和历史 TopN 恢复的搜索场景。游戏适配器可继承此类添加专属表（如 scores）。

    """

    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)

        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        """_connect。"""
        conn = sqlite3.connect(str(self.db_path))

        conn.row_factory = sqlite3.Row

        return conn

    def _init_schema(self) -> None:
        """_init_schema。"""

        conn = self._connect()

        try:
            conn.executescript(self._schema_sql())

            conn.commit()

        finally:
            conn.close()

        """_schema_sql。"""

    def _schema_sql(self) -> str:
        return """

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


        CREATE TABLE IF NOT EXISTS result_scores (

            signature TEXT NOT NULL,

            combo_key TEXT NOT NULL,

            score REAL NOT NULL,

            payload TEXT NOT NULL,

            PRIMARY KEY (signature, combo_key)

        );

        """

    # ── runs ────────────────────────────────────────────

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

    def run_status(self, signature: str) -> str | None:
        conn = self._connect()

        try:
            row = conn.execute(
                "SELECT status FROM runs WHERE signature=?",
                (signature,),
            ).fetchone()

        finally:
            conn.close()

        return row["status"] if row else None

    # ── processed ───────────────────────────────────────

    def get_processed_keys(self, signature: str) -> set[str]:
        conn = self._connect()

        try:
            rows = conn.execute(
                "SELECT combo_key FROM processed WHERE signature=?",
                (signature,),
            ).fetchall()

        finally:
            conn.close()

        return {r["combo_key"] for r in rows}

    def mark_processed_batch(self, signature: str, combo_keys: list[str]) -> None:
        if not combo_keys:
            return

        conn = self._connect()

        try:
            conn.executemany(
                """

                INSERT OR IGNORE INTO processed(signature, combo_key)

                VALUES (?, ?)

                """,
                [(signature, key) for key in combo_keys],
            )

            conn.commit()

        finally:
            conn.close()

    def mark_scored_batch(self, signature: str, rows: list[tuple[str, float, str]]) -> None:
        """保存预编码评分与 processed；旧 hook 子类走兼容的有序两阶段路径。"""
        if not rows:
            return
        encoded = [(signature, key, float(score), payload) for key, score, payload in rows]
        legacy_hook = type(self).mark_processed_batch is not SearchRunStore.mark_processed_batch
        conn = self._connect()
        try:
            conn.executemany(
                "INSERT OR REPLACE INTO result_scores(signature, combo_key, score, payload) VALUES (?, ?, ?, ?)",
                encoded,
            )
            if not legacy_hook:
                conn.executemany(
                    "INSERT OR IGNORE INTO processed(signature, combo_key) VALUES (?, ?)",
                    [(signature, key) for key, _score, _payload in rows],
                )
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
        if legacy_hook:
            self.mark_processed_batch(signature, [key for key, _score, _payload in rows])

    def get_scored_results(self, signature: str) -> list[tuple[str, float, Any]]:
        """读取某次运行的可恢复评分，按分数降序。"""
        conn = self._connect()
        try:
            rows = conn.execute(
                "SELECT s.combo_key, s.score, s.payload FROM result_scores s "
                "JOIN processed p ON p.signature=s.signature AND p.combo_key=s.combo_key "
                "WHERE s.signature=? ORDER BY s.score DESC",
                (signature,),
            ).fetchall()
        finally:
            conn.close()
        return [(str(row["combo_key"]), float(row["score"]), json.loads(row["payload"])) for row in rows]

    def count_processed(self, signature: str) -> int:
        conn = self._connect()

        try:
            row = conn.execute(
                "SELECT COUNT(*) AS c FROM processed WHERE signature=?",
                (signature,),
            ).fetchone()

        finally:
            conn.close()

        return int(row["c"]) if row else 0

    def delete_run(self, signature: str) -> None:
        conn = self._connect()

        try:
            conn.execute("DELETE FROM result_scores WHERE signature=?", (signature,))

            conn.execute("DELETE FROM processed WHERE signature=?", (signature,))

            conn.execute("DELETE FROM runs WHERE signature=?", (signature,))

            conn.commit()

        finally:
            conn.close()
