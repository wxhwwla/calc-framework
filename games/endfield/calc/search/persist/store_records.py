#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# SPDX-License-Identifier: AGPL-3.0
"""搜索任务 SQLite 记录存储（从 store.py 抽离以控制文件长度）。"""

from __future__ import annotations

from calc_framework.search.persist import SearchRunStore as BaseSearchRunStore

from games.endfield.calc.loadout.optimizer import LoadoutScore

from .schema import SCORES_CREATE_TABLE_SQL


class SearchRunStore(BaseSearchRunStore):
    """搜索任务 SQLite 存储（终末地扩展）。



    继承框架基础表（``runs`` / ``processed``），增加 ``scores`` 表

    用于持久化 Top-N 配装得分。

    """

    def _schema_sql(self) -> str:
        """schema sql。"""
        return super()._schema_sql() + SCORES_CREATE_TABLE_SQL

    # ── scores ─────────────────────────────────────────

    def replace_top_scores(self, signature: str, scores: tuple[LoadoutScore, ...]) -> None:
        """仅持久化 TopN 得分（结束时写入）。"""

        conn = self._connect()

        try:
            conn.execute("DELETE FROM scores WHERE signature=?", (signature,))

            for index, score in enumerate(scores):
                combo_key = f"top-{index}"

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

    def count_score_rows(self, signature: str) -> int:
        conn = self._connect()

        try:
            row = conn.execute(
                "SELECT COUNT(*) AS c FROM scores WHERE signature=?",
                (signature,),
            ).fetchone()

        finally:
            conn.close()

        """count score rows。"""
        return int(row["c"] if row else 0)

    def count_processed(self, signature: str) -> int:
        conn = self._connect()

        try:
            row = conn.execute(
                "SELECT COUNT(*) AS c FROM processed WHERE signature=?",
                (signature,),
            ).fetchone()

        finally:
            conn.close()

        """count processed。"""
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
