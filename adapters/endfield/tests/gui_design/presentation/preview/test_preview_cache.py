#!/usr/bin/env python3
"""预览计算缓存接入测试。"""

import unittest

from adapters.endfield.calc.core.preview_cache import cached_preview, sync_preview_dependencies
from adapters.endfield.calc.core.result_cache import reset_global_result_cache


class TestPreviewCache(unittest.TestCase):
    def setUp(self) -> None:
        reset_global_result_cache()

    def test_cached_preview_skips_second_compute(self) -> None:
        sync_preview_dependencies(char_level=80, weapon_level=90)
        calls = {"n": 0}

        def compute() -> str:
            calls["n"] += 1
            return "ok"

        v1, hit1 = cached_preview("demo", compute)
        v2, hit2 = cached_preview("demo", compute)
        self.assertEqual(v1, "ok")
        self.assertEqual(v2, "ok")
        self.assertFalse(hit1)
        self.assertTrue(hit2)
        self.assertEqual(calls["n"], 1)

    def test_cache_misses_after_dependency_change(self) -> None:
        sync_preview_dependencies(char_level=80)
        cached_preview("k", lambda: 1)
        sync_preview_dependencies(char_level=81)
        _, hit = cached_preview("k", lambda: 2)
        self.assertFalse(hit)


if __name__ == "__main__":
    unittest.main()
