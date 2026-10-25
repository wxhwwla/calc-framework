# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""AdapterManager 和启动器单元测试。"""

from __future__ import annotations

import pytest

from calc_framework.config.manager import AdapterManager, discover_adapters


class TestDiscoverAdapters:
    def test_discovers_endfield_and_card_rpg(self):
        adapters = discover_adapters()

        assert len(adapters) >= 2

        names = list(adapters.keys())

        assert any(k.lower() for k in names)  # non-empty names

    def test_each_adapter_has_meta_json(self):
        adapters = discover_adapters()

        for path in adapters.values():
            meta = path / "meta.json"

            assert meta.is_file(), f"{path} 缺少 meta.json"


class TestAdapterManager:
    def test_available_adapters(self):
        mgr = AdapterManager()

        names = mgr.names

        assert len(names) >= 2

    def test_load_endfield(self):
        mgr = AdapterManager()

        for name in mgr.names:
            if "终末地" in name or "endfield" in name.lower():
                pkg = mgr.load(name)

                assert pkg is not None

                assert pkg.dag_service is not None

                return

        pytest.skip("未找到 endfield 适配器")

    def test_load_card_rpg(self):
        mgr = AdapterManager()

        for name in mgr.names:
            if "card" in name.lower() or "卡牌" in name:
                pkg = mgr.load(name)

                assert pkg is not None

                assert pkg.dag_service is not None

                return

        pytest.skip("未找到 card_rpg 适配器")

    def test_load_unknown_raises(self):
        mgr = AdapterManager()

        with pytest.raises(KeyError, match="未找到"):
            mgr.load("nonexistent_game_adapter")

    def test_summary_includes_all(self):
        mgr = AdapterManager()

        summary = mgr.summary()

        assert len(summary) >= 2

        for entry in summary:
            assert "name" in entry

            assert "path" in entry

    def test_reload_clears_cache(self):
        mgr = AdapterManager()

        name = mgr.names[0]

        pkg1 = mgr.load(name)

        pkg2 = mgr.reload(name)

        assert pkg1 is not pkg2

    def test_refresh_discovers_new(self):
        mgr = AdapterManager()

        before = len(mgr.names)

        mgr.refresh()

        assert len(mgr.names) == before
