#!/usr/bin/env python3

# SPDX-License-Identifier: AGPL-3.0
"""SQLite 续跑与去重恢复。



终末地 ``SearchRunStore`` 继承框架 ``calc_framework.search.persist.SearchRunStore``，

在基础 ``runs`` / ``processed`` 表之上增加端特有 ``scores`` 表。

"""



from __future__ import annotations

import time
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from pathlib import Path

from calc_framework.search.persist import SearchRunStore as BaseSearchRunStore

from games.endfield.calc.core.top_n_tracker import TopNTracker
from games.endfield.calc.damage.engine import DamageContext
from games.endfield.calc.loadout.optimizer import (
    LoadoutScore,
    OptimizerConfig,
    OptimizerTask,
    WeaponCandidate,
    build_optimizer_search_plan,
    evaluate_task,
    iter_optimizer_tasks,
)

from ..evaluate.context import SearchEvalContext
from ..run.cancel import SearchCancelToken
from ..run.parallel import run_bounded_parallel

# 续跑进度批量写入条数

PROCESSED_BATCH_SIZE = 500





@dataclass(frozen=True)

class ResumeExecutionResult:

    """续跑执行结果。"""



    top_results: tuple[LoadoutScore, ...]

    total_combinations: int

    processed_combinations: int

    processed_this_run: int

    skipped_preprocessed: int

    cancelled: bool





class SearchRunStore(BaseSearchRunStore):

    """搜索任务 SQLite 存储（终末地扩展）。



    继承框架基础表（``runs`` / ``processed``），增加 ``scores`` 表

    用于持久化 Top-N 配装得分。

    """



    def _schema_sql(self) -> str:

        return super()._schema_sql() + """

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
        """schema sql。"""



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

        return int(row["c"] if row else 0)
        """count score rows。"""



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
        """count processed。"""



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
        """load top scores。"""





@dataclass

class PendingTaskStream:

    """待处理任务流（附带跳过计数）。"""



    skipped_preprocessed: int = 0





def _iter_pending_tasks(

    *,

    plan,

    allow_duplicate_accessory: bool,

    existing_keys: set[str],

) -> tuple[Iterator[tuple[str, OptimizerTask]], PendingTaskStream]:

    """流式产出待处理 (combo_key, task)，并统计已跳过数量。"""

    stream = PendingTaskStream()



    def _generator() -> Iterator[tuple[str, OptimizerTask]]:

        for task in iter_optimizer_tasks(plan, allow_duplicate_accessory=allow_duplicate_accessory):

            key = _task_key(task)

            if key in existing_keys:

                stream.skipped_preprocessed += 1

                continue

            yield key, task
        """generator。"""



    return _generator(), stream





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
    """task key。"""





def execute_search_with_resume(

    *,

    db_path: Path,

    run_signature: str,

    base_context: DamageContext,

    weapons: list[WeaponCandidate],

    equipment_catalog: dict[str, list[dict]],

    config: OptimizerConfig,

    max_workers: int = 1,

    cancel_token: SearchCancelToken | None = None,

    progress_callback: Callable[[dict], None] | None = None,

    search_eval: SearchEvalContext | None = None,

    task_evaluator: Callable[[OptimizerTask], LoadoutScore] | None = None,

) -> ResumeExecutionResult:

    """执行可续跑搜索：自动跳过已处理组合。"""

    store = SearchRunStore(db_path)

    plan = build_optimizer_search_plan(

        weapons=weapons,

        equipment_catalog=equipment_catalog,

        config=config,

    )

    total_combinations = plan.total_combinations

    store.ensure_run(run_signature, total_combinations)



    existing_keys = store.get_processed_keys(run_signature)

    pending_iter, pending_stream = _iter_pending_tasks(

        plan=plan,

        allow_duplicate_accessory=config.allow_duplicate_accessory,

        existing_keys=existing_keys,

    )

    token = cancel_token or SearchCancelToken()

    processed_this_run = 0

    processed_keys_buffer: list[str] = []

    top_tracker = TopNTracker(config.top_n, key_fn=lambda score: score.final_damage)

    started_at = time.perf_counter()



    def _evaluate(task: OptimizerTask) -> LoadoutScore:

        if task_evaluator is not None:

            return task_evaluator(task)

        return evaluate_task(

            base_context=base_context,

            crit_mode=config.crit_mode,

            task=task,

            search_eval=search_eval,

        )
        """evaluate。"""



    def _on_result(item: tuple[str, OptimizerTask], score: LoadoutScore) -> None:

        nonlocal processed_this_run

        key, _task = item

        top_tracker.offer(score)

        processed_keys_buffer.append(key)

        processed_this_run += 1

        if len(processed_keys_buffer) >= PROCESSED_BATCH_SIZE:

            store.mark_processed_batch(run_signature, processed_keys_buffer)

            processed_keys_buffer.clear()
        """on result。"""



    def _progress(info: dict) -> None:

        if not progress_callback:

            return

        # 须读 pending_stream：skipped 在遍历中递增，不能先用后赋的局部变量

        processed_total = pending_stream.skipped_preprocessed + int(info.get("processed", 0))

        elapsed = max(1e-6, time.perf_counter() - started_at)

        speed = processed_this_run / elapsed if processed_this_run else 0.0

        remain = max(0, total_combinations - processed_total)

        eta = remain / speed if speed > 0 else 0.0

        progress_callback(

            {

                "processed": processed_total,

                "total": total_combinations,

                "speed_per_sec": speed,

                "eta_seconds": eta,

            }

        )
        """progress。"""



    _, _processed_count, cancelled = run_bounded_parallel(

        work_items=pending_iter,

        total=total_combinations,

        evaluate=lambda item: _evaluate(item[1]),

        max_workers=max_workers,

        cancel_token=token,

        progress_callback=_progress,

        on_result=_on_result,

    )



    if processed_keys_buffer:

        store.mark_processed_batch(run_signature, processed_keys_buffer)



    skipped_preprocessed = pending_stream.skipped_preprocessed

    top_scores = top_tracker.results()

    store.replace_top_scores(run_signature, top_scores)

    store.mark_run_status(run_signature, "cancelled" if cancelled else "completed")

    processed_total = store.count_processed(run_signature)

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

