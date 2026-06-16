#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""run_bounded_parallel 多进程后端测试。"""

from __future__ import annotations

import unittest

from games.endfield.calc.damage.engine import DamageContext
from games.endfield.calc.equipment.system import build_runtime_equipment_from_wiki_draft
from games.endfield.calc.loadout.in_memory_optimizer import run_enumerated_optimizer_parallel
from games.endfield.calc.loadout.optimizer import OptimizerConfig, WeaponCandidate
from games.endfield.calc.search.evaluate.process_worker import ProcessWorkerPayload
from games.endfield.calc.search.run import parallel as parallel_mod


def _catalog() -> dict:
    chest = build_runtime_equipment_from_wiki_draft(
        {"名称": "胸甲A", "_wiki_params": {"装备种类": "护甲", "所属套组": "套装A"}}
    )
    gloves = build_runtime_equipment_from_wiki_draft(
        {"名称": "护手A", "_wiki_params": {"部位": "护手", "套装": "套装A"}}
    )
    accessories = [
        build_runtime_equipment_from_wiki_draft({"名称": f"配件{i}", "_wiki_params": {"部位": "配件", "套装": "套装A"}})
        for i in range(4)
    ]
    return {"chest": [chest], "gloves": [gloves], "accessories": accessories}


class TestParallelBackendResolution(unittest.TestCase):
    def test_auto_selects_process_when_workers_and_payload(self) -> None:
        payload = ProcessWorkerPayload(
            config=OptimizerConfig(),
            search_eval=None,
            base_context=DamageContext(final_attack=1.0, skill_multiplier=1.0),
        )
        backend = parallel_mod._resolve_parallel_backend(
            max_workers=4,
            parallel_backend="auto",
            process_payload=payload,
        )
        self.assertEqual(backend, "process")

    def test_auto_falls_back_to_thread_when_single_worker(self) -> None:
        payload = ProcessWorkerPayload(
            config=OptimizerConfig(),
            search_eval=None,
            base_context=DamageContext(final_attack=1.0, skill_multiplier=1.0),
        )
        backend = parallel_mod._resolve_parallel_backend(
            max_workers=1,
            parallel_backend="auto",
            process_payload=payload,
        )
        self.assertEqual(backend, "thread")


class TestProcessParallelIntegration(unittest.TestCase):
    def _run_search(self, *, parallel_backend: str, max_workers: int):
        return run_enumerated_optimizer_parallel(
            base_context=DamageContext(final_attack=0.0, skill_multiplier=1.0, enemy_defense=0.0),
            weapons=[WeaponCandidate(name="武器A", final_attack=1000.0)],
            equipment_catalog=_catalog(),
            config=OptimizerConfig(top_n=3),
            max_workers=max_workers,
            parallel_backend=parallel_backend,  # type: ignore[arg-type]
        )

    def test_process_matches_thread_results(self) -> None:
        thread_top, thread_total, thread_done, _, _ = self._run_search(
            parallel_backend="thread",
            max_workers=2,
        )
        process_top, process_total, process_done, _, _ = self._run_search(
            parallel_backend="process",
            max_workers=2,
        )
        self.assertEqual(thread_total, process_total)
        self.assertEqual(thread_done, process_done)
        self.assertEqual(
            [s.final_damage for s in thread_top],
            [s.final_damage for s in process_top],
        )


if __name__ == "__main__":
    unittest.main()
