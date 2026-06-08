# SPDX-License-Identifier: AGPL-3.0
"""块级缓存单元测试。"""

from __future__ import annotations

from calc_framework.dag.block_cache import BlockCache


class TestBlockCache:
    def test_get_missing(self) -> None:
        cache = BlockCache()
        result = cache.get("nonexistent", {"a": 1.0})
        assert result is None

    def test_put_and_get(self) -> None:
        cache = BlockCache()
        cache.put("b1", {"a": 1.0}, {"out": 42.0})
        result = cache.get("b1", {"a": 1.0})
        assert result is not None
        assert result["out"] == 42.0

    def test_different_input_returns_none(self) -> None:
        cache = BlockCache()
        cache.put("b1", {"a": 1.0}, {"out": 42.0})
        result = cache.get("b1", {"a": 2.0})
        assert result is None

    def test_invalidate(self) -> None:
        cache = BlockCache()
        cache.put("b1", {"a": 1.0}, {"out": 42.0})
        cache.invalidate("b1")
        assert cache.get("b1", {"a": 1.0}) is None

    def test_invalidate_all(self) -> None:
        cache = BlockCache()
        cache.put("b1", {"a": 1.0}, {"out": 10.0})
        cache.put("b2", {"a": 2.0}, {"out": 20.0})
        cache.invalidate_all()
        assert cache.get("b1", {"a": 1.0}) is None
        assert cache.get("b2", {"a": 2.0}) is None

    def test_put_overwrites(self) -> None:
        cache = BlockCache()
        cache.put("b1", {"a": 1.0}, {"out": 10.0})
        cache.put("b1", {"a": 1.0}, {"out": 99.0})
        result = cache.get("b1", {"a": 1.0})
        assert result is not None
        assert result["out"] == 99.0

    def test_multiple_blocks_independent(self) -> None:
        cache = BlockCache()
        cache.put("b1", {"a": 1.0}, {"out": 10.0})
        cache.put("b2", {"a": 2.0}, {"out": 20.0})
        r1 = cache.get("b1", {"a": 1.0})
        r2 = cache.get("b2", {"a": 2.0})
        assert r1 is not None and r1["out"] == 10.0
        assert r2 is not None and r2["out"] == 20.0

    def test_get_does_not_mutate_cache(self) -> None:
        cache = BlockCache()
        cache.put("b1", {"a": 1.0}, {"out": 42.0})
        r1 = cache.get("b1", {"a": 1.0})
        r2 = cache.get("b1", {"a": 1.0})
        assert r1 is not None and r2 is not None
        assert r1["out"] == r2["out"]

    def test_empty_inputs(self) -> None:
        cache = BlockCache()
        cache.put("b1", {}, {"out": 1.0})
        result = cache.get("b1", {})
        assert result is not None
        assert result["out"] == 1.0
