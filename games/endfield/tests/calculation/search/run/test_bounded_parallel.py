#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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

    def test_frozen_exe_forces_thread_even_with_many_workers(self) -> None:
        from unittest.mock import patch

        payload = ProcessWorkerPayload(
            config=OptimizerConfig(),
            search_eval=None,
            base_context=DamageContext(final_attack=1.0, skill_multiplier=1.0),
        )
        with patch.object(parallel_mod, "_pyinstaller_frozen", return_value=True):
            backend = parallel_mod._resolve_parallel_backend(
                max_workers=24,
                parallel_backend="auto",
                process_payload=payload,
            )
        self.assertEqual(backend, "thread")
        with patch.object(parallel_mod, "_pyinstaller_frozen", return_value=True):
            backend = parallel_mod._resolve_parallel_backend(
                max_workers=24,
                parallel_backend="process",
                process_payload=payload,
            )
        self.assertEqual(backend, "thread")

    def test_frozen_caps_workers_to_one_at_phase1(self) -> None:
        from unittest.mock import patch

        with patch.object(parallel_mod, "_pyinstaller_frozen", return_value=True):
            with patch.object(parallel_mod, "frozen_allow_multi_workers", side_effect=lambda n: 1):
                self.assertEqual(parallel_mod._resolve_max_workers(24), 1)

    def test_frozen_uses_inline_at_phase1(self) -> None:
        from unittest.mock import patch

        with patch.object(parallel_mod, "_pyinstaller_frozen", return_value=True):
            with patch.object(parallel_mod, "frozen_use_thread_pool", return_value=False):
                with patch.object(parallel_mod, "_run_inline_loop") as inline_mock:
                    with patch.object(parallel_mod, "_run_parallel_loop") as pool_mock:
                        parallel_mod.run_bounded_parallel(
                            work_items=[1, 2],
                            total=2,
                            evaluate=lambda x: x,
                            max_workers=4,
                        )
        inline_mock.assert_called_once()
        pool_mock.assert_not_called()

    def test_frozen_uses_pool_at_phase2(self) -> None:
        from unittest.mock import patch

        with patch.object(parallel_mod, "_pyinstaller_frozen", return_value=True):
            with patch.object(parallel_mod, "frozen_use_thread_pool", return_value=True):
                with patch.object(parallel_mod, "frozen_allow_multi_workers", side_effect=lambda n: n):
                    with patch.object(parallel_mod, "_run_inline_loop") as inline_mock:
                        with patch.object(parallel_mod, "_run_parallel_loop") as pool_mock:
                            parallel_mod.run_bounded_parallel(
                                work_items=[1, 2],
                                total=2,
                                evaluate=lambda x: x,
                                max_workers=2,
                            )
        pool_mock.assert_called_once()
        inline_mock.assert_not_called()

    def test_frozen_uses_batch_pool_at_phase5(self) -> None:
        from unittest.mock import patch

        with patch.object(parallel_mod, "_pyinstaller_frozen", return_value=True):
            with patch.object(parallel_mod, "frozen_use_batch_thread_pool", return_value=True):
                with patch.object(parallel_mod, "frozen_allow_multi_workers", side_effect=lambda n: n):
                    with patch.object(parallel_mod, "_run_inline_loop") as inline_mock:
                        with patch.object(parallel_mod, "_run_parallel_loop") as pool_mock:
                            parallel_mod.run_bounded_parallel(
                                work_items=list(range(2000)),
                                total=2000,
                                evaluate=lambda x: x,
                                max_workers=4,
                                batch_size=1000,
                                batch_evaluate=lambda batch: batch,
                            )
        pool_mock.assert_called_once()
        inline_mock.assert_not_called()


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
