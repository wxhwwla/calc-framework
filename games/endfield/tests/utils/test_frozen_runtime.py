# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""frozen_runtime 单元测试。"""

from __future__ import annotations

import os
import sys
import unittest
from unittest.mock import patch

import utils.frozen_runtime as fr


class TestFrozenRuntime(unittest.TestCase):
    def test_phase0_disables_rust_by_default_env(self) -> None:
        with patch.object(sys, "frozen", True, create=True):
            with patch.dict(os.environ, {"CALC_FROZEN_SEARCH_PHASE": "0"}, clear=True):
                fr.apply_frozen_runtime_defaults()
                self.assertEqual(os.environ.get("RUST_SEARCH_FALLBACK"), "1")
                self.assertFalse(fr.use_rust_search_accel())

    def test_default_phase_is_three(self) -> None:
        with patch.object(sys, "frozen", True, create=True):
            with patch.dict(os.environ, {}, clear=True):
                self.assertEqual(fr.frozen_search_phase(), 3)
                self.assertFalse(fr.frozen_use_thread_pool())
                self.assertTrue(fr.frozen_use_qthread_search())
                self.assertFalse(fr.frozen_use_batch_thread_pool())
                self.assertEqual(fr.frozen_allow_multi_workers(8), 1)
                self.assertEqual(fr.search_recommended_workers(8), 1)
                self.assertFalse(fr.rust_parallel_batch_enabled())

    def test_batch_pool_experimental(self) -> None:
        with patch.object(sys, "frozen", True, create=True):
            with patch.dict(
                os.environ,
                {"CALC_FROZEN_SEARCH_PHASE": "3", "CALC_SEARCH_BATCH_POOL": "1"},
                clear=True,
            ):
                self.assertTrue(fr.frozen_use_batch_thread_pool())
                self.assertEqual(fr.frozen_allow_multi_workers(8), 8)
                self.assertTrue(fr.rust_parallel_batch_enabled())

    def test_default_phase_is_two(self) -> None:
        with patch.object(sys, "frozen", True, create=True):
            with patch.dict(os.environ, {"CALC_FROZEN_SEARCH_PHASE": "2"}, clear=True):
                self.assertEqual(fr.frozen_search_phase(), 2)
                self.assertTrue(fr.frozen_use_thread_pool())
                self.assertFalse(fr.frozen_use_qthread_search())

    def test_phase1_enables_rust(self) -> None:
        with patch.object(sys, "frozen", True, create=True):
            with patch.dict(os.environ, {"CALC_FROZEN_SEARCH_PHASE": "1"}, clear=True):
                self.assertTrue(fr.use_rust_search_accel())
                self.assertFalse(fr.frozen_use_thread_pool())
                self.assertFalse(fr.frozen_use_qthread_search())

    def test_phase2_enables_pool_and_workers(self) -> None:
        with patch.object(sys, "frozen", True, create=True):
            with patch.dict(os.environ, {"CALC_FROZEN_SEARCH_PHASE": "2"}, clear=True):
                self.assertTrue(fr.frozen_use_thread_pool())
                self.assertEqual(fr.frozen_allow_multi_workers(8), 8)
                self.assertFalse(fr.frozen_use_qthread_search())

    def test_phase3_enables_qthread_without_pool(self) -> None:
        with patch.object(sys, "frozen", True, create=True):
            with patch.dict(os.environ, {"CALC_FROZEN_SEARCH_PHASE": "3"}, clear=True):
                self.assertTrue(fr.frozen_use_qthread_search())
                self.assertFalse(fr.frozen_use_thread_pool())
                self.assertFalse(fr.frozen_use_batch_thread_pool())
                self.assertEqual(fr.frozen_allow_multi_workers(8), 1)
                self.assertTrue(fr.frozen_use_search_job_batch())

    def test_phase5_batch_pool_only_with_env(self) -> None:
        with patch.object(sys, "frozen", True, create=True):
            with patch.dict(os.environ, {"CALC_FROZEN_SEARCH_PHASE": "5"}, clear=True):
                self.assertFalse(fr.frozen_use_batch_thread_pool())
            with patch.dict(
                os.environ,
                {"CALC_FROZEN_SEARCH_PHASE": "5", "CALC_SEARCH_BATCH_POOL": "1"},
                clear=True,
            ):
                self.assertTrue(fr.frozen_use_batch_thread_pool())
                self.assertEqual(fr.frozen_allow_multi_workers(8), 8)

    def test_dev_allows_rust_without_fallback(self) -> None:
        with patch.object(sys, "frozen", False, create=True):
            with patch.dict(os.environ, {}, clear=True):
                self.assertTrue(fr.use_rust_search_accel())
                self.assertEqual(fr.frozen_search_phase(), 5)

    def test_fallback_env_disables_rust(self) -> None:
        with patch.object(sys, "frozen", True, create=True):
            with patch.dict(
                os.environ,
                {"CALC_FROZEN_SEARCH_PHASE": "4", "RUST_SEARCH_FALLBACK": "1"},
                clear=True,
            ):
                self.assertFalse(fr.use_rust_search_accel())

    def test_full_batch_default_on_and_opt_out(self) -> None:
        with patch.object(sys, "frozen", False, create=True):
            with patch.dict(os.environ, {}, clear=True):
                self.assertTrue(fr.use_rust_full_batch())
            with patch.dict(os.environ, {"CALC_RUST_FULL_BATCH": "0"}, clear=True):
                self.assertFalse(fr.use_rust_full_batch())
            with patch.dict(os.environ, {"RUST_SEARCH_FALLBACK": "1"}, clear=True):
                self.assertFalse(fr.use_rust_full_batch())


if __name__ == "__main__":
    unittest.main()
