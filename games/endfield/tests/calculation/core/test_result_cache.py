#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""计算结果缓存测试。"""

import unittestfrom games.endfield.calc.core.result_cache import (    CalculationResultCache,    get_global_result_cache,    reset_global_result_cache,)class TestResultCache(unittest.TestCase):
    def test_hit_when_dependencies_unchanged(self) -> None:
        cache = CalculationResultCache()
        cache.set_dependency("level", 80)
        calls = {"n": 0}

        def compute() -> int:
            calls["n"] += 1
            return 42

        v1, hit1 = cache.get_or_compute("k", compute)
        v2, hit2 = cache.get_or_compute("k", compute)
        self.assertEqual(v1, 42)
        self.assertEqual(v2, 42)
        self.assertFalse(hit1)
        self.assertTrue(hit2)
        self.assertEqual(calls["n"], 1)

    def test_miss_after_dependency_update(self) -> None:
        cache = CalculationResultCache()
        cache.set_dependency("level", 1)
        cache.get_or_compute("k", lambda: "a")
        cache.set_dependency("level", 2)
        value, hit = cache.get_or_compute("k", lambda: "b")
        self.assertEqual(value, "b")
        self.assertFalse(hit)

    def test_same_dependency_value_does_not_clear(self) -> None:
        cache = CalculationResultCache()
        cache.set_dependency("level", 5)
        cache.get_or_compute("k", lambda: 1)
        cache.set_dependency("level", 5)
        _, hit = cache.get_or_compute("k", lambda: 2)
        self.assertTrue(hit)

    def test_clear_and_stats(self) -> None:
        cache = CalculationResultCache()
        cache.set_dependency("a", 1)
        cache.get_or_compute("x", lambda: 1)
        self.assertEqual(cache.stats()["entries"], 1)
        cache.clear()
        self.assertEqual(cache.stats()["entries"], 0)

    def test_global_singleton_reset(self) -> None:
        reset_global_result_cache()
        a = get_global_result_cache()
        reset_global_result_cache()
        b = get_global_result_cache()
        self.assertIsNot(a, b)


if __name__ == "__main__":
    unittest.main()
